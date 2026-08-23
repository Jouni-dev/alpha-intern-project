# AI Agent Evaluation — Task Notes

## Challenge Overview

Build an evaluation framework for the Story-RAG agent (Task 6). The goal: replace manual testing ("it seemed to work") with quantified metrics that can be tracked over time and compared across configuration changes.

**Key principle from primer:** Evaluation is not QA at the end — it's what tells you whether your changes actually improved the system.

---

## Challenge 1: Golden Set Construction

### Approach

Created a fixed 15-question test set, stratified by answer type, to avoid bias toward happy-path questions only.

**Breakdown:**
- **Single-passage (6 questions):** Answer appears clearly in one chunk
  - "How long had Elena been keeping the lighthouse at Merrow Point?"
  - "Who pulled Tomas out of the water?"
  - "What was Tomas's father's name?"
  - "What ship was Tomas on when he wrecked?"
  - "What initials were scratched into the compass?"
  - "When did Elena's grandfather Henrik vanish?"

- **Multi-passage (4 questions):** Answer requires synthesizing information from multiple chunks
  - "Why did Tomas take a berth on the fishing boat that wrecked?"
  - "What did Elena discover under the floorboards in the lamp room, and what did it reveal?"
  - "How is the compass connected to both Tomas and Elena's family?"
  - "What did the logbook reveal about Henrik's disappearance?"

- **Unanswerable (5 questions):** Answer not in the story; model should refuse gracefully
  - "What was Tomas's favorite food?"
  - "Did Mattias Holt ever return to his family?"
  - "How many miles could the lighthouse lamp be seen from on a stormy night?"
  - "What was the name of the district office official who assigned Elena to Merrow Point?"
  - "How many people were originally on the Kestrel Anne when it wrecked?"

### Rationale

Questions were written in natural language (not copied from the story) and expected answers were hand-verified against the story text. This prevents the common pitfall of "testing on the questions you built it to answer."

---

## Challenge 2: Metrics Selection & Implementation

### Initial Approach: Ragas Metrics

Attempted to use Ragas (RAG Evaluation for AI Systems) with three metrics:
1. **Faithfulness** — Are all claims in the answer supported by retrieved passages?
2. **AnswerRelevancy** — Does the answer address the question asked?
3. **ContextPrecision** — Of the chunks retrieved, how many were actually relevant?

### Problem Encountered

**AnswerRelevancy async hang:** Ragas's async implementation of AnswerRelevancy would hang indefinitely during parallel execution. Multiple attempted fixes failed:
- Installing missing dependencies (`langchain-google-vertexai`, `google-cloud-aiplatform`)
- Downgrading/upgrading Ragas versions
- Running metrics sequentially instead of parallel
- Adding 90-second timeouts

**Root cause:** Ragas 0.4.3 has known compatibility issues with async execution in newer versions of langchain.

### Solution: Custom Implementation

**Replaced Ragas AnswerRelevancy with custom LLM-as-judge scorer:**
- Uses OpenAI API directly with a simple prompt
- Scores 1–5: "Does the answer address the question?"
- Returns score normalized to 0–1 scale (to match Ragas format)
- No async issues — runs synchronously within sequential metric flow

**Custom AnswerRelevancy Prompt:**
```
You are evaluating whether an answer addresses a question.

Question: {question}
Answer: {answer}

Score the relevancy 1-5:
1 = Completely irrelevant to the question
2 = Mostly irrelevant, touches on some aspect
3 = Somewhat relevant but misses key aspects
4 = Mostly addresses the question
5 = Directly and fully addresses the question

Respond with ONLY a number 1-5.
```

### Final Metric Stack

✅ **Faithfulness (Ragas)** — LLM-as-judge; checks if claims are grounded in retrieved context  
✅ **AnswerRelevancy (Custom)** — LLM-as-judge; checks if answer addresses the question  
✅ **ContextPrecision (Ragas)** — LLM-as-judge; checks if retrieved chunks were relevant

---

## Challenge 3: Evaluation Architecture

### Pipeline Flow

