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
def chat(user_message, temperature=0.7, max_tokens=1024):
    
    conversation_history.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=max_tokens,
        temperature=temperature,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *conversation_history
        ],
    )
    
    reply_json = json.loads(response.choices[0].message.content)
    reply = reply_json["reply"]
    
    conversation_history.append({"role": "assistant", "content": reply})
    return reply, temperature

# -- Run the chatbot -------------------------------------- 
print("\nHello! I'm a world-class expert across multiple fields. \nHow can I help you today?\n")
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    
    reply, temp_used = chat(user_input, temperature=1.5)
    
    print(f"\n[temperature={temp_used}]")
    print(f"Assistant: {reply}\n")