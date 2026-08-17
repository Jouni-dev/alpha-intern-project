"""
Comprehensive Multi-Tool Agent Evaluator

9 metrics aligned to Evaluating_AI_Agents_Primer
"""

import json
import re
from typing import Dict, List, Any
from openai import OpenAI
from dotenv import load_dotenv
import os

print("[evaluate] Module loaded")

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from story_retriever import retrieve_story_chunks
from agent import ask_with_tools
from financial_retrieval import retrieve_financial_chunks
from golden_set import golden_set_extended


def score_tool_call_accuracy(expected_tools: List[str], actual_tools: List[str]) -> float:
    expected_set = set(expected_tools)
    actual_set = set(actual_tools)
    return 1.0 if expected_set == actual_set else 0.0


def score_faithfulness(answer: str, retrieved_chunks: List[str]) -> float:
    if not retrieved_chunks:
        return 0.0
    
    context = "\n\n".join(retrieved_chunks)
    prompt = f"""Score how grounded this answer is in the provided context.

Context (retrieved chunks):
{context}

Answer to evaluate:
{answer}

Scoring rubric:
1 = Answer makes unsupported claims
2 = Some claims grounded, others not
3 = Most claims grounded, minor issues
4 = Almost all grounded, very minor issues
5 = Every claim directly traceable to context

Respond with ONLY a digit (1-5)."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10
    )
    
    try:
        score = int(response.choices[0].message.content.strip())
        normalized = (score - 1) / 4.0
        print(f"[score_faithfulness] Score: {score}/5 → {normalized:.2f}")
        return normalized
    except:
        return 0.5


def score_answer_relevancy(question: str, answer: str) -> float:
    prompt = f"""Score whether this answer actually addresses the question.

Question: {question}

Answer: {answer}

Scoring rubric:
1 = Completely off-topic
2 = Barely addresses
3 = Partially addresses
4 = Mostly addresses with minor gaps
5 = Directly and fully addresses

Respond with ONLY a digit (1-5)."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=10
    )
    
    try:
        score = int(response.choices[0].message.content.strip())
        normalized = (score - 1) / 4.0
        print(f"[score_answer_relevancy] Score: {score}/5 → {normalized:.2f}")
        return normalized
    except:
        return 0.5


def score_context_precision(question: str, retrieved_chunks: List[str]) -> float:
    if not retrieved_chunks:
        return 0.0
    
    relevant_count = 0
    
    for chunk in retrieved_chunks:
        prompt = f"""Is this chunk relevant to answering the question?

Question: {question}

Chunk: {chunk[:200]}...

Answer with ONLY 'yes' or 'no'."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5
        )
        
        answer = response.choices[0].message.content.strip().lower()
        if "yes" in answer:
            relevant_count += 1
    
    precision = relevant_count / len(retrieved_chunks)
    print(f"[score_context_precision] {relevant_count}/{len(retrieved_chunks)} relevant → {precision:.2f}")
    return precision


def score_context_recall(question: str, retrieved_chunks: List[str], expected_answer: str) -> float:
    context = "\n\n".join(retrieved_chunks)
    prompt = f"""Given these retrieved chunks, can the expected answer be fully derived?

Question: {question}

Retrieved chunks:
{context}

Expected answer:
{expected_answer}

Can the expected answer be fully answered from the retrieved chunks?
Answer with ONLY 'yes' or 'no'."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5
    )
    
    answer = response.choices[0].message.content.strip().lower()
    recall = 1.0 if "yes" in answer else 0.0
    print(f"[score_context_recall] Recall: {recall:.2f}")
    return recall


def extract_dollar_amounts(text: str) -> List[str]:
    pattern = r'\$[\d,]+\.?\d*'
    return re.findall(pattern, text)


def score_exact_match_accuracy(expected: str, answer: str) -> float:
    expected_amounts = extract_dollar_amounts(expected)
    
    if not expected_amounts:
        return 1.0
    
    for amount in expected_amounts:
        if amount in answer:
            print(f"[score_exact_match_accuracy] Found '{amount}' in answer ✓")
            return 1.0
    
    print(f"[score_exact_match_accuracy] Expected amounts {expected_amounts} not found")
    return 0.0


