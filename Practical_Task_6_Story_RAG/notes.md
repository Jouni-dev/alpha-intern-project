# Challenge 1: Why Can't You Just Paste the Whole Story In?

## Q1: What actually happens if you paste the entire story into the system prompt and just ask your question directly?

The model answers all questions accurately. It successfully retrieves both explicit details (like character names) and buried facts (like specific events) by reading through the entire narrative.

## Q2: If that works for this story, would it still work if the story were 300 pages long instead of a few?

No. A 300-page story would cause the model to make logic errors, hallucinate details, and become confused by the volume of information. The context window would also become too expensive in tokens.

## Q3: Is there a difference between "the model technically has this text somewhere in its context" and "the model can reliably find the one detail relevant to this question"?

Yes. Having text in context means the information exists, but the model isn't actively searching for what's relevant—it just predicts statistically. Reliably finding a detail requires active reasoning: understanding the question, filtering for relevance, and retrieving the exact answer. As stories grow larger, this becomes harder and less reliable.

# Challenge 2: Breaking the Story Into Searchable Pieces

## Q1: What is your splitting strategy, and why did you choose it?

Split on paragraph breaks (`\n\n`) first, since authors already mark meaningful boundaries. If any paragraph exceeds 1000 characters, recursively split it further on sentence boundaries (`. `). This preserves complete thoughts while keeping chunks focused and retrievable. We also add 150-character overlap between chunks — each chunk (except the first) includes the last 150 characters of the previous chunk to preserve context across boundaries.

## Q2: How many pieces did it produce for your story?

The story was split into 3 chunks total. Chunk 1 is the title (30 chars). Chunk 2 combines the title and first paragraph (556 chars) with overlap from Chunk 1. Chunk 3 is the second paragraph (558 chars) with 150-character overlap from Chunk 2 at the beginning.

## Q3: What could go wrong if a split lands in the middle of a sentence, or separates a cause from its effect?

If a split severs a cause-and-effect pair, the context and meaning of each chunk is lost independently — the effect chunk won't make sense without the cause. The overlap mechanism prevents this by repeating the last 150 characters of the previous chunk at the start of the next one, ensuring that causal links and other critical connections survive the boundary.

## Q4: Should neighboring pieces share any of the same text with each other, or should each piece be a completely clean, non-overlapping slice?

Yes, neighboring pieces should overlap. We add 150 characters of the previous chunk to the start of each new chunk. This overlap ensures that information spanning a chunk boundary doesn't get orphaned, and that critical context is preserved even when retrieval picks individual chunks to send to the model.