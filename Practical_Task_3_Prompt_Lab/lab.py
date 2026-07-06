# -- Imports ---------------------------------------------- 
import os
import json #added for JSON handling
from openai import OpenAI
from dotenv import load_dotenv

# -- Load API key from .env -------------------------------- 
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -- YOUR SYSTEM PROMPT ----------------------------------- 
#prompt generated using ai
SYSTEM_PROMPT = """


Always respond in JSON format with a single key called reply.
Example: { "reply": "your response here" }

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
