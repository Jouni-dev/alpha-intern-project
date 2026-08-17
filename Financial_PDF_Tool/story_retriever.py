"""
Story Retriever Wrapper

Exposes story retrieval as a simple function that returns chunks,
matching the interface of retrieve_financial_chunks.

This separation allows ask_about_story (full agent with synthesis)
to stay independent, while story_retriever provides just-chunks
retrieval for use in the dual-tool agent.
"""

from story_rag import retrieve_chunks_from_chroma, collection
from typing import List

print("[story_retriever] Module loaded")


def retrieve_story_chunks(question: str, k: int = 3) -> List[str]:
    """
    Retrieve top-k story chunks relevant to the question.
    
    Args:
        question: user's question
        k: number of chunks to retrieve
    
    Returns:
        list of chunk strings (no answer synthesis)
    """
    print(f"[retrieve_story_chunks] Retrieving top-{k} chunks for: {question[:60]}...")
    
    chunks = retrieve_chunks_from_chroma(question, collection, top_k=k)
    print(f"[retrieve_story_chunks] Retrieved {len(chunks)} chunks")
    
    return chunks


if __name__ == "__main__":
    test_questions = [
        "Who pulled Tomas out of the water?",
        "What was the lighthouse keeper's name?",
        "Tell me about the compass"
    ]
    
    for q in test_questions:
        print(f"\nQ: {q}")
        results = retrieve_story_chunks(q, k=2)
        for r in results:
            print(f"  → {r[:100]}...")