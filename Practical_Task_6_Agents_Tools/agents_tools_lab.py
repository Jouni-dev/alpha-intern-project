def get_weather(city: str, unit: str = "celsius") -> dict:
    """Pretend this calls a real weather API."""
    mock_data = {"San Francisco": 18, "Cairo": 34, "London": 15}
    temp = mock_data.get(city, 20)
    if unit == "fahrenheit":
        temp = temp * 9 / 5 + 32
    return {"city": city, "temperature": temp, "unit": unit}


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



import json
from openai import OpenAI
 
client = OpenAI()
messages = [{"role": "user", "content": "What's the weather in Cairo?"}]
 
response = client.chat.completions.create(
    model="gpt-4o",
    messages=messages,
    tools=tools,
)
 
msg = response.choices[0].message
 
# If the model wants a tool run, msg.tool_calls is populated instead of msg.content:
# tool_calls[0].function.name == "get_weather"
# tool_calls[0].function.arguments == '{"city": "Cairo"}'   (a JSON string)
 
if msg.tool_calls:
    messages.append(msg)  # keep the assistant's tool-call turn in history
 
    for call in msg.tool_calls:
        args = json.loads(call.function.arguments)
        result = get_weather(**args)          # actually run it
 
        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": json.dumps(result),
        })
 
    final = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
    )
    print(final.choices[0].message.content)
 
 

