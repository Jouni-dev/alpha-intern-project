"""
Financial Retrieval Module

Manages ChromaDB collection for financial data.
Stores financial chunks with embeddings.
Provides retrieval interface for agent.
"""

import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI
from typing import List, Dict, Any

print("[financial_retrieval] Module loaded")

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

chroma_client = chromadb.PersistentClient(path="./chroma_db")


def initialize_financial_collection(chunks: List[Dict[str, Any]]) -> chromadb.Collection:
    """Initialize financial ChromaDB collection and store chunks."""
    print("[initialize_financial_collection] Initializing collection...")
    
    collection = chroma_client.get_or_create_collection(
        name="financial_chunks",
        metadata={"document_type": "financial_pdf", "source": "mid_Financial.pdf"}
    )
    
    if len(chunks) == 0:
        print("[initialize_financial_collection] No chunks to store")
        return collection
    
    print(f"[initialize_financial_collection] Processing {len(chunks)} chunks...")
    
    ids = []
    texts = []
    metadatas = []
    
    for chunk in chunks:
        chunk_id = f"financial_{chunk['page']}_{chunk['table_index']}_{chunk.get('row_index', 0)}"
        ids.append(chunk_id)
        texts.append(chunk["text"])
        metadatas.append({
            "page": str(chunk["page"]),
            "report_type": chunk["report_type"],
            "table_index": str(chunk["table_index"]),
            "document_type": "financial_pdf"
        })
    
    # Batch embed all chunks in one API call
    print("[initialize_financial_collection] Embedding all chunks (batch)...")
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    embeddings = [item.embedding for item in response.data]
    
    print("[initialize_financial_collection] Storing in ChromaDB...")
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    
    print(f"[initialize_financial_collection] ✓ Stored {len(ids)} chunks")
    return collection


def get_financial_collection() -> chromadb.Collection:
    """Get existing financial collection."""
    return chroma_client.get_collection(name="financial_chunks")


def retrieve_financial_chunks(question: str, k: int = 3) -> List[str]:
    """Retrieve top-k financial chunks relevant to the question."""
    print(f"[retrieve_financial_chunks] Retrieving top-{k} chunks for: {question[:60]}...")
    
    collection = get_financial_collection()
    
    # Embed the question
    print("[retrieve_financial_chunks] Embedding question...")
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    )
    question_embedding = response.data[0].embedding
    
    # Query ChromaDB
    print("[retrieve_financial_chunks] Querying ChromaDB...")
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=k
    )
    
    chunks = results["documents"][0] if results["documents"] else []
    print(f"[retrieve_financial_chunks] Retrieved {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        print(f"[retrieve_financial_chunks] Chunk {i+1}: {chunk[:80]}...")
    
    return chunks


if __name__ == "__main__":
    from financial_extraction import extract_financial_chunks
    
    print("[__main__] Starting financial retrieval setup...\n")
    
    print("[__main__] Extracting tables from PDF...")
    chunks = extract_financial_chunks("./mid_Financial.pdf")
    
    print("\n[__main__] Initializing ChromaDB collection...")
    collection = initialize_financial_collection(chunks)
    
    print("\n[__main__] Testing retrieval...\n")
    test_questions = [
        "What was the Unrestricted Public Support in the Actual vs Plan?",
        "What is the total checking/savings balance?",
        "What changed year-over-year?"
    ]
    
    for q in test_questions:
        print(f"\n[__main__] Q: {q}")
        results = retrieve_financial_chunks(q, k=2)
        for r in results:
            print(f"  → {r[:120]}...")