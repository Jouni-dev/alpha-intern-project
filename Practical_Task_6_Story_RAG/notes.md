# Challenge 1: Why Can't You Just Paste the Whole Story In?

## Q1: What actually happens if you paste the entire story into the system prompt and just ask your question directly?

The model answers all questions accurately. It successfully retrieves both explicit details (like character names) and buried facts (like specific events) by reading through the entire narrative.

## Q2: If that works for this story, would it still work if the story were 300 pages long instead of a few?

No. A 300-page story would cause the model to make logic errors, hallucinate details, and become confused by the volume of information. The context window would also become too expensive in tokens.

## Q3: Is there a difference between "the model technically has this text somewhere in its context" and "the model can reliably find the one detail relevant to this question"?

Yes. Having text in context means the information exists, but the model isn't actively searching for what's relevant—it just predicts statistically. Reliably finding a detail requires active reasoning: understanding the question, filtering for relevance, and retrieving the exact answer. As stories grow larger, this becomes harder and less reliable.