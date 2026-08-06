import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("story.txt", "r") as f:
    story = f.read()


def chunk_story(text, max_chunk_size=1000, overlap_size=150):
    """
    Split story into chunks with backward overlap.
    
    Args:
        text: full story text
        max_chunk_size: max characters per chunk
        overlap_size: characters to overlap between chunks
    
    Returns:
        list of chunks with overlap
    """
    # Step 1: Split on paragraph breaks
    paragraphs = text.split("\n\n")
    chunks = []
    
    # Step 2: Split oversized paragraphs into sentences
    for paragraph in paragraphs:
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
            chunked_with_overlap.append(overlap + " " + chunk)
    
    return chunked_with_overlap


system_prompt = """You are a helpful assistant. Answer questions based only on the provided story excerpts. If the answer is not in the excerpts, say you don't know."""


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


def initialize_chroma_collection(chunks):
    """
    Initialize Chroma collection with story chunks and embeddings.
    
    Args:
        chunks: list of story chunks
    
    Returns:
        Chroma collection object
    """
    # Initialize Chroma client with persistent storage
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # Try to get existing collection, or create new one
    try:
        collection = chroma_client.get_collection(name="story_chunks")
        print(f"Loaded existing Chroma collection with {collection.count()} chunks")
    except:
        # Collection doesn't exist, create it
        print("Creating new Chroma collection...")
        collection = chroma_client.create_collection(name="story_chunks")
        
        # Generate embeddings and add to collection
        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            collection.add(
                ids=[str(i)],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"chunk_index": i}]
            )
            print(f"Added chunk {i+1}/{len(chunks)}")
        
        print(f"Chroma collection created with {len(chunks)} chunks")
    
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
    return retrieved_chunks


def search_story_tool_definition():
    """
    Return the JSON schema for the search_story tool.
    This tells the model what the tool does and what parameters it accepts.
    """
    return {
        "type": "function",
        "function": {
            "name": "search_story",
            "description": "Search the story for information relevant to a user's question. Call this tool when the user asks about events, characters, or details from the story. The tool returns the 3 most relevant chunks from the story text.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The user's question about the story"
                    }
                },
                "required": ["question"],
                "additionalProperties": False
            }
        }
    }


# Initialize story chunks
chunks = chunk_story(story)

# Initialize Chroma collection
collection = initialize_chroma_collection(chunks)

print(f"RAG system ready: {len(chunks)} chunks in Chroma collection\n")

# Initialize conversation history for multi-turn dialogue
conversation_history = []

while True:
    question = input("\nAsk a question about the story (or 'quit' to exit): ")
    if question.lower() == "quit":
        break
    
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
        tools=[search_story_tool_definition()]
    )
    
    msg = response.choices[0].message
    
    # Check if the model wants to call a tool
    if msg.tool_calls:
        # Model decided it needs to search the story
        conversation_history.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})
        
        # Execute the tool call(s)
        for tool_call in msg.tool_calls:
            if tool_call.function.name == "search_story":
                # Parse the arguments
                args = json.loads(tool_call.function.arguments)
                user_question = args.get("question", question)
                
                # Retrieve chunks from Chroma
                retrieved = retrieve_chunks_from_chroma(user_question, collection, top_k=3)
                
                # Add tool result to conversation history
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": "\n\n".join(retrieved)
                })
        
        # Second API call: send tool results back to model for final answer
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=256,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history
            ],
            tools=[search_story_tool_definition()]
        )
        
        final_msg = final_response.choices[0].message
        answer = final_msg.content
        
        # Add final answer to conversation history
        conversation_history.append({"role": "assistant", "content": answer})
    else:
        # Model answered directly without needing the tool
        answer = msg.content
        conversation_history.append({"role": "assistant", "content": answer})
    
    print(f"\nAnswer: {answer}\n")