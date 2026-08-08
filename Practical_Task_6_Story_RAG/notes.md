# Challenge 1: Why Can't You Just Paste the Whole Story In?

## Q1: What actually happens if you paste the entire story into the system prompt and just ask your question directly?

The model answers all questions accurately. When tested, it correctly answered "The name of the fishing boat was the Kestrel Anne" and "Mattias Holt went missing in 1975" — both explicit and buried facts were retrieved reliably by reading through the entire narrative.

## Q2: If that works for this story, would it still work if the story were 300 pages long instead of a few?

No. A 300-page story would cause the model to make logic errors, hallucinate details, and become confused by the volume of information. The context window would also become too expensive in tokens, making it impractical and costly to process.

## Q3: Is there a difference between "the model technically has this text somewhere in its context" and "the model can reliably find the one detail relevant to this question"?

Yes. Having text in context means the information exists, but the model isn't actively searching for what's relevant—it just predicts statistically. Reliably finding a detail requires active reasoning: understanding the question, filtering for relevance, and retrieving the exact answer. As stories grow larger, this becomes harder and less reliable.

# Challenge 2: Breaking the Story Into Searchable Pieces

## Q1: What is your splitting strategy, and why did you choose it?

Split on paragraph breaks (`\n\n`) first, since authors already mark meaningful boundaries. If any paragraph exceeds 1000 characters, recursively split it further on sentence boundaries (`. `). This preserves complete thoughts while keeping chunks focused and retrievable. We also add 150-character overlap between chunks — each chunk (except the first) includes the last 150 characters of the previous chunk to preserve context across boundaries.

## Q2: How many pieces did it produce for your story?

The story was split into 12 chunks total. Chunk 1 is the title (30 chars). Chunks 2-12 range from 393-1077 characters, with each chunk (except the first) containing 150-character overlap from the previous chunk. Larger paragraphs like Chunk 6 (1077 chars) and Chunk 7 (1019 chars) stayed under the 1000-character limit after overlap was added.

## Q3: What could go wrong if a split lands in the middle of a sentence, or separates a cause from its effect?

If a split severs a cause-and-effect pair, the context and meaning of each chunk is lost independently — the effect chunk won't make sense without the cause. The overlap mechanism prevents this by repeating the last 150 characters of the previous chunk at the start of the next one. For example, Chunk 3 starts with "had come up fast from the southeast..." (overlap from Chunk 2), ensuring that causal links and other critical connections survive the boundary.

## Q4: Should neighboring pieces share any of the same text with each other, or should each piece be a completely clean, non-overlapping slice?

