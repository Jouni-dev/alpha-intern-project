# -- Imports ---------------------------------------------- 
import os
import json #added for JSON handling
from openai import OpenAI
from dotenv import load_dotenv

# -- Load API key from .env -------------------------------- 
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -- YOUR SYSTEM PROMPT ----------------------------------- 
SYSTEM_PROMPT = """
You are a world-class expert across many fields: programming, development, business, engineering, math, physics, philosophy, critical thinking, and problem-solving.

You think multiple layers deeper than most people across several disciplines. You're great at spotting hidden patterns and anticipating consequences.

Your communication style is direct and precise. You explain complex concepts in a way that's easy to understand — accessible enough that even a child could grasp the core idea.

You're committed to evidence-based thinking. You accept better evidence and adjust your perspective when you're certain the provided evidence is true from multiple reliable sources.

When working through a problem, you say "Let me think about this:" and then solve it step-by-step aloud so the user can follow your complete reasoning process. After thinking it through, simplify your explanation into language anyone can understand.

At the end of each explanation, always say: "If you have any more questions, I am more than happy to answer them."

Always respond in JSON format with a single key called reply.
Example: { "reply": "your response here" }
"""

# -- Conversation history ---------------------------------- 
conversation_history = []

# -- The chat function ------------------------------------ 
def chat(user_message, temperature=0.7, max_tokens=1024, use_examples=False):

    # For Challenge 4: Add examples to teach the format
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
    ]

    # If use_examples=True, add few-shot examples BEFORE the user's actual question
    if use_examples:
        # These are example exchanges showing the format
        messages.extend([
            {"role": "user", "content": "apple"},
            {"role": "assistant", "content": "apple  ::  noun  ::  a round fruit that grows on trees  ::  fruit"},

            {"role": "user", "content": "book"},
            {"role": "assistant", "content": "book  ::  noun  ::  a set of written pages bound together  ::  literature"},

            {"role": "user", "content": "run"},
            {"role": "assistant", "content": "run  ::  verb  ::  to move quickly using your legs  ::  movement"},
        ])

    # Add conversation history
    messages.extend(conversation_history)

    # Add the current user message
    conversation_history.append({"role": "user", "content": user_message})
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=messages,
    )

    raw_content = response.choices[0].message.content

    # Try to parse JSON, but handle incomplete JSON gracefully
    try:
        reply_json = json.loads(raw_content)
        reply = reply_json["reply"]
    except json.JSONDecodeError:
        # If JSON is incomplete (truncated), just use the raw content
        reply = raw_content

    conversation_history.append({"role": "assistant", "content": reply})

    return reply

# -- Run the chatbot -------------------------------------- 
print("\nChallenge 4: Few-Shot Prompting\n")
print("Type words and the model will format them as: word :: part_of_speech :: definition :: category\n")

while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break

    # Set use_examples=True to enable few-shot prompting
    # Set use_examples=False to test without examples
    reply = chat(user_input, temperature=0.7, max_tokens=1024, use_examples=True)

    print(f"\nAssistant: {reply}\n")