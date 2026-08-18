"""
Unified Multi-Tool Agent

Dual-tool agent (story + financial) using OpenAI function calling.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from typing import List, Dict, Any, Callable

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """You are an AI assistant with access to two tools:

1. search_story - retrieves relevant story passages (characters, events, plot)
2. search_financial - retrieves relevant financial data (accounts, amounts, comparisons)

Rules:
- If the question is about people, events, or narrative -> use search_story
- If the question is about money, accounts, numbers, or financial data -> use search_financial
- If the question could need both -> call both tools
- If the question cannot be answered by either tool -> do not call any tool
- Base your answer ONLY on what the tools return."""


def define_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "search_story",
                "description": "Retrieve story passages about characters, events, plot, emotions.",
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
                "description": "Retrieve financial data about accounts, line items, dollar amounts, comparisons.",
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
    """Ask a question, model picks tool(s), retriever returns chunks, model synthesizes answer."""
    
    if conversation_history is None:
        conversation_history = [{"role": "system", "content": SYSTEM_PROMPT}]

    messages = conversation_history + [{"role": "user", "content": question}]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=define_tools(),
        tool_choice="auto"
    )

    assistant_message = response.choices[0].message
    finish_reason = response.choices[0].finish_reason

    tool_calls_made = []
    all_retrieved_chunks = []

    if finish_reason == "tool_calls" and assistant_message.tool_calls:
        messages.append(assistant_message)

        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            try:
                tool_args = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}
            tool_question = tool_args.get("question", question)

            tool_calls_made.append({"tool": tool_name, "question": tool_question})

            if tool_name == "search_story":
                chunks = retrieve_story_func(tool_question)
            elif tool_name == "search_financial":
                chunks = retrieve_financial_func(tool_question)
            else:
                chunks = []

            all_retrieved_chunks.extend(chunks)

            tool_result_text = "\n\n".join(chunks) if chunks else "No relevant information found."
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result_text
            })

        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        answer = final_response.choices[0].message.content
        messages.append({"role": "assistant", "content": answer})

    else:
        answer = assistant_message.content
        messages.append({"role": "assistant", "content": answer})

    return {
        "question": question,
        "answer": answer,
        "tool_calls": tool_calls_made,
        "retrieved_chunks": all_retrieved_chunks,
        "conversation_history": messages
    }


if __name__ == "__main__":
    from story_retriever import retrieve_story_chunks
    from financial_retrieval import retrieve_financial_chunks

    test_questions = [
        "Who pulled Tomas out of the water?",
        "What was the Unrestricted Public Support amount?",
        "What is the answer to life, the universe, and everything?"
    ]

    for q in test_questions:
        result = ask_with_tools(q, retrieve_story_chunks, retrieve_financial_chunks)
        print(f"Q: {q}")
        print(f"A: {result['answer'][:100]}...\n")