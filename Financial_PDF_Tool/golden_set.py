"""
Extended Golden Set for Multi-Tool Evaluation

Contains:
- Story-only questions (expect search_story)
- Financial-only questions (expect search_financial)
- Mixed/ambiguous questions (tests judgment)
- Trick questions (should refuse or use no tool)
"""

golden_set_extended = [
    # === STORY-ONLY QUESTIONS (6) ===
    {
        "question": "Who pulled Tomas out of the water?",
        "expected": "Elena Voss pulled Tomas out of the water and brought him inside the lighthouse.",
        "type": "story-single",
        "expected_tools": ["search_story"]
    },
    {
        "question": "How long had Elena been keeping the lighthouse at Merrow Point?",
        "expected": "Elena had kept the light at Merrow Point for six years.",
        "type": "story-single",
        "expected_tools": ["search_story"]
    },
    {
        "question": "What was Tomas's father's name?",
        "expected": "Tomas's father's name was Mattias Holt.",
        "type": "story-single",
        "expected_tools": ["search_story"]
    },
    {
        "question": "What ship was Tomas on when he wrecked?",
        "expected": "Tomas was on a fishing boat called the Kestrel Anne.",
        "type": "story-single",
        "expected_tools": ["search_story"]
    },
    {
        "question": "How is the compass connected to both Tomas and Elena's family?",
        "expected": "The compass originally belonged to Elena's grandfather Henrik. He gave it to Mattias Holt (Tomas's father) when he rowed him to the mainland in 1975.",
        "type": "story-multi",
        "expected_tools": ["search_story"]
    },
    {
        "question": "When did Elena's grandfather Henrik vanish?",
        "expected": "Henrik vanished during a routine supply run in the autumn of 1975.",
        "type": "story-single",
        "expected_tools": ["search_story"]
    },
    
    # === FINANCIAL-ONLY QUESTIONS (6) ===
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
        "question": "What report types are included in this financial document?",
        "expected": "Actual vs Plan, Year-over-Year Comparison, and Balance Sheet",
        "type": "financial-multi",
        "expected_tools": ["search_financial"]
    },
    {
        "question": "What was the Change % for Unrestricted Public Support in Actual vs Plan?",
        "expected": "28.34%",
        "type": "financial-single",
        "expected_tools": ["search_financial"]
    },
    
    # === MIXED/AMBIGUOUS QUESTIONS ===
    {
        "question": "Did the story mention anything about Wikimedia Foundation?",
        "expected": "No, the story is about a lighthouse and does not mention Wikimedia Foundation.",
        "type": "mixed-should-refuse",
        "expected_tools": ["search_story"]  # Tries story, finds nothing
    },
    {
        "question": "Compare the narrative structure of the lighthouse story to financial documentation.",
        "expected": "The story is a narrative about characters and emotions; the financial document is structured data with accounts and numbers.",
        "type": "mixed-conceptual",
        "expected_tools": ["search_story", "search_financial"]  # Might need both
    },
    
    # === TRICK QUESTIONS (should refuse) ===
    {
        "question": "What is the answer to life, the universe, and everything?",
        "expected": "I cannot answer this question from the available documents.",
        "type": "trick-unanswerable",
        "expected_tools": []  # Should not call any tool
    },
    {
        "question": "How much did the lighthouse keeper earn?",
        "expected": "The story does not mention Elena's salary or earnings.",
        "type": "trick-unanswerable",
        "expected_tools": ["search_story"]  # Tries story, finds it's not there
    },
]
