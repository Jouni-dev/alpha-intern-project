"""
Extended Golden Set for Multi-Source, Multi-Tool Evaluation

Contains:
- Anthropic-doc-only questions (expect search_anthropic_info)
- Financial-only questions (expect search_financial)
- Mixed/ambiguous questions (tests judgment)
- Validation questions (expect search_anthropic_info -> web_search, the new
  capability in this task - checking a document claim against live sources)
- Trick questions (should refuse or use no tool)
"""

golden_set_extended = [
    # === ANTHROPIC-DOC-ONLY QUESTIONS (5) ===
    {
        "question": "Who founded Anthropic and when?",
        "expected": "Anthropic was founded in 2021 by former OpenAI employees including Dario Amodei (CEO) and Daniela Amodei (President).",
        "type": "anthropic-single",
        "expected_tools": ["search_anthropic_info"]
    },
    {
        "question": "What is Constitutional AI?",
        "expected": "A technique for training models to be helpful and harmless using a written set of principles (a constitution) instead of relying purely on large volumes of human feedback labeling.",
        "type": "anthropic-single",
        "expected_tools": ["search_anthropic_info"]
    },
    {
        "question": "What is Anthropic's Responsible Scaling Policy?",
        "expected": "A framework, published in 2023, that ties increasingly capable models to increasingly stringent safety and security requirements, using a series of AI Safety Levels (ASL) modeled on biosafety levels.",
        "type": "anthropic-single",
        "expected_tools": ["search_anthropic_info"]
    },
    {
        "question": "What is scalable oversight?",
        "expected": "Techniques for supervising AI systems that may eventually be more capable than the humans supervising them, including debate-style setups and weak-to-strong generalization experiments.",
        "type": "anthropic-single",
        "expected_tools": ["search_anthropic_info"]
    },
    {
        "question": "What is the Model Context Protocol and when was it released?",
        "expected": "An open standard released by Anthropic in late 2024 that defines a standard client-server interface so AI models can connect to external tools and data sources without custom integration work each time.",
        "type": "anthropic-single",
        "expected_tools": ["search_anthropic_info"]
    },

    # === FINANCIAL-ONLY QUESTIONS (5) ===
    {
        "question": "What was the Unrestricted Public Support amount in the Actual vs Plan report for Jul-Dec 08?",
        "expected": "$4,828,861",
        "type": "financial-single",
        "expected_tools": ["search_financial"]
    },
    {
        "question": "What is the Balance Sheet total for checking/savings as of Dec 31, 08?",
        "expected": "$6,677,717.40",
        "type": "financial-single",
        "expected_tools": ["search_financial"]
    },
    {
        "question": "What was the year-over-year change in Unrestricted Public Support?",
        "expected": "$2,492,058.28 increase (106.64% change)",
        "type": "financial-multi",
        "expected_tools": ["search_financial"]
    },
    {
        "question": "How much did Accounts/Contributions Receivable increase from Dec 31, 07 to Dec 31, 08?",
        "expected": "$980,231.05",
        "type": "financial-single",
        "expected_tools": ["search_financial"]
    },
    {
        "question": "What was the Change % for Unrestricted Public Support in Actual vs Plan?",
        "expected": "28.34%",
        "type": "financial-single",
        "expected_tools": ["search_financial"]
    },

    # === MIXED/AMBIGUOUS QUESTIONS (2) ===
    {
        "question": "Does the Anthropic document mention anything about Wikimedia Foundation's finances?",
        "expected": "No, the Anthropic document is about the company Anthropic and does not mention Wikimedia Foundation or its finances.",
        "type": "mixed-should-refuse",
        "expected_tools": ["search_anthropic_info"]
    },
    {
        "question": "Compare Anthropic's approach to AI safety with the structure of the financial report in this project.",
        "expected": "Anthropic's safety approach (Constitutional AI, interpretability, RSP) is company research policy; the financial report is structured numeric data (accounts, amounts, comparisons) about an unrelated organization (Wikimedia Foundation).",
        "type": "mixed-conceptual",
        "expected_tools": ["search_anthropic_info", "search_financial"]
    },

    # === VALIDATION QUESTIONS - require web_search (2) ===
    {
        "question": "Is Claude 3.7 Sonnet still Anthropic's latest model, or has that changed?",
        "expected": "No - the document is a snapshot from early 2025; newer models have since superseded Claude 3.7 Sonnet. This should be confirmed with a live web search.",
        "type": "anthropic-validation",
        "expected_tools": ["search_anthropic_info", "web_search"]
    },
    {
        "question": "Are Google and Amazon still major investors in Anthropic, or has that changed since this document was written?",
        "expected": "The document states Google and Amazon are major investors; this claim should be checked against current sources since investor relationships can change.",
        "type": "anthropic-validation",
        "expected_tools": ["search_anthropic_info", "web_search"]
    },

    # === TRICK QUESTIONS (should refuse) (2) ===
    {
        "question": "What is the answer to life, the universe, and everything?",
        "expected": "I cannot answer this question from the available documents.",
        "type": "trick-unanswerable",
        "expected_tools": []
    },
    {
        "question": "How much did Anthropic's CEO get paid in 2008?",
        "expected": "This cannot be answered - Anthropic was not founded until 2021, and the financial document is a 2008 report for an unrelated organization (Wikimedia Foundation), not Anthropic.",
        "type": "trick-unanswerable",
        "expected_tools": []
    },
]
