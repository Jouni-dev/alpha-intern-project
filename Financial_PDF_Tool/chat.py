"""
Interactive Chat Interface

Ask questions about the story and financial data in real-time.
The dual-tool agent picks the right tool and synthesizes answers.
"""

import os
from dotenv import load_dotenv
from typing import List, Dict, Any

print("[chat] Module loaded")

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
        ("Mixed examples:", [
            "Compare the story to the financial data",
            "Did the story mention anything about Wikimedia Foundation?"
        ])
    ]
    
    print("\n" + "-"*80)
    print("EXAMPLES")
    print("-"*80)
    for category, qs in examples:
        print(f"\n{category}")
        for q in qs:
            print(f"  → {q}")
    print("-"*80 + "\n")


def format_answer(result: Dict[str, Any]) -> None:
    """Pretty-print the agent's response."""
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
            print(f"  • {tc['tool']}: {tc['question']}")
    
    if retrieved_chunks:
        print("\n" + "-"*80)
        print("RETRIEVED CHUNKS")
        print("-"*80)
        for i, chunk in enumerate(retrieved_chunks):
            preview = chunk[:120] + "..." if len(chunk) > 120 else chunk
            print(f"  [{i+1}] {preview}")
    
    print("-"*80 + "\n")


def run_chat():
    """Interactive chat loop."""
    print_header()
    
    conversation_history = None
    
    while True:
        try:
            question = input("You: ").strip()
            
            if not question:
                continue
            
            if question.lower() == "quit":
                print("\n[chat] Goodbye!")
                break
            
            if question.lower() == "help":
                print_help()
                continue
            
            print("\n[chat] Processing...")
            
            result = ask_with_tools(
                question,
                retrieve_story_chunks,
                retrieve_financial_chunks,
                conversation_history
            )
            
            # Update conversation history for multi-turn
            conversation_history = result["conversation_history"]
            
            format_answer(result)
        
        except KeyboardInterrupt:
            print("\n\n[chat] Interrupted by user. Goodbye!")
            break
        except Exception as e:
            print(f"\n[chat] Error: {str(e)}")
            print("[chat] Please try again.\n")


if __name__ == "__main__":
    run_chat()