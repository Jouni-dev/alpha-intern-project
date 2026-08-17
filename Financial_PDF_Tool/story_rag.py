import os
import json
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

print("[story_rag] Loading environment and initializing OpenAI client...")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("[story_rag] OpenAI client initialized")

print("[story_rag] Reading story.txt...")
with open("story.txt", "r") as f:
    story = f.read()
print(f"[story_rag] Story loaded: {len(story)} characters")


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
    print(f"[chunk_story] Starting chunking: max_size={max_chunk_size}, overlap={overlap_size}")
    
    # Step 1: Split on paragraph breaks
    paragraphs = text.split("\n\n")
    print(f"[chunk_story] Found {len(paragraphs)} paragraphs")
    chunks = []
    
    # Step 2: Split oversized paragraphs into sentences
    for para_idx, paragraph in enumerate(paragraphs):
        if len(paragraph) <= max_chunk_size:
            chunks.append(paragraph)
            print(f"[chunk_story] Para {para_idx}: kept as-is ({len(paragraph)} chars)")
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
            print(f"[chunk_story] Para {para_idx}: split into {len([c for c in chunks if c])} chunks")
    
    # Step 3: Add backward overlap between chunks
    chunked_with_overlap = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            # First chunk has no overlap
            chunked_with_overlap.append(chunk)
            print(f"[chunk_story] Chunk {i}: no overlap ({len(chunk)} chars)")
        else:
            # Get the last overlap_size characters from previous chunk
            previous_chunk = chunks[i - 1]
            overlap = previous_chunk[-overlap_size:] if len(previous_chunk) >= overlap_size else previous_chunk
            # Prepend overlap to current chunk
            final_chunk = overlap + " " + chunk
            chunked_with_overlap.append(final_chunk)
            print(f"[chunk_story] Chunk {i}: added overlap ({len(final_chunk)} chars total)")
    
    print(f"[chunk_story] Chunking complete: {len(chunked_with_overlap)} chunks with overlap")
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
    print(f"[get_embedding] Requesting embedding for {len(text)} chars of text")
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    embedding = response.data[0].embedding
    print(f"[get_embedding] Received embedding: {len(embedding)} dimensions")
    return embedding


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
    similarity = dot_product / (magnitude1 * magnitude2)
    print(f"[cosine_similarity] Calculated: {similarity:.4f}")
    return similarity


def initialize_chroma_collection(chunks):
    """
    Initialize Chroma collection with story chunks and embeddings.
    
    Args:
        chunks: list of story chunks
    
    Returns:
        Chroma collection object
    """
    print(f"[initialize_chroma_collection] Initializing with {len(chunks)} chunks")
    print(f"[initialize_chroma_collection] Creating PersistentClient at ./chroma_db")
    
    # Initialize Chroma client with persistent storage
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    
    # Try to get existing collection, or create new one
    try:
        collection = chroma_client.get_collection(name="story_chunks")
        count = collection.count()
        print(f"[initialize_chroma_collection] Loaded existing collection with {count} chunks")
    except Exception as e:
        # Collection doesn't exist, create it
        print(f"[initialize_chroma_collection] Collection doesn't exist, creating new one")
        print(f"[initialize_chroma_collection] Creating collection 'story_chunks'")
        collection = chroma_client.create_collection(name="story_chunks")
        
        # Generate embeddings and add to collection
        for i, chunk in enumerate(chunks):
            print(f"[initialize_chroma_collection] Processing chunk {i+1}/{len(chunks)}")
            embedding = get_embedding(chunk)
            collection.add(
                ids=[str(i)],
                embeddings=[embedding],
                documents=[chunk],
                metadatas=[{"chunk_index": i}]
            )
            print(f"[initialize_chroma_collection] Added chunk {i+1}/{len(chunks)} to collection")
        
        print(f"[initialize_chroma_collection] Collection created and populated with {len(chunks)} chunks")
    
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
    print(f"[retrieve_chunks_from_chroma] Retrieving top-{top_k} chunks for question")
    print(f"[retrieve_chunks_from_chroma] Question: '{question[:80]}...'")
    
    # Get embedding for the question
    print(f"[retrieve_chunks_from_chroma] Embedding the question...")
    question_embedding = get_embedding(question)
    
    # Query Chroma collection
    print(f"[retrieve_chunks_from_chroma] Querying Chroma collection...")
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=top_k
    )
    
    # Extract and return the documents
    retrieved_chunks = results["documents"][0] if results["documents"] else []
    print(f"[retrieve_chunks_from_chroma] Retrieved {len(retrieved_chunks)} chunks")
    for idx, chunk in enumerate(retrieved_chunks):
        print(f"[retrieve_chunks_from_chroma] Chunk {idx+1}: {len(chunk)} chars, first 60: '{chunk[:60]}...'")
    
    return retrieved_chunks


def search_story_tool_definition():
    """
    Return the JSON schema for the search_story tool.
    This tells the model what the tool does and what parameters it accepts.
    """
    print(f"[search_story_tool_definition] Returning tool definition for search_story")
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


