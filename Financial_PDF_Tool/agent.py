"""
Unified Multi-Tool Agent

Handles both story and financial tools. Decides which tool(s) to use
based on the question, using OpenAI function calling.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any, Callable

print("[agent] Module loaded")

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an AI assistant with access to two tools:

1. search_story - searches a lighthouse story for narrative content (characters, events, plot)
2. search_financial - searches a financial report for accounts, dollar amounts, budget vs actual, balance sheet data

Rules:
- If the question is about people, events, or narrative -> use search_story
- If the question is about money, accounts, numbers, or financial data -> use search_financial
- If the question could need both -> call both tools
- If the question cannot be answered by either tool -> do not call any tool, and say you cannot answer it from the available documents
- Base your answer only on what the tools return. If the tools return nothing relevant, say you don't know."""


def define_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_story",
                "description": "Search the lighthouse story for narrative content about characters, events, plot, and emotions. Use this for questions about Elena, Tomas, Henrik, the lighthouse, the compass, or what happened.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "What to search for in the story"}
                    },
                    "required": ["question"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_financial",
                "description": "Search the financial report for accounts, line items, dollar amounts, budget vs actual, year-over-year comparisons, balance sheet items, revenue, and expenses. Use this for questions about financial data, money, accounts, or numbers.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string", "description": "What financial information to search for"}
                    },
                    "required": ["question"]
                }
            }
        }
    ]


def ask_with_tools(
    question: str,
    retrieve_story_func: Callable[[str], List[str]],
    retrieve_financial_func: Callable[[str], List[str]],
    conversation_history: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Returns:
    {
        "question": ...,
        "answer": ...,
        "tool_calls": [{"tool": "search_story" | "search_financial", "question": ...}],
        "retrieved_chunks": [...],
        "conversation_history": [...]
    }
    """
    print(f"\n[agent] ========== NEW QUESTION ==========")
    print(f"[agent] Question: {question[:80]}...")

    if conversation_history is None:
        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

    messages = conversation_history + [{"role": "user", "content": question}]

    print("[agent] Making FIRST API call (tool decision)...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=define_tools(),
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message
    finish_reason = response.choices[0].finish_reason
    print(f"[agent] Finish reason: {finish_reason}")

    tool_calls_made = []
    all_retrieved_chunks = []

    if finish_reason == "tool_calls" and assistant_message.tool_calls:
        print(f"[agent] Model requested {len(assistant_message.tool_calls)} tool call(s)")

        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}
            tool_question = tool_args.get("question", question)

            print(f"[agent] Tool: {tool_name} | Args: {tool_question[:60]}...")
            tool_calls_made.append({"tool": tool_name, "question": tool_question})

            if tool_name == "search_story":
                chunks = retrieve_story_func(tool_question)
            elif tool_name == "search_financial":
                chunks = retrieve_financial_func(tool_question)
            else:
                print(f"[agent] WARNING: unknown tool '{tool_name}'")
                chunks = []

            all_retrieved_chunks.extend(chunks)
            print(f"[agent] Retrieved {len(chunks)} chunks")

            tool_result_text = "\n\n".join(chunks) if chunks else "No relevant information found."
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result_text
            })

        print("[agent] Making SECOND API call (synthesis)...")
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        answer = final_response.choices[0].message.content
        messages.append({"role": "assistant", "content": answer})

    else:
        answer = assistant_message.content
        messages.append({"role": "assistant", "content": answer})
        print("[agent] No tool call made - model answered directly")

    print(f"[agent] Answer: {answer[:100]}...")
    print("[agent] ========== QUESTION COMPLETE ==========\n")

    return {
        "question": question,
        "answer": answer,
        "tool_calls": tool_calls_made,
        "retrieved_chunks": all_retrieved_chunks,
        "conversation_history": messages
    }


if __name__ == "__main__":
    from financial_retrieval import retrieve_financial_chunks

    def retrieve_story_chunks_stub(q):
        print(f"[stub] Would search story for: {q}")
        return [f"[STUB] Story chunk placeholder for: {q}"]

    print("[__main__] Testing dual-tool agent...\n")

    test_questions = [
        "Who pulled Tomas out of the water?",
        "What was the Unrestricted Public Support amount in the Actual vs Plan report?",
        "What is the answer to life, the universe, and everything?"
    ]

    for q in test_questions:
        result = ask_with_tools(q, retrieve_story_chunks_stub, retrieve_financial_chunks)
        print(f"Q: {q}")
        print(f"A: {result['answer'][:150]}...")
        print(f"Tools used: {[t['tool'] for t in result['tool_calls']]}\n")