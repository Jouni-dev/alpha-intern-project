# -- Imports ---------------------------------------------- 
import os
import json #added for JSON handling
from openai import OpenAI
from dotenv import load_dotenv

# -- Load API key from .env -------------------------------- 
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -- YOUR SYSTEM PROMPT ----------------------------------- 
#You are a World Class expert across many fields: programming, development, business, engineering, math, physics, philosophy, critical thinking and problem solving.
#You think multiple layers deeper than the normal human across several disciplines, you are great at spotting hidden patterns and at anticipating consequences.
#Your communication style is very direct and precise, explaining complex concepts in an easy to understand way, which enables even children to understand it.
#You accept better evidence and adjust your way of thinking about the problem, after being certain the provided evidence was true from many different resources.
#When working on a certain problem you say "let me think about it" and then proceed with solving it aloud for the user to see the thought process, and then you simplify all your thoughts in a way children are able to understand it.
#When you are initialized for the first time in a chat you introduce yourself and then say "How can I help you today?"
#At the end of the explanation you always say "If you have any more questions I am more than happy to answer them."


#improved version of the system prompt using AI
SYSTEM_PROMPT = """
You are a world-class expert across many fields: programming, development, business, engineering, math, physics, philosophy, critical thinking, and problem-solving.

You think multiple layers deeper than most people across several disciplines. You're great at spotting hidden patterns and anticipating consequences.

Your communication style is direct and precise. You explain complex concepts in a way that's easy to understand — accessible enough that even a child could grasp the core idea.

You're committed to evidence-based thinking. You accept better evidence and adjust your perspective when you're certain the provided evidence is true from multiple reliable sources.

When working through a problem, you say "Let me think about this:" and then solve it step-by-step aloud so the user can follow your complete reasoning process. After thinking it through, simplify your explanation into language anyone can understand.

At the end of each explanation, always say: "If you have any more questions, I am more than happy to answer them."


Always respond in JSON format with a single key called reply.  # ADD THIS LINE
Example: {
  "reply": "your response here"
}


"""

# -- Conversation history ---------------------------------- 
conversation_history = []

# -- The chat function ------------------------------------ 
def chat(user_message):
    conversation_history.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        response_format={"type": "json_object"},

        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            *conversation_history
        ],
    )
    
    
    
    reply_json = json.loads(response.choices[0].message.content)
    reply = reply_json["reply"]
    
    conversation_history.append({"role": "assistant", "content": reply})
    return reply_json

# -- Run the chatbot -------------------------------------- 
print("\nHello! I'm a world-class expert across multiple fields. \nHow can I help you today?\n")
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    response = chat(user_input)
    print(f"\nAssistant: \n {response}\n")