def ask_about_story(question, conversation_history=None):
    """
    Ask a question about the story. The model decides whether to retrieve chunks or answer directly.
    
    Args:
        question: user's question
        conversation_history: optional list of prior messages (for multi-turn)
    
    Returns:
        dict with "answer", "retrieved_chunks", and updated "conversation_history"
    """
    print(f"\n[ask_about_story] ========== NEW QUESTION ==========")
    print(f"[ask_about_story] Question: '{question}'")
    
    if conversation_history is None:
        conversation_history = []
        print(f"[ask_about_story] Conversation history is empty, starting fresh")
    else:
        print(f"[ask_about_story] Using existing conversation history ({len(conversation_history)} messages)")
    
    # Add user question to conversation history
    conversation_history.append({"role": "user", "content": question})
    print(f"[ask_about_story] Added user message to history (now {len(conversation_history)} messages)")
    
    # First API call: send question + tool definitions to the model
    print(f"[ask_about_story] Making FIRST API call to gpt-4o-mini (decision call)...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        messages=[
            {"role": "system", "content": system_prompt},
            *conversation_history
        ],
        tools=[search_story_tool_definition()]
    )
    
    print(f"[ask_about_story] Received response from FIRST API call")
    msg = response.choices[0].message
    print(f"[ask_about_story] Response has content: {msg.content is not None}")
    print(f"[ask_about_story] Response has tool_calls: {msg.tool_calls is not None}")
    
    retrieved_chunks = []
    
    # Check if the model wants to call a tool
    if msg.tool_calls:
        print(f"[ask_about_story] Model requested tool call(s): {len(msg.tool_calls)} call(s)")
        
        # Model decided it needs to search the story
        conversation_history.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})
        print(f"[ask_about_story] Added assistant message with tool calls to history")
        
        # Execute the tool call(s)
        for tool_idx, tool_call in enumerate(msg.tool_calls):
            print(f"[ask_about_story] Processing tool call {tool_idx+1}/{len(msg.tool_calls)}")
            print(f"[ask_about_story] Tool name: {tool_call.function.name}")
            
            if tool_call.function.name == "search_story":
                # Parse the arguments
                print(f"[ask_about_story] Parsing tool arguments...")
                args = json.loads(tool_call.function.arguments)
                user_question = args.get("question", question)
                print(f"[ask_about_story] Tool argument 'question': '{user_question}'")
                
                # Retrieve chunks from Chroma
                print(f"[ask_about_story] Calling retrieve_chunks_from_chroma()...")
                retrieved_chunks = retrieve_chunks_from_chroma(user_question, collection, top_k=3)
                
                # Add tool result to conversation history
                tool_result_content = "\n\n".join(retrieved_chunks)
                conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result_content
                })
                print(f"[ask_about_story] Added tool result to history: {len(tool_result_content)} chars")
        
        # Second API call: send tool results back to model for final answer
        print(f"[ask_about_story] Making SECOND API call to gpt-4o-mini (synthesis call)...")
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=256,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history
            ],
            tools=[search_story_tool_definition()]
        )
        
        print(f"[ask_about_story] Received response from SECOND API call")
        final_msg = final_response.choices[0].message
        answer = final_msg.content
        print(f"[ask_about_story] Final answer: '{answer[:100]}...'")
        
        # Add final answer to conversation history
        conversation_history.append({"role": "assistant", "content": answer})
        print(f"[ask_about_story] Added final answer to history (now {len(conversation_history)} messages)")
    else:
        # Model answered directly without needing the tool
        print(f"[ask_about_story] Model answered directly without tool call")
        answer = msg.content
        print(f"[ask_about_story] Direct answer: '{answer[:100]}...'")
        conversation_history.append({"role": "assistant", "content": answer})
        print(f"[ask_about_story] Added direct answer to history")
    
    print(f"[ask_about_story] ========== QUESTION COMPLETE ==========\n")
    
    return {
        "answer": answer,
        "retrieved_chunks": retrieved_chunks,
        "conversation_history": conversation_history
    }


# Initialize story chunks
print("\n[MODULE INIT] Starting module initialization...")
print("[MODULE INIT] Chunking story...")
chunks = chunk_story(story)

# Initialize Chroma collection
print("[MODULE INIT] Initializing Chroma collection...")
collection = initialize_chroma_collection(chunks)

print(f"[MODULE INIT] ✓ RAG system ready: {len(chunks)} chunks in Chroma collection\n")


# Interactive mode (optional, for manual testing)
if __name__ == "__main__":
    print("[INTERACTIVE MODE] Starting interactive mode...")
    conversation_history = []
    while True:
        question = input("\nAsk a question about the story (or 'quit' to exit): ")
        if question.lower() == "quit":
            print("[INTERACTIVE MODE] Exiting...")
            break
        
        result = ask_about_story(question, conversation_history)
        conversation_history = result["conversation_history"]
        print(f"\nAnswer: {result['answer']}\n")