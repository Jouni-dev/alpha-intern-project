"""
Story Retriever Wrapper

Exposes story retrieval as chunks-only function for dual-tool agent.
"""

from story_rag import retrieve_chunks_from_chroma, collection
from typing import List


def retrieve_story_chunks(question: str, k: int = 3) -> List[str]:
    """Retrieve top-k story chunks relevant to the question."""
    chunks = retrieve_chunks_from_chroma(question, collection, top_k=k)
    return chunks


if __name__ == "__main__":
    test_questions = [
        "Who pulled Tomas out of the water?",
        "What was the lighthouse keeper's name?",
        "Tell me about the compass"
    ]
    
    for q in test_questions:
        results = retrieve_story_chunks(q, k=2)
        print(f"Q: {q}")
        print(f"✓ Retrieved {len(results)} chunks\n")