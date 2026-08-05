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


# Create chunks for retrieval (used in Challenge 3+)
chunks = chunk_story(story)


while True:
    question = input("\nAsk a question about the story (or 'quit' to exit): ")
    if question.lower() == "quit":
        break
    answer = ask_about_story(question)
    print(f"\nAnswer: {answer}\n")