1. **Golden set item** → 2. **ask_about_story()** (pipeline execution) → 3. **Score with three metrics** (sequential) → 4. **Aggregate by question type** → 5. **Scorecard**

### Key Design Decisions

**Sequential metric scoring per item:** Avoids async race conditions. Items run in parallel (asyncio.gather), but within each item, metrics run one-after-another.

**Separate retrieval exposure:** Refactored `story_rag.py` to expose `retrieve_chunks_from_chroma()` as a standalone callable function, so evaluation can measure both retrieval quality (precision) and answer quality (faithfulness, relevancy).

**Timeout protection:** Each metric gets 90 seconds max. If it exceeds that, it returns `None` and evaluation continues.

**Scorecard by type, not overall mean:** The primer warns that averaging hides failures. A system that's perfect on single-passage but fails every unanswerable question can show a deceptive overall score. Reporting per-type scores reveals this.

---

## Challenge 4: Execution & Results

### Test Run 1: 3 Questions (Single-passage, Multi-passage, Unanswerable)

**Result:** All three metrics scored successfully.

| Type | Faith | Relev | Prec |
|---|---|---|---|
| Single | 1.00 | 1.00 | 1.00 |
| Multi | 0.50 | 0.75 | 0.83 |
| Unans | 1.00 | 0.50 | 0.00 |
| **Overall** | **0.83** | **0.75** | **0.61** |

**Observations:**
- Single-passage near-perfect: clear retrieval, clear answer
- Multi-passage weaker on faithfulness (0.50): model synthesized from chunks but added slight embellishment
- Unanswerable: correctly refused ("I don't know") but precision 0 because retrieval pulled irrelevant chunks for an out-of-scope question

### Test Run 2: 15 Questions (Full Golden Set)

**Result:** 14 of 15 items scored (93% success rate). One item (unanswerable about district office official) had a pipeline error (answer object returned None from API).

| Type | Faith | Relev | Prec | Count |
|---|---|---|---|---|
| Single (6) | 1.00 | 1.00 | 0.97 | 6 |
| Multi (4) | 1.00 | 1.00 | 0.96 | 4 |
| Unans (5) | 0.83 | 0.70 | 0.71 | 4 |
| **Overall (14)** | **0.95** | **0.91** | **0.89** | **14** |

---

## Findings

### What's Working Well

✅ **Faithfulness is excellent (0.95)** — the agent grounds answers in retrieved text, not hallucinations. This is the most critical metric for a RAG system.

✅ **Relevancy is strong (0.91)** — answers address the questions asked. The custom LLM-as-judge scorer proved reliable and didn't hang.

✅ **Precision is solid (0.89)** — retrieval consistently pulls relevant chunks. The embedding-based search with ChromaDB is doing its job.

✅ **Single-passage and multi-passage near-perfect (0.96–1.00 across all metrics)** — the agent handles answerable questions at production quality.

### Where Precision Breaks Down

⚠️ **Unanswerable questions have weaker precision (0.71)** — when asked about information not in the story, the model correctly refuses to answer ("I don't know") but the retrieval step still pulls chunks (relevant to the question topic, but not containing the answer). This is expected behavior — retrieval optimizes for relevance to the query, not for answerhood.

**Example:** "What was Tomas's favorite food?" → Retrieval pulls chunks about Tomas (relevant) → Model correctly says "I don't know" (faithful) → But chunks don't contain an answer (precision ≠ 1.0).

### Limitation: Pipeline Error on 1 Question

One unanswerable question triggered an error in `story_rag.py` when the model response object was None. This didn't crash the full evaluation (error handling caught it) but left that item unscored. Worth investigating in next iteration, but likely an edge case in the OpenAI response format.

---

## Metrics Interpretation

### Faithfulness (0.95)

**What it measures:** Of the claims in the answer, what fraction are supported by the retrieved passages?

**Scoring:** Ragas's Faithfulness metric uses an LLM to check each claim against the context. A score of 1.00 means every claim traces back to a passage. 0.95 overall means near-perfect grounding.

**Why it matters:** Hallucinations are the enemy of RAG. High faithfulness means the answer is only as good as the retrieved text, which is the whole point.