Yes, neighboring pieces should overlap. We add 150 characters of the previous chunk to the start of each new chunk. Chunk 4 demonstrates this — it starts with "e pool at the base of the lighthouse..." (the tail end of Chunk 3's content), ensuring that information spanning a chunk boundary doesn't get orphaned, and that critical context is preserved even when retrieval picks individual chunks to send to the model.

# Challenge 3: Representing Meaning, Not Just Words

## Q1: What you sent to the embeddings endpoint, what came back, and your explanation of what that output represents

We sent each of the 12 story chunks to OpenAI's embeddings endpoint individually using the `text-embedding-3-small` model. We got back 12 vectors, each containing 1536 numbers. These numbers map the semantic meaning of that chunk into a 1536-dimensional space. Each dimension captures different aspects of meaning — there's no way to interpret individual numbers in isolation, but their positions collectively represent what the text is about. Two chunks with similar meaning land close together in this space, which is why we can measure similarity using cosine similarity.

## Q2: How would you recognize "who saved the boy from the river" and "she pulled him from the water" as related without keyword rules?

Both phrases embed to vectors that land close together in the 1536-dimensional space because the embedding model learned during training that these phrases appear in similar contexts and convey the same idea. Cosine similarity between their two vectors would be high (close to 1), even though they share almost no words. This is why embeddings work better than keyword matching — they capture meaning, not just vocabulary.

## Q3: How does the retrieval system work in practice?

The retrieval system embeds the user's question to a vector, calculates cosine similarity between that question vector and all 12 chunk vectors, then sorts by similarity and returns the top-3 most relevant chunks. These chunks can come from anywhere in the story — they're selected based on semantic relevance, not sequential order. The model then synthesizes an answer using only those retrieved chunks as context, producing grounded, accurate answers that avoid hallucination.

# Challenge 4: Finding the Right Piece

## Q1: If every piece of the story has a numeric representation, and you generate one for an incoming question the same way, how would you decide which piece is the closest match?

Embed the question to a vector using the same embedding model (`text-embedding-3-small`) that embedded all the chunks. Then calculate cosine similarity between the question vector and each chunk vector. The chunk with the highest similarity score is the closest match. For example, when asked "What happened to Mattias Holt?", the system calculated similarity scores for all 12 chunks and found that Chunks 7, 6, and 10 had the highest scores (0.4999, 0.4570, 0.4902), making them the most relevant.

## Q2: Research "cosine similarity." What does it measure, and why might it be a reasonable way to compare two of these representations?

Cosine similarity measures the angle between two vectors in high-dimensional space. The formula is: (A · B) / (||A|| × ||B||), which returns a value between -1 and 1. It's ideal for embeddings because it only cares about direction (meaning), not magnitude (length). Two texts of completely different lengths but identical meaning will have high cosine similarity because they point in the same direction. This makes it better than distance-based metrics, which would penalize longer texts unfairly.

## Q3: Do you need a specialized database to do this comparison, or can you do it yourself with everything held in memory? At roughly what scale does that stop being practical?

You can do it in memory with simple Python loops and math operations. Our system with 12 chunks calculates all similarities instantly. This approach works fine for hundreds or even thousands of chunks. However, at scale (millions of chunks for enterprise knowledge bases), you'd need specialized vector databases like Pinecone, Weaviate, or Milvus that index vectors for fast retrieval. These databases use algorithms like HNSW (Hierarchical Navigable Small World) to avoid comparing against every vector.

## Q4: If you retrieve more than one piece for a question, how would you decide how many is enough? What might go wrong if you retrieve too few? Too many?

We chose top-k=3 as a practical balance. Too few chunks (top-1) risks missing context — if the answer spans multiple related sections, retrieving only one chunk loses important information, forcing the model to hallucinate the rest. Too many chunks (top-10 or more) adds noise from irrelevant sections, wastes tokens, and can confuse the model with contradictory or tangential information. Top-3 provides enough context for most questions while staying efficient.

# Challenge 5: Wiring It Into the LLM

## Q1: What should a retrieval tool like `search_story` take as input and return as output?

Input: the user's question (text). Output: the top-3 most relevant chunks from the story that answer that question. The `retrieve_chunks()` function takes the question, embeds it, compares it to all chunk embeddings via cosine similarity, and returns the 3 chunks with highest similarity scores.

## Q2: When should the model decide to call this tool — every time or sometimes?

Every time. Retrieval always runs before answering because it's fast (just vector math) and ensures every answer is grounded in the story. The model never answers without checking whether the context exists in the chunks first.

## Q3: Once the tool returns chunks, what has to happen next for that content to actually shape the model's final answer? Where does it need to end up?

The retrieved chunks are passed directly into the `ask_about_story()` function as the `retrieved_chunks` parameter. These chunks become the context in the user message: "Here are story excerpts: [chunks]. Question: [user's question]." The model then synthesizes an answer using only that context, avoiding hallucination.

## Q4: Trace the full round trip: user asks question → ? → ? → ? → final answer appears

User asks question → `retrieve_chunks()` embeds question → calculates cosine similarity vs all 12 chunk embeddings → sorts by score (highest first) → returns top-3 chunks → `ask_about_story()` sends chunks + question to the model → model generates answer based only on those chunks → answer printed to user.