import os
import json
import hashlib
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("anthropic_info.txt", "r") as f:
    anthropic_doc = f.read()


def chunk_document(text, max_chunk_size=1000, overlap_size=150):
    """
    Split document into chunks with backward overlap.

    Args:
        text: full document text
        max_chunk_size: max characters per chunk
        overlap_size: characters to overlap between chunks

    Returns:
        list of chunks with overlap
    """
    # Step 1: Split on paragraph breaks
    paragraphs = text.split("\n\n")
    chunks = []

    # Step 2: Split oversized paragraphs into sentences
    for para_idx, paragraph in enumerate(paragraphs):
        if len(paragraph) <= max_chunk_size:
            chunks.append(paragraph)
        else:
            # Split on sentence boundaries (. followed by space)
            sentences = paragraph.split(". ")
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 <= max_chunk_size:
                    current_chunk += sentence + ". "
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + ". "
            if current_chunk:
                chunks.append(current_chunk.strip())

    # Step 3: Add backward overlap between chunks
    chunked_with_overlap = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            # First chunk has no overlap
            chunked_with_overlap.append(chunk)
        else:
            # Get the last overlap_size characters from previous chunk
            previous_chunk = chunks[i - 1]
            overlap = previous_chunk[-overlap_size:] if len(previous_chunk) >= overlap_size else previous_chunk
            # Prepend overlap to current chunk
            final_chunk = overlap + " " + chunk
            chunked_with_overlap.append(final_chunk)

    print(f"[chunk_document] {len(chunked_with_overlap)} chunks produced")
    return chunked_with_overlap


system_prompt = """You are a helpful assistant. Answer questions based only on the provided Anthropic company information excerpts. If the answer is not in the excerpts, say you don't know."""


def get_embedding(text):
    """
    Get embedding vector for text using OpenAI's embedding model.

    Args:
        text: text to embed

    Returns:
        list of 1536 numbers representing the text's meaning
    """
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1, vec2: lists of numbers (embeddings)

    Returns:
        similarity score between 0 and 1
    """
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = sum(a ** 2 for a in vec1) ** 0.5
    magnitude2 = sum(b ** 2 for b in vec2) ** 0.5
    return dot_product / (magnitude1 * magnitude2)


def initialize_chroma_collection(chunks, document_text):
    """
    Initialize Chroma collection with Anthropic document chunks and embeddings.
    Re-embeds automatically if anthropic_info.txt has changed since the collection
    was last built (detected via a content hash stored in the collection metadata) -
    otherwise editing the document would silently keep serving stale chunks.

    Args:
        chunks: list of document chunks
        document_text: the full source document text, used to detect changes

    Returns:
        Chroma collection object
    """
    doc_hash = hashlib.sha256(document_text.encode("utf-8")).hexdigest()

    # Initialize Chroma client with persistent storage
    chroma_client = chromadb.PersistentClient(path="./chroma_db")

    # Try to get existing collection, or create new one
    try:
        collection = chroma_client.get_collection(name="anthropic_chunks")
        stored_hash = (collection.metadata or {}).get("source_hash")

        if stored_hash != doc_hash:
            print(f"[initialize_chroma_collection] Document changed since last run - rebuilding")
            chroma_client.delete_collection(name="anthropic_chunks")
            raise ValueError("stale collection deleted, falling through to rebuild")

        print(f"[initialize_chroma_collection] Loaded existing collection ({collection.count()} chunks, up to date)")
    except Exception:
        # Collection doesn't exist, or was just deleted for being stale - (re)create it
        collection = chroma_client.create_collection(
            name="anthropic_chunks",
            metadata={"source_hash": doc_hash}
        )

        # Generate embeddings and add to collection
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            collection.add(
                ids=[str(i)],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"chunk_index": i}]
            )

        print(f"[initialize_chroma_collection] Created and embedded {len(chunks)} chunks")

    return collection


def retrieve_chunks_from_chroma(question, collection, top_k=3):
    """
    Retrieve relevant chunks from Chroma collection.

    Args:
        question: user's question
        collection: Chroma collection object
        top_k: number of chunks to retrieve

    Returns:
        list of top-k relevant chunks
    """
    # Get embedding for the question
    question_embedding = get_embedding(question)

    # Query Chroma collection
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )

    # Extract and return the documents
    retrieved_chunks = results["documents"][0] if results["documents"] else []
    print(f"[search_anthropic_info] \"{question[:60]}\" -> {len(retrieved_chunks)} chunks")

    return retrieved_chunks


def search_anthropic_tool_definition():
    """
    Return the JSON schema for the search_anthropic_info tool.
    This tells the model what the tool does and what parameters it accepts.
    """
    return {
        "type": "function",
        "function": {
            "name": "search_anthropic_info",
            "description": "Search the Anthropic company document for information relevant to a user's question. Call this tool when the user asks about Anthropic's history, products, research, funding, or leadership. The tool returns the 3 most relevant chunks from the document.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The user's question about Anthropic"
                    }
                },
                "required": ["question"],
                "additionalProperties": False
            }
        }
    }


def ask_about_anthropic(question, conversation_history=None):
    """
    Ask a question about Anthropic. The model decides whether to retrieve chunks or answer directly.

    Args:
        question: user's question
        conversation_history: optional list of prior messages (for multi-turn)

    Returns:
        dict with "answer", "retrieved_chunks", and updated "conversation_history"
    """
    if conversation_history is None:
        conversation_history = []

    # Add user question to conversation history
    conversation_history.append({"role": "user", "content": question})

    # First API call: send question + tool definitions to the model
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        messages=[
            {"role": "system", "content": system_prompt},
            *conversation_history
        ],
        tools=[search_anthropic_tool_definition()]
    )

    msg = response.choices[0].message
    retrieved_chunks = []

    # Check if the model wants to call a tool
    if msg.tool_calls:
        # Model decided it needs to search the document
        conversation_history.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})

        # Execute the tool call(s)
        for tool_call in msg.tool_calls:
            if tool_call.function.name == "search_anthropic_info":
                args = json.loads(tool_call.function.arguments)
                user_question = args.get("question", question)

                # Retrieve chunks from Chroma
                retrieved_chunks = retrieve_chunks_from_chroma(user_question, collection, top_k=3)

                # Add tool result to conversation history
                tool_result_content = "\n\n".join(retrieved_chunks)
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_content
                })

        # Second API call: send tool results back to model for final answer
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=256,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history
            ],
            tools=[search_anthropic_tool_definition()]
        )

        final_msg = final_response.choices[0].message
        answer = final_msg.content
        conversation_history.append({"role": "assistant", "content": answer})
    else:
        # Model answered directly without needing the tool
        answer = msg.content
        conversation_history.append({"role": "assistant", "content": answer})

    return {
        "answer": answer,
        "retrieved_chunks": retrieved_chunks,
        "conversation_history": conversation_history
    }


# Initialize document chunks and Chroma collection
chunks = chunk_document(anthropic_doc)
collection = initialize_chroma_collection(chunks, anthropic_doc)
print(f"[anthropic_rag] Ready: {len(chunks)} chunks loaded\n")


# Interactive mode (optional, for manual testing)
if __name__ == "__main__":
    print("[INTERACTIVE MODE] Starting interactive mode...")
    conversation_history = []
    while True:
        question = input("\nAsk a question about Anthropic (or 'quit' to exit): ")
        if question.lower() == "quit":
            print("[INTERACTIVE MODE] Exiting...")
            break

        result = ask_about_anthropic(question, conversation_history)
        conversation_history = result["conversation_history"]
        print(f"\nAnswer: {result['answer']}\n")
