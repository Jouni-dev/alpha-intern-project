from openai import OpenAI
import json
from dotenv import load_dotenv

load_dotenv()

travel_schema = {
    "type": "object",
    "properties": {
        "destination": {
            "type": "string",
            "description": "The travel destination chosen by the user"
        },
        "number_of_days": {
            "type": "integer",
            "description": "Number of days for the trip (how long the trip will last)"
        },
        "daily_activities": {
            "type": "array",
            "description": "Day-by-day travel activities throughout the trip",
            "items": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "integer",
                        "description": "The day number"
                    },
                    "activities": {
                        "type": "array",
                        "description": "Activities planned for that day",
                        "items": {
                            "type": "string"
                        }
                    }
                },
                "required": ["day", "activities"],
                "additionalProperties": False
            }
        },
        "estimated_budget": {
            "type": "number",
            "description": "Estimated total cost of the trip"
        },
        "travel_tips": {
            "type": "array",
            "description": "Useful tips for the traveler",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "destination",
        "number_of_days",
        "daily_activities",
        "estimated_budget",
        "travel_tips"
    ],
    "additionalProperties": False
}

client = OpenAI()


def get_user_input():
    destination = input("Enter destination: ").strip()
    days = int(input("Enter number of days: "))
    return destination, days


def create_prompt(destination, days):
    prompt = f"""
    Create a travel itinerary for {destination} for {days} days.
    
    Return only the JSON structure requested.
    """
    return prompt


def call_openai(prompt, temperature=0.7, max_tokens=700):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "travel_itinerary",
                "schema": travel_schema,
                "strict": True
            }
        },
        messages=[
            {"role": "system", "content": "You are a travel planner that creates structured JSON itineraries."},
            {"role": "user", "content": prompt}
        ]
    )
    return response


def print_itinerary(itinerary, response):
    print("\n--- Travel Itinerary ---")
    print(f"Destination: {itinerary['destination']}")
    print(f"Days: {itinerary['number_of_days']}")

    print("\nDay-by-Day Activities:")
    for day in itinerary["daily_activities"]:
        print(f"  Day {day['day']}:")
        for activity in day["activities"]:
            print(f"    - {activity}")

    print(f"\nEstimated Budget: ${itinerary['estimated_budget']}")

    print("\nTravel Tips:")
    for tip in itinerary["travel_tips"]:
        print(f"  - {tip}")

    print(f"\nFinish Reason: {response.choices[0].finish_reason}")


def main():
    destination, days = get_user_input()
    prompt = create_prompt(destination, days)

    print("\nGenerating your travel itinerary...\n")

    response = call_openai(prompt)

    raw_json = response.choices[0].message.content
    itinerary = json.loads(raw_json)

    print_itinerary(itinerary, response)


if __name__ == "__main__":
    main()