def score_row_column_integrity(question: str, answer: str, retrieved_chunks: List[str]) -> float:
    prompt = f"""Check if this answer correctly associates account names with their values.

Question: {question}

Answer: {answer}

Retrieved context:
{chr(10).join(retrieved_chunks)}

Does the answer pair account names with THEIR SPECIFIC VALUES (not values from different accounts)?
Answer with ONLY 'yes' or 'no'."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=5
    )
    
    answer_text = response.choices[0].message.content.strip().lower()
    integrity = 1.0 if "yes" in answer_text else 0.0
    print(f"[score_row_column_integrity] Integrity: {integrity:.2f}")
    return integrity


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    input_cost = (prompt_tokens / 1_000_000) * 0.15
    output_cost = (completion_tokens / 1_000_000) * 0.60
    return input_cost + output_cost


def run_evaluation():
    print("\n" + "="*80)
    print("STARTING COMPREHENSIVE MULTI-TOOL AGENT EVALUATION")
    print("="*80 + "\n")
    
    results = []
    
    for q_idx, question_data in enumerate(golden_set_extended):
        question = question_data["question"]
        expected = question_data["expected"]
        q_type = question_data["type"]
        expected_tools = question_data["expected_tools"]
        
        print(f"\n[Q{q_idx+1}/{len(golden_set_extended)}] {question[:60]}...")
        print(f"Type: {q_type} | Expected tools: {expected_tools}")
        
        result = ask_with_tools(
            question,
            retrieve_story_chunks,
            retrieve_financial_chunks
        )
        
        answer = result["answer"]
        retrieved_chunks = result["retrieved_chunks"]
        actual_tools = [t["tool"] for t in result["tool_calls"]]
        
        print(f"Answer: {answer[:80]}...")
        print(f"Actual tools called: {actual_tools}")
        
        # COMPUTE ALL 9 METRICS
        
        tool_accuracy = score_tool_call_accuracy(expected_tools, actual_tools)
        print(f"[1] Tool accuracy: {tool_accuracy:.2f}")
        
        faithfulness = score_faithfulness(answer, retrieved_chunks)
        print(f"[2] Faithfulness: {faithfulness:.2f}")
        
        relevancy = score_answer_relevancy(question, answer)
        print(f"[3] Relevancy: {relevancy:.2f}")
        
        context_precision = score_context_precision(question, retrieved_chunks)
        print(f"[4] Context precision: {context_precision:.2f}")
        
        context_recall = score_context_recall(question, retrieved_chunks, expected)
        print(f"[5] Context recall: {context_recall:.2f}")
        
        exact_match = score_exact_match_accuracy(expected, answer)
        print(f"[6] Exact-match accuracy: {exact_match:.2f}")
        
        row_col_integrity = score_row_column_integrity(question, answer, retrieved_chunks)
        print(f"[7] Row-column integrity: {row_col_integrity:.2f}")
        
        prompt_tokens = len(question.split()) * 2 + len(str(retrieved_chunks)) * 2
        completion_tokens = len(answer.split()) * 2
        cost = estimate_cost(prompt_tokens, completion_tokens)
        print(f"[8] Est. tokens: {prompt_tokens} prompt, {completion_tokens} completion | Cost: ${cost:.4f}")
        
        results.append({
            "question_idx": q_idx + 1,
            "question": question,
            "question_type": q_type,
            "expected": expected,
            "answer": answer,
            "expected_tools": expected_tools,
            "actual_tools": actual_tools,
            "retrieved_chunks": retrieved_chunks,
            "metrics": {
                "tool_accuracy": tool_accuracy,
                "faithfulness": faithfulness,
                "answer_relevancy": relevancy,
                "context_precision": context_precision,
                "context_recall": context_recall,
                "exact_match_accuracy": exact_match,
                "row_column_integrity": row_col_integrity,
                "estimated_cost": cost,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
        })
    
    # GENERATE SCORECARD
    
    print("\n" + "="*80)
    print("EVALUATION COMPLETE - SCORECARD")
    print("="*80)
    
    scorecard = {
        "total_questions": len(results),
        "aggregate_metrics": {},
        "by_question_type": {},
        "regression_check": {},
        "results": results
    }
    
    for metric_name in ["tool_accuracy", "faithfulness", "answer_relevancy", "context_precision", "context_recall", "exact_match_accuracy", "row_column_integrity"]:
        scores = [r["metrics"][metric_name] for r in results]
        scorecard["aggregate_metrics"][metric_name] = {
            "mean": sum(scores) / len(scores),
            "min": min(scores),
            "max": max(scores),
            "std": (sum((x - (sum(scores)/len(scores)))**2 for x in scores) / len(scores))**0.5
        }
    
    types = set(r["question_type"] for r in results)
    for q_type in types:
        type_results = [r for r in results if r["question_type"] == q_type]
        type_scores = {}
        for metric_name in ["tool_accuracy", "faithfulness", "answer_relevancy"]:
            scores = [r["metrics"][metric_name] for r in type_results]
            type_scores[metric_name] = sum(scores) / len(scores)
        scorecard["by_question_type"][q_type] = {
            "count": len(type_results),
            "metrics": type_scores
        }
    
    story_results = [r for r in results if "story" in r["question_type"]]
    if story_results:
        story_faithfulness = sum(r["metrics"]["faithfulness"] for r in story_results) / len(story_results)
        scorecard["regression_check"]["story_faithfulness"] = story_faithfulness
        status = "✓ PASS" if story_faithfulness >= 0.95 else "✗ FAIL"
        print(f"\nRegression check (story questions): {story_faithfulness:.3f} {status}")
    
    print("\n[AGGREGATE METRICS]")
    for metric_name, stats in scorecard["aggregate_metrics"].items():
        print(f"  {metric_name}:")
        print(f"    Mean: {stats['mean']:.3f} | Min: {stats['min']:.3f} | Max: {stats['max']:.3f}")
    
    print("\n[BY QUESTION TYPE]")
    for q_type, data in scorecard["by_question_type"].items():
        print(f"  {q_type} ({data['count']} questions):")
        for metric, score in data["metrics"].items():
            print(f"    {metric}: {score:.3f}")
    
    with open("eval_results.json", "w") as f:
        json.dump(scorecard, f, indent=2)
    print("\n✓ Results saved to eval_results.json")
    
    return scorecard


if __name__ == "__main__":
    scorecard = run_evaluation()