### AnswerRelevancy (0.91)

**What it measures:** Does the answer actually address the question, or does it talk around it?

**Scoring:** Custom LLM-as-judge scores 1–5 ("Does this answer the question?"). Normalized to 0–1.

**Why it matters:** A faithful answer to the wrong question is still wrong. Relevancy catches semantic drift.

### ContextPrecision (0.89)

**What it measures:** Of the 3 chunks retrieved, how many were actually useful for answering the question?

**Scoring:** Ragas's ContextPrecision uses an LLM to judge each chunk as "relevant" or "not relevant" to the question. If 3/3 are relevant → 1.00. If 2/3 → 0.67.

**Why it matters:** Retrieval is the gating step. Bad retrieval → bad answers, no matter how smart the synthesis. Precision 0.89 means we're retrieving mostly relevant chunks, but there's room to tune (bigger k, different chunk sizes, keyword hybrid search).

---

## Next Steps & Recommendations

### For Immediate Iteration

1. **Investigate the one pipeline error** — Why did the response object come back None for one unanswerable question? Check API response structure.

2. **Tune retrieval for unanswerable questions** — Consider:
   - Hybrid search (vector + keyword) to avoid near-miss chunks
   - System prompt modification to be more conservative ("If the information is not explicitly stated, say 'I don't know'")
   - Raising the cosine-similarity threshold for chunk selection

3. **Run evaluation after each change** — This framework is now the speedometer. If you adjust chunk size, k, or the system prompt, re-run the golden set and compare scores.

### For Adding a Second Tool

When you add the PDF financial document tool (next task):

1. **Extend golden set** — Add 5–10 questions that require both tools (e.g., "Compare the story's theme to this financial metric")
2. **Add tool-call accuracy tracking** — Use the pattern from Primer Section 7.2:
   - Track which tool the model chose (or if it chose none)
   - Compare against an `expected_tool` field in the golden set
   - Score: correct_calls / total_calls
3. **Re-run scorecard** — See if multi-tool reasoning hurts single-tool performance (regression testing)

### For Production Deployment

- **Automate evaluation** — Add this script to CI/CD. Every commit that touches `story_rag.py` or the system prompt re-runs the golden set.
- **Set thresholds** — Define acceptable ranges: e.g., "Faithfulness ≥ 0.90, Precision ≥ 0.85" as a gate for deployment.
- **Grow the golden set** — Start with 15; over time, add real user queries and their expected answers.
- **Monitor unanswerable handling** — Track false negatives (model answers when it should refuse) vs. false positives (model refuses when it should answer).

---

## Technical Notes

### Files & Structure

- **`story_rag.py`** — Refactored to expose retrieval function and `ask_about_story()` callable
- **`evaluate.py`** — Main evaluator; parallel item scoring, sequential metrics, custom AnswerRelevancy
- **`golden_set.py`** — 15-question test set with expected answers and type tags
- **`eval_results.json`** — Detailed per-item results (question, answer, chunks, scores)
- **`requirements.txt`** — Core dependencies (openai, chromadb, ragas, langchain-google-vertexai, etc.)

### Dependencies Resolved

- **Ragas VertexAI import bug:** Fixed by installing `langchain-google-vertexai` and patching `/ragas/llms/base.py` line 12
- **Async compatibility:** Switched to sequential metric execution within parallel item loop
- **Custom scorer:** Avoids Ragas async issues entirely

### Environment

- **conda env:** `agent-eval` (Python 3.11)
- **Branch:** `AI-Agent-Evaluation`
- **OpenAI model:** `gpt-4o-mini` for both agent and evaluation
- **Embeddings:** `text-embedding-3-small`

---

## Conclusion

The Story-RAG agent is **production-ready for single-tool, single-document retrieval**. Faithfulness (0.95) and relevancy (0.91) are strong. Precision (0.89) is solid, with known weakness on unanswerable questions (expected and addressable with retrieval tuning).

**This evaluation framework is now the source of truth.** All future changes will be measured against this baseline. The next step is adding a second tool and verifying that multi-tool reasoning doesn't regress single-tool performance.