"""
Interactive Chat Interface

Ask questions about the story and financial data in real-time.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from story_retriever import retrieve_story_chunks
from agent import ask_with_tools
from financial_retrieval import retrieve_financial_chunks


def print_header():
    print("\n" + "="*80)
    print("DUAL-TOOL AGENT - INTERACTIVE CHAT")
    print("="*80)
    print("\nAsk questions about:")
    print("  • Story: Elena, Tomas, Henrik, the lighthouse, the compass, events")
    print("  • Finance: accounts, dollar amounts, budget vs actual, balance sheet")
    print("  • Mixed: both story and financial questions")
    print("\nType 'quit' to exit, 'help' for examples")
    print("="*80 + "\n")


def print_help():
    examples = [
        ("Story examples:", [
            "Who pulled Tomas out of the water?",
            "What was Tomas's father's name?",
            "How is the compass connected to both families?"
        ]),
        ("Financial examples:", [
            "What was the Unrestricted Public Support amount?",
            "What is the Balance Sheet total for checking/savings?",
            "What was the year-over-year change in Unrestricted Public Support?"
        ]),
    ]
    
    print("\n" + "-"*80)
    print("EXAMPLES")
    print("-"*80)
    for category, qs in examples:
        print(f"\n{category}")
        for q in qs:
            print(f"  → {q}")
    print("-"*80 + "\n")


def format_answer(result) -> None:
    answer = result["answer"]
    tool_calls = result["tool_calls"]
    retrieved_chunks = result["retrieved_chunks"]
    
    print("\n" + "-"*80)
    print("ANSWER")
    print("-"*80)
    print(answer)
    
    if tool_calls:
        print("\n" + "-"*80)
        print("TOOLS USED")
        print("-"*80)
        for tc in tool_calls:
            print(f"  • {tc['tool']}")
    
    if retrieved_chunks:
        print("\n" + "-"*80)
        print("CHUNKS RETRIEVED")
        print("-"*80)
        for i, chunk in enumerate(retrieved_chunks):
            preview = chunk[:100] + "..." if len(chunk) > 100 else chunk
            print(f"  [{i+1}] {preview}")
    
    print("-"*80 + "\n")


def run_chat():
    print_header()
    conversation_history = None
    
    while True:
        try:
            question = input("You: ").strip()
            
            if not question:
                continue
            
            if question.lower() == "quit":
                print("\n✓ Goodbye!")
                break
            
            if question.lower() == "help":
                print_help()
                continue
            
            result = ask_with_tools(
                question,
                retrieve_story_chunks,
                retrieve_financial_chunks,
                conversation_history
            )
            
            conversation_history = result["conversation_history"]
            format_answer(result)
        
        except KeyboardInterrupt:
            print("\n\n✓ Goodbye!")
            break
        except Exception as e:
            print(f"\n✗ Error: {str(e)}\n")


if __name__ == "__main__":
    run_chat()