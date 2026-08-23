"""
Anthropic Info Retriever Wrapper

Exposes Anthropic document retrieval as chunks-only function for the multi-tool agent.
"""

from anthropic_rag import retrieve_chunks_from_chroma, collection
from typing import List


def retrieve_anthropic_chunks(question: str, k: int = 3) -> List[str]:
    """Retrieve top-k Anthropic document chunks relevant to the question."""
    chunks = retrieve_chunks_from_chroma(question, collection, top_k=k)
    return chunks


if __name__ == "__main__":
    test_questions = [
        "Who founded Anthropic?",
        "What is Constitutional AI?",
        "Tell me about the Responsible Scaling Policy"
    ]

    for q in test_questions:
        results = retrieve_anthropic_chunks(q, k=2)
        print(f"Q: {q}")
        print(f"Retrieved {len(results)} chunks\n")
