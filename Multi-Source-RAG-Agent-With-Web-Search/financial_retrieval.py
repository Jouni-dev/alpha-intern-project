"""
Financial Retrieval Module

Manages ChromaDB collection for financial data.
"""

import os
from dotenv import load_dotenv
import chromadb
from openai import OpenAI
from typing import List, Dict, Any

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
chroma_client = chromadb.PersistentClient(path="./chroma_db")


def initialize_financial_collection(chunks: List[Dict[str, Any]]) -> chromadb.Collection:
    collection = chroma_client.get_or_create_collection(
        name="financial_chunks",
        metadata={"document_type": "financial_pdf", "source": "mid_Financial.pdf"}
    )
    
    if len(chunks) == 0:
        return collection
    
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
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    embeddings = [item.embedding for item in response.data]
    
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas
    )
    
    return collection


def get_financial_collection() -> chromadb.Collection:
    return chroma_client.get_collection(name="financial_chunks")


def retrieve_financial_chunks(question: str, k: int = 3) -> List[str]:
    collection = get_financial_collection()
    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    )
    question_embedding = response.data[0].embedding
    
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=k
    )

    retrieved_chunks = results["documents"][0] if results["documents"] else []
    print(f"[search_financial] \"{question[:60]}\" -> {len(retrieved_chunks)} chunks")

    return retrieved_chunks


if __name__ == "__main__":
    from financial_extraction import extract_financial_chunks
    
    chunks = extract_financial_chunks("./mid_Financial.pdf")
    collection = initialize_financial_collection(chunks)
    print(f"Stored {len(chunks)} chunks in ChromaDB")
    
    test_questions = [
        "What was the Unrestricted Public Support in the Actual vs Plan?",
        "What is the total checking/savings balance?",
        "What changed year-over-year?"
    ]
    
    for q in test_questions:
        results = retrieve_financial_chunks(q, k=2)
        print(f"\nQ: {q}")
        print(f"Retrieved {len(results)} chunks")