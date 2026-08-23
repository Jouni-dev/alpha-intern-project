"""
Unified Multi-Tool Agent

Three-tool agent (Anthropic info + financial + live web search) using OpenAI's
Responses API, which is required for the built-in web_search tool.
"""

import os
import json
import time
import sys
from dotenv import load_dotenv
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError, APITimeoutError
from typing import List, Dict, Any, Callable

# web_search results can contain Unicode punctuation that crashes print() on
# Windows consoles using a legacy codepage - force UTF-8 to avoid that.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an AI assistant with access to three tools:

1. search_anthropic_info - retrieves relevant passages about Anthropic (company history, products, research, funding, leadership)
2. search_financial - retrieves relevant financial data (accounts, amounts, comparisons)
3. web_search - searches the live internet

Rules:
- If the question is about Anthropic the company, its products, or AI safety/research concepts that Anthropic works on (Constitutional AI, interpretability, scalable oversight, Responsible Scaling Policy, red-teaming, MCP, tool use, etc.) -> use search_anthropic_info, even if the word "Anthropic" is not in the question. Err on the side of checking the document rather than answering from your own general knowledge - the document is the source of truth here, not what you already know.
- If the question is about money, accounts, numbers, or financial data -> use search_financial
- If the question asks whether something about Anthropic is still true, current, up to date, unchanged, or "the latest" (this includes words like "still", "latest", "now", "changed", "current", as well as explicit requests to validate/verify/fact-check) -> use search_anthropic_info first to see what the document claims, then ALWAYS use web_search to check that specific claim against current real-world sources. Do not just repeat the document's claim without checking web_search - the document may be outdated. For these validation questions, start your answer with a one-line verdict - exactly one of "VALIDATION RESULT: CONFIRMED - still accurate", "VALIDATION RESULT: OUTDATED - this has changed", or "VALIDATION RESULT: INCORRECT - the document was wrong" - then in 2-3 short sentences state what the document claimed and what the web search found.
- If the question cannot be answered by any tool -> do not call any tool
- Base your answer ONLY on what the tools return.

Answer style: plain text only, no markdown (no bold, no bullet lists, no links). Be direct and brief - a few sentences, not a report. Do not close with offers to help further or follow-up questions."""


def define_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "name": "search_anthropic_info",
            "description": "Retrieve passages about Anthropic: company history, products, research (Constitutional AI, interpretability), funding, leadership.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "What to search for in the Anthropic document"}
                },
                "required": ["question"]
            }
        },
        {
            "type": "function",
            "name": "search_financial",
            "description": "Retrieve financial data about accounts, line items, dollar amounts, comparisons.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "What financial information to search for"}
                },
                "required": ["question"]
            }
        },
        {
            "type": "web_search"
        }
    ]


def _call_responses_with_retry(next_input, previous_response_id, max_retries=3):
    """Wraps the one API call this agent actually depends on. Transient failures
    (rate limit, connection drop, timeout) are worth retrying with backoff - a bad
    API key is not, so that fails immediately with a clear message instead of
    burning through retries that can't possibly help."""
    for attempt in range(max_retries):
        try:
            return client.responses.create(
                model="gpt-4o",
                instructions=SYSTEM_PROMPT,
                input=next_input,
                tools=define_tools(),
                previous_response_id=previous_response_id
            )
        except AuthenticationError:
            raise RuntimeError("OpenAI API key is missing or invalid - check your .env file.")
        except (RateLimitError, APIConnectionError, APITimeoutError) as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"OpenAI API unavailable after {max_retries} attempts: {e}")
            time.sleep(2 ** attempt)  # 1s, 2s, 4s backoff


def ask_with_tools(
    question: str,
    retrieve_anthropic_func: Callable[[str], List[str]],
    retrieve_financial_func: Callable[[str], List[str]],
    previous_response_id: str = None
) -> Dict[str, Any]:
    """Ask a question, model picks tool(s) - including live web search - retriever
    functions return chunks for the two custom tools, model synthesizes the answer.

    Multi-turn conversations are continued via previous_response_id (the Responses
    API keeps the conversation state server-side), not by replaying the full history -
    replaying raw output items back as input caused the model to lose track of earlier
    tool results and drop parts of multi-part answers."""

    next_input = [{"role": "user", "content": question}]

    tool_calls_made = []
    all_retrieved_chunks = []
    MAX_TOOL_ITERATIONS = 6  # guardrail: cap tool calls per turn so a confused model can't loop forever

    for iteration in range(MAX_TOOL_ITERATIONS):
        response = _call_responses_with_retry(next_input, previous_response_id)
        previous_response_id = response.id

        function_calls = [item for item in response.output if item.type == "function_call"]
        web_search_calls = [item for item in response.output if item.type == "web_search_call"]

        for ws_call in web_search_calls:
            query = getattr(ws_call.action, "query", None) if hasattr(ws_call, "action") else None
            tool_calls_made.append({"tool": "web_search", "question": query})

        if not function_calls:
            answer = response.output_text
            break

        next_input = []
        for call in function_calls:
            tool_name = call.name
            try:
                tool_args = json.loads(call.arguments)
            except json.JSONDecodeError:
                tool_args = {}
            tool_question = tool_args.get("question", question)

            tool_calls_made.append({"tool": tool_name, "question": tool_question})

            if tool_name == "search_anthropic_info":
                chunks = retrieve_anthropic_func(tool_question)
            elif tool_name == "search_financial":
                chunks = retrieve_financial_func(tool_question)
            else:
                chunks = []

            all_retrieved_chunks.extend(chunks)

            tool_result_text = "\n\n".join(chunks) if chunks else "No relevant information found."
            next_input.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": tool_result_text
            })
    else:
        # Loop exhausted MAX_TOOL_ITERATIONS without the model settling on a final answer
        answer = "I wasn't able to settle on an answer after several tool calls - please rephrase the question."

    return {
        "question": question,
        "answer": answer,
        "tool_calls": tool_calls_made,
        "retrieved_chunks": all_retrieved_chunks,
        "last_response_id": previous_response_id
    }


if __name__ == "__main__":
    from anthropic_retriever import retrieve_anthropic_chunks
    from financial_retrieval import retrieve_financial_chunks

    test_questions = [
        "Who founded Anthropic?",
        "What was the Unrestricted Public Support amount?",
        "Is Claude 3.7 Sonnet still Anthropic's latest model, or has that changed?",
        "What is the total checking/savings balance, and who is Anthropic's CEO?"
    ]

    for q in test_questions:
        result = ask_with_tools(q, retrieve_anthropic_chunks, retrieve_financial_chunks)
        print(f"Q: {q}")
        print(f"Tools used: {[t['tool'] for t in result['tool_calls']]}")
        print(f"A: {result['answer'][:200]}...\n")
