"""
Interactive Chat Interface

Ask questions about Anthropic, the financial data, or have the agent validate
document claims against a live web search, all in real-time.
"""

import os
import sys
from dotenv import load_dotenv

# web_search results can contain Unicode punctuation (smart quotes, narrow
# no-break spaces, etc.) that crashes print() on Windows consoles using a
# legacy codepage - force UTF-8 so live search content never kills the CLI.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

load_dotenv()

from anthropic_retriever import retrieve_anthropic_chunks
from agent import ask_with_tools
from financial_retrieval import retrieve_financial_chunks


def print_header():
    print("\n" + "=" * 80)
    print("MULTI-SOURCE RAG AGENT - INTERACTIVE CHAT")
    print("=" * 80)
    print("\nAsk questions about:")
    print("  - Anthropic: founding, products, Constitutional AI, safety research, funding")
    print("  - Finance: accounts, dollar amounts, budget vs actual, balance sheet")
    print("  - Validation: ask if something about Anthropic is still true/current/changed")
    print("    to trigger a live web search alongside the document")
    print("\nType 'quit' to exit, 'help' for examples")
    print("=" * 80 + "\n")


def print_help():
    examples = [
        ("Anthropic document examples:", [
            "Who founded Anthropic?",
            "What is Constitutional AI?",
            "What is the Model Context Protocol?"
        ]),
        ("Financial examples:", [
            "What was the Unrestricted Public Support amount?",
            "What is the Balance Sheet total for checking/savings?",
            "What was the year-over-year change in Unrestricted Public Support?"
        ]),
        ("Validation examples (triggers web_search):", [
            "Is Claude 3.7 Sonnet still Anthropic's latest model?",
            "Are Google and Amazon still Anthropic's main investors?"
        ]),
    ]

    print("\n" + "-" * 80)
    print("EXAMPLES")
    print("-" * 80)
    for category, qs in examples:
        print(f"\n{category}")
        for q in qs:
            print(f"  -> {q}")
    print("-" * 80 + "\n")


def format_answer(result) -> None:
    answer = result["answer"]
    tool_calls = result["tool_calls"]
    retrieved_chunks = result["retrieved_chunks"]

    print("\n" + "-" * 80)
    print("ANSWER")
    print("-" * 80)
    print(answer)

    if tool_calls:
        print("\n" + "-" * 80)
        print("TOOLS USED")
        print("-" * 80)
        for tc in tool_calls:
            if tc["tool"] == "web_search":
                print(f"  - web_search: \"{tc['question']}\"")
            else:
                print(f"  - {tc['tool']}: \"{tc['question']}\"")

    if retrieved_chunks:
        print("\n" + "-" * 80)
        print("CHUNKS RETRIEVED")
        print("-" * 80)
        for i, chunk in enumerate(retrieved_chunks):
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            print(f"  [{i+1}] {preview}")

    print("-" * 80 + "\n")


def run_chat():
    print_header()
    previous_response_id = None

    while True:
        try:
            question = input("You: ").strip()

            if not question:
                continue

            if question.lower() == "quit":
                print("\nGoodbye!")
                break

            if question.lower() == "help":
                print_help()
                continue

            result = ask_with_tools(
                question,
                retrieve_anthropic_chunks,
                retrieve_financial_chunks,
                previous_response_id
            )

            previous_response_id = result["last_response_id"]
            format_answer(result)

        except (KeyboardInterrupt, EOFError):
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {str(e)}\n")


if __name__ == "__main__":
    run_chat()
