import os
import requests
from dotenv import load_dotenv

load_dotenv()

import json
from openai import OpenAI


# ── System Prompt ───────────────────────────────────────────
SYSTEM_PROMPT = """You are a helpful, friendly weather assistant. Your purpose is to provide accurate weather information for any location in the world.

You have access to a real-time weather tool that returns: temperature, feels_like, humidity, pressure, wind_speed, and description.

IMPORTANT: Answer ONLY what the user asks for. Do not volunteer extra information they didn't request.

When you respond, always format your answer as JSON with an "answer" field containing the weather info and a "friendly_message" field with a brief friendly closing."""


# ── Response Format Schema ───────────────────────────────────
RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "weather_response",
        "description": "Structured weather response with answer and friendly message",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The weather information the user asked for"
                },
                "friendly_message": {
                    "type": "string",
                    "description": "A friendly closing message"
                }
            },
            "required": ["answer", "friendly_message"],
            "additionalProperties": False
        }
    }
}


def get_weather(city: str, unit: str = "celsius") -> dict:
    """Call the real OpenWeatherMap API to get current weather with full details."""
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        # Extract all weather information from the API response
        temp_celsius = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        pressure = data["main"]["pressure"]
        wind_speed = data["wind"]["speed"]
        description = data["weather"][0]["description"]
        
        # Convert to Fahrenheit if requested
        if unit == "fahrenheit":
            temp = temp_celsius * 9 / 5 + 32
            feels_like = feels_like * 9 / 5 + 32
        else:
            temp = temp_celsius
        
        return {
            "city": city,
            "temperature": round(temp, 1),
            "feels_like": round(feels_like, 1),
            "humidity": humidity,
            "pressure": pressure,
            "wind_speed": wind_speed,
            "description": description,
            "unit": unit
        }
    
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
        "description": "Get the current weather for a given city including temperature, humidity, wind speed, and conditions.",
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


# ── Input Validation: Classify if question is weather-related ────
def classify_input(user_message: str) -> bool:
    """
    Use the model to determine if the user's input is weather-related.
    Returns True if weather-related, False otherwise.
    """
    classification_prompt = f"""Determine if the following user message is asking about weather or weather-related information.
Answer with only "YES" or "NO".

Examples of weather questions:
- "What's the weather in Paris?"
- "What about humidity in Dubai?"
- "What other weather information do you have?"
- "Tell me about the wind speed"

Examples of non-weather questions:
- "Tell me a joke"
- "What is 2+2?"
- "Who is the president?"

User message: "{user_message}"

Is this a weather-related question? Answer only YES or NO."""
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": classification_prompt}],
            max_tokens=10,
        )
        
        answer = response.choices[0].message.content.strip().upper()
        return "YES" in answer
    
    except Exception as e:
        print(f"[Classification error: {e}]")
        return True


# ── Output Validation: Check if response is about weather ────
def is_weather_answer(response_text: str) -> bool:
    """
    Check if the model's response is actually about weather.
    Looks for weather-related keywords.
    """
    weather_keywords = [
        "temperature", "weather", "celsius", "fahrenheit", "degree",
        "forecast", "rain", "sunny", "cloudy", "wind", "humidity",
        "condition", "°c", "°f", "degrees", "temp", "pressure",
        "precipitation", "clear", "overcast", "storm", "snow", "hot", "cold",
        "feels like", "speed", "description"
    ]
    
    response_lower = response_text.lower()
    
    # Check if response contains at least one weather keyword
    for keyword in weather_keywords:
        if keyword in response_lower:
            return True
    
    return False


# ── Redirect Message for Non-Weather Questions ──────────────
REDIRECT_MESSAGE = "Unfortunately, I can't answer that question since I'm made to be a weather assistant. Feel free to ask me anything you want to know about the weather though!"


# ── Function to handle tool calling ─────────────────────────
def chat(user_message: str):
    """Send a message and handle tool calls if needed."""
    conversation_history.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
        tools=tools,
    )
    
    msg = response.choices[0].message
    
    if msg.tool_calls:
        conversation_history.append(msg)
        
        for call in msg.tool_calls:
            args = json.loads(call.function.arguments)
            result = get_weather(**args)
            
            conversation_history.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result),
            })
        
        # Call API again with tool result AND response format
        final = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history,
            tools=tools,
            response_format=RESPONSE_FORMAT,
        )
        
        reply_text = final.choices[0].message.content
        
        try:
            reply_json = json.loads(reply_text)
            full_response = reply_json
        except json.JSONDecodeError:
            full_response = {"answer": reply_text, "friendly_message": ""}
        
        conversation_history.append({"role": "assistant", "content": reply_text})
        return full_response
    
    else:
        # No tool call, just return the reply (shouldn't happen in normal flow)
        reply_text = msg.content
        
        try:
            reply_json = json.loads(reply_text)
            full_response = reply_json
        except json.JSONDecodeError:
            full_response = {"answer": reply_text, "friendly_message": ""}
        
        conversation_history.append({"role": "assistant", "content": reply_text})
        return full_response


# ── Main chatbot loop with guardrails ───────────────────────
print("\nYour weather assistant is ready. Type quit to exit.\n")
while True:
    user_input = input("You: ")
    if user_input.lower() == "quit":
        break
    
    # INPUT VALIDATION: Check if question is weather-related
    if not classify_input(user_input):
        # Return redirect message in JSON format
        redirect_json = {
            "answer": REDIRECT_MESSAGE,
            "friendly_message": ""
        }
        print(f"\nAssistant: {json.dumps(redirect_json)}\n")
        continue
    
    # Process weather-related question
    response = chat(user_message=user_input)
    
    # OUTPUT VALIDATION: Check if response is actually about weather
    answer = response.get("answer", "") if isinstance(response, dict) else str(response)
    
    if not is_weather_answer(answer):
        # Return redirect message in JSON format
        redirect_json = {
            "answer": REDIRECT_MESSAGE,
            "friendly_message": ""
        }
        print(f"\nAssistant: {json.dumps(redirect_json)}\n")
    else:
        if isinstance(response, dict):
            print(f"\nAssistant: {json.dumps(response)}\n")
        else:
            print(f"\nAssistant: {response}\n")