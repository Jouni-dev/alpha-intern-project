import os

import requests
from dotenv import load_dotenv

load_dotenv()

import json

from openai import OpenAI


def get_weather(city: str, unit: str = "celsius") -> dict:
    """Call the real OpenWeatherMap API to get current weather."""
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # Raise error if status code is not 200
        data = response.json()
        
        # Extract temperature from the API response
        temp_celsius = data["main"]["temp"]  # Already in Celsius because we added &units=metric
        
        # Convert to Fahrenheit if requested
        if unit == "fahrenheit":
            temp = temp_celsius * 9 / 5 + 32
        else:
            temp = temp_celsius
        
        return {"city": city, "temperature": temp, "unit": unit}
    
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return {"error": f"City '{city}' not found", "city": city}
        else:
            return {"error": f"API error: {response.status_code}", "city": city}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to connect to weather API: {str(e)}", "city": city}
    
    except (KeyError, ValueError) as e:
        return {"error": f"Invalid API response format", "city": city}


tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a given city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name, e.g. Cairo"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["city"]
        }
    }
}]

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ── Conversation history ────────────────────────────────────
conversation_history = []

# ── Function to handle tool calling ─────────────────────────
def chat(user_message: str):
    """Send a message and handle tool calls if needed."""
    conversation_history.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        tools=tools,
    )
    
    msg = response.choices[0].message
    
    # If the model wants a tool run, msg.tool_calls is populated instead of msg.content:
    # tool_calls[0].function.name == "get_weather"
    # tool_calls[0].function.arguments == '{"city": "Cairo"}'   (a JSON string)
    
    if msg.tool_calls:
        conversation_history.append(msg)  # keep the assistant's tool-call turn in history
        
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = get_weather(**args)          # actually run it
            
            conversation_history.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })
        
        # Call API again with tool result
        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation_history,
            tools=tools,
        )
        
        reply = final.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": reply})
        return reply
    
    else:
        # No tool call, just return the reply
        reply = msg.content
        conversation_history.append({"role": "assistant", "content": reply})
        return reply

# ── Main chatbot loop ───────────────────────────────────────
print("\nYour assistant is ready. Type quit to exit.\n")
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    response = chat(user_input)
    print(f"\nAssistant: {response}\n")