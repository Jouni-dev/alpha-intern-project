import os
import json
import asyncio
import statistics
from dotenv import load_dotenv
from openai import AsyncOpenAI
from ragas.llms import llm_factory
from ragas.embeddings.base import embedding_factory
from ragas.metrics.collections import Faithfulness, AnswerRelevancy, ContextPrecision

print("[evaluate] Loading environment variables...")
load_dotenv()

print("[evaluate] Importing pipeline and golden set...")
from story_rag import ask_about_story, retrieve_chunks_from_chroma, collection
from golden_set import golden_set

print(f"[evaluate] Golden set loaded: {len(golden_set)} questions")
print("[evaluate] Golden set breakdown:")
types = {}
for item in golden_set:
    qtype = item["type"]
    types[qtype] = types.get(qtype, 0) + 1
for qtype, count in sorted(types.items()):
    print(f"  - {qtype}: {count}")

print("\n[evaluate] Initializing async OpenAI client...")
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
print("[evaluate] AsyncOpenAI client initialized")

# Initialize Ragas metrics with OpenAI models
print("\n[evaluate] Initializing Ragas metrics...")
print("[evaluate] Creating LLM factory for gpt-4o-mini...")
llm = llm_factory("gpt-4o-mini", client=client)
print("[evaluate] ✓ LLM factory created")

print("[evaluate] Creating embeddings factory for text-embedding-3-small...")
embeddings = embedding_factory("openai", model="text-embedding-3-small", client=client)
print("[evaluate] ✓ Embeddings factory created")

print("[evaluate] Instantiating Faithfulness metric...")
faithfulness = Faithfulness(llm=llm)
print("[evaluate] ✓ Faithfulness metric ready")

print("[evaluate] Instantiating AnswerRelevancy metric...")
relevancy = AnswerRelevancy(llm=llm, embeddings=embeddings)
print("[evaluate] ✓ AnswerRelevancy metric ready")

print("[evaluate] Instantiating ContextPrecision metric...")
precision = ContextPrecision(llm=llm)
print("[evaluate] ✓ ContextPrecision metric ready")

print("\n[evaluate] ✓✓✓ All Ragas metrics initialized. Ready to evaluate.\n")


async def score_item(item_idx, item):
    """
    Run one golden set item through the pipeline and score with Ragas.
    
    Args:
        item_idx: index of this item in the golden set
        item: dict with question, expected, type
    
    Returns:
        dict with all scores and metadata
    """
    print(f"\n[score_item {item_idx}] ========== SCORING ITEM {item_idx+1} ==========")
    print(f"[score_item {item_idx}] Type: {item['type']}")
    print(f"[score_item {item_idx}] Question: {item['question'][:70]}...")
    
    # Run the question through the pipeline
    print(f"[score_item {item_idx}] Running through pipeline (ask_about_story)...")
    try:
        result = ask_about_story(item["question"])
        answer = result["answer"]
        retrieved_chunks = result["retrieved_chunks"]
        print(f"[score_item {item_idx}] ✓ Pipeline execution complete")
        print(f"[score_item {item_idx}] Answer length: {len(answer)} chars")
        print(f"[score_item {item_idx}] Retrieved chunks: {len(retrieved_chunks)}")
    except Exception as e:
        print(f"[score_item {item_idx}] ✗ ERROR in pipeline: {e}")
        return {
            "question": item["question"],
            "expected": item["expected"],
            "type": item["type"],
            "answer": None,
            "retrieved_chunks": [],
            "faithfulness": None,
            "relevancy": None,
            "precision": None,
            "error": str(e)
        }
    
    # Score with Ragas metrics
    print(f"[score_item {item_idx}] Starting Ragas scoring...")
    
    faith_score = None
    try:
        print(f"[score_item {item_idx}] Scoring: Faithfulness...")
        faith_score = (
            await faithfulness.ascore(
                user_input=item["question"],
                response=answer,
                retrieved_contexts=retrieved_chunks
            )
        ).value
        print(f"[score_item {item_idx}] ✓ Faithfulness score: {faith_score:.2f}")
    except Exception as e:
        print(f"[score_item {item_idx}] ✗ Faithfulness error: {e}")
    
    relevance_score = None
    try:
        print(f"[score_item {item_idx}] Scoring: AnswerRelevancy...")
        relevance_score = (
            await relevancy.ascore(
                user_input=item["question"],
                response=answer
            )
        ).value
        print(f"[score_item {item_idx}] ✓ AnswerRelevancy score: {relevance_score:.2f}")
    except Exception as e:
        print(f"[score_item {item_idx}] ✗ AnswerRelevancy error: {e}")
    
    precision_score = None
    try:
        print(f"[score_item {item_idx}] Scoring: ContextPrecision...")
        precision_score = (
            await precision.ascore(
                user_input=item["question"],
                reference=item["expected"],
                retrieved_contexts=retrieved_chunks
            )
        ).value
        print(f"[score_item {item_idx}] ✓ ContextPrecision score: {precision_score:.2f}")
    except Exception as e:
        print(f"[score_item {item_idx}] ✗ ContextPrecision error: {e}")
    
    print(f"[score_item {item_idx}] ========== ITEM {item_idx+1} COMPLETE ==========\n")
    
    return {
        "question": item["question"],
        "expected": item["expected"],
        "type": item["type"],
        "answer": answer,
        "retrieved_chunks": retrieved_chunks,
        "faithfulness": faith_score,
        "relevancy": relevance_score,
        "precision": precision_score
    }


