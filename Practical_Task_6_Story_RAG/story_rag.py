import os
from dotenv import load_dotenv
from openai import OpenAI

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


def ask_about_story(question, retrieved_chunks=None):
    context = ""
    if retrieved_chunks:
        context = "\n\n".join(retrieved_chunks)
    
    user_message = f"""Here are story excerpts:

{context}

Question: {question}"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    )
    return response.choices[0].message.content


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


def retrieve_chunks(question, chunks, chunk_embeddings, top_k=3):
    """
    Find the top-k most relevant chunks for a question.
    
    Args:
        question: user's question
        chunks: list of text chunks
        chunk_embeddings: list of embedding vectors for chunks
        top_k: how many chunks to return
    
    Returns:
        list of top-k chunks sorted by relevance
    """
    question_embedding = get_embedding(question)
    similarities = []
    
    for i, chunk_emb in enumerate(chunk_embeddings):
        sim = cosine_similarity(question_embedding, chunk_emb)
        similarities.append((i, sim, chunks[i]))
    
    # Sort by similarity (descending) and take top-k
    top_chunks = sorted(similarities, key=lambda x: x[1], reverse=True)[:top_k]
    return [chunk for _, _, chunk in top_chunks]


# Create chunks for retrieval
chunks = chunk_story(story)

# Create embeddings for all chunks
chunk_embeddings = []
for chunk in chunks:
    embedding = get_embedding(chunk)
    chunk_embeddings.append(embedding)

print(f"RAG system ready: {len(chunks)} chunks, {len(chunk_embeddings)} embeddings\n")

while True:
    question = input("\nAsk a question about the story (or 'quit' to exit): ")
    if question.lower() == "quit":
        break
    retrieved = retrieve_chunks(question, chunks, chunk_embeddings, top_k=3)
    answer = ask_about_story(question, retrieved)
    print(f"\nAnswer: {answer}\n")