async def run_evaluation():
    """
    Run all golden set items through evaluation and produce a scorecard.
    """
    print(f"\n[run_evaluation] ========== STARTING EVALUATION ==========")
    print(f"[run_evaluation] Running evaluation on {len(golden_set)} questions...")
    print(f"[run_evaluation] Using asyncio.gather() for parallel scoring\n")
    
    # Score all items
    print("[run_evaluation] Awaiting all scoring tasks...")
    results = await asyncio.gather(
        *(score_item(idx, item) for idx, item in enumerate(golden_set))
    )
    print(f"[run_evaluation] ✓ All {len(results)} items scored\n")
    
    # Aggregate by question type
    print("\n" + "="*80)
    print("EVALUATION SCORECARD")
    print("="*80 + "\n")
    
    for qtype in ["single-passage", "multi-passage", "unanswerable"]:
        type_results = [r for r in results if r["type"] == qtype]
        
        if not type_results:
            print(f"\n{qtype.upper()}")
            print("-" * 40)
            print("No questions of this type")
            continue
        
        print(f"\n{qtype.upper()}")
        print("-" * 40)
        print(f"[aggregate] Processing {qtype}: {len(type_results)} questions")
        
        faithfulness_scores = [r["faithfulness"] for r in type_results if r["faithfulness"] is not None]
        relevancy_scores = [r["relevancy"] for r in type_results if r["relevancy"] is not None]
        precision_scores = [r["precision"] for r in type_results if r["precision"] is not None]
        
        print(f"[aggregate] {qtype}: {len(faithfulness_scores)} faithfulness scores, {len(relevancy_scores)} relevancy, {len(precision_scores)} precision")
        
        if faithfulness_scores:
            mean_faith = statistics.mean(faithfulness_scores)
            print(f"Faithfulness:  {mean_faith:.2f} ({len(faithfulness_scores)} scored)")
        else:
            print(f"Faithfulness:  N/A (no scores)")
        
        if relevancy_scores:
            mean_relev = statistics.mean(relevancy_scores)
            print(f"Relevancy:     {mean_relev:.2f} ({len(relevancy_scores)} scored)")
        else:
            print(f"Relevancy:     N/A (no scores)")
        
        if precision_scores:
            mean_prec = statistics.mean(precision_scores)
            print(f"Precision:     {mean_prec:.2f} ({len(precision_scores)} scored)")
        else:
            print(f"Precision:     N/A (no scores)")
        
        print(f"Questions:     {len(type_results)}")
    
    # Overall stats
    print(f"\n{'='*40}")
    print("OVERALL")
    print("-" * 40)
    all_faith = [r["faithfulness"] for r in results if r["faithfulness"] is not None]
    all_relev = [r["relevancy"] for r in results if r["relevancy"] is not None]
    all_prec = [r["precision"] for r in results if r["precision"] is not None]
    
    print(f"[aggregate] Overall: {len(all_faith)} faithfulness scores, {len(all_relev)} relevancy, {len(all_prec)} precision")
    
    if all_faith:
        overall_faith = statistics.mean(all_faith)
        print(f"Faithfulness:  {overall_faith:.2f}")
    else:
        print(f"Faithfulness:  N/A")
    
    if all_relev:
        overall_relev = statistics.mean(all_relev)
        print(f"Relevancy:     {overall_relev:.2f}")
    else:
        print(f"Relevancy:     N/A")
    
    if all_prec:
        overall_prec = statistics.mean(all_prec)
        print(f"Precision:     {overall_prec:.2f}")
    else:
        print(f"Precision:     N/A")
    
    print(f"Total questions: {len(results)}\n")
    
    # Save detailed results to JSON
    print("[run_evaluation] Saving detailed results to eval_results.json...")
    results_file = "eval_results.json"
    with open(results_file, "w") as f:
        # Convert for JSON serialization (floats are fine, lists of strings are fine)
        json_results = [
            {
                "question": r["question"],
                "expected": r["expected"],
                "type": r["type"],
                "answer": r["answer"],
                "retrieved_chunks": r["retrieved_chunks"],
                "faithfulness": r["faithfulness"],
                "relevancy": r["relevancy"],
                "precision": r["precision"]
            }
            for r in results
        ]
        json.dump(json_results, f, indent=2)
    
    print(f"[run_evaluation] ✓ Detailed results saved to {results_file}\n")
    print(f"[run_evaluation] ========== EVALUATION COMPLETE ==========\n")
    
    return results


if __name__ == "__main__":
    print("[__main__] Entering main entry point")
    results = asyncio.run(run_evaluation())
    print("[__main__] Evaluation run complete")