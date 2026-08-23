from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError, BadRequestError
import json
from dotenv import load_dotenv
import time

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
    while True:
        destination = input("Enter destination: ").strip()
        
        if not destination:
            print("Destination cannot be empty. Please try again.")
            continue
        
        if destination.isdigit():
            print("Destination cannot be only numbers. Please try again.")
            continue
        
        if len(destination) < 2:
            print("Destination must be at least 2 characters. Please try again.")
            continue
        
        break

    while True:
        try:
            days_input = input("Enter number of days: ").strip()
            days = int(days_input)
            
            if days < 1:
                print("Number of days must be at least 1.")
                continue
            
            if days > 21:
                print("Number of days must be between 1 and 21.")
                continue
            
            break
        except ValueError:
            print("Please enter a valid number for days.")
            continue

    return destination, days


def validate_itinerary(data):
    if not isinstance(data, dict):
        raise ValueError("Invalid response: Expected a JSON object (dictionary).")

    required_fields = ["destination", "number_of_days", "daily_activities", "estimated_budget", "travel_tips"]
    
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: '{field}'")

    if not isinstance(data["destination"], str):
        raise ValueError("Invalid type: 'destination' should be a string.")
    
    if not isinstance(data["number_of_days"], int):
        raise ValueError("Invalid type: 'number_of_days' should be an integer.")
    
    if not isinstance(data["daily_activities"], list):
        raise ValueError("Invalid type: 'daily_activities' should be a list.")
    
    if len(data["daily_activities"]) == 0:
        raise ValueError("'daily_activities' list cannot be empty.")
    
    for day in data["daily_activities"]:
        if not isinstance(day, dict):
            raise ValueError("Each daily activity should be an object (dictionary).")
        if "day" not in day or "activities" not in day:
            raise ValueError("Each day object must have 'day' and 'activities' fields.")
        if not isinstance(day["activities"], list):
            raise ValueError("'activities' within each day must be a list.")

    if not isinstance(data["travel_tips"], list):
        raise ValueError("Invalid type: 'travel_tips' should be a list.")
    
    if len(data["travel_tips"]) == 0:
        raise ValueError("'travel_tips' list cannot be empty.")
    
    for tip in data["travel_tips"]:
        if not isinstance(tip, str):
            raise ValueError("Each travel tip should be a string.")

    budget = data["estimated_budget"]
    if not isinstance(budget, (int, float)):
        raise ValueError("'estimated_budget' should be a number.")

    return True


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

    max_retries = 3
    response = None

    for attempt in range(max_retries):
        try:
            response = call_openai(prompt)
            break

        except AuthenticationError:
            print("Authentication Error: Your OpenAI API key is invalid or expired.")
            print("Please check your .env file and ensure OPENAI_API_KEY is correct.")
            return

        except RateLimitError:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 2
                print(f"Rate limit hit. Waiting {wait_time} seconds before retry ({attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            else:
                print("Rate limit exceeded after multiple retries. Please try again later.")
                return

        except APIConnectionError:
            if attempt < max_retries - 1:
                print(f"Connection error. Retrying ({attempt + 1}/{max_retries})...")
                time.sleep(1)
            else:
                print("Could not connect to OpenAI. Check your internet connection.")
                return

        except BadRequestError as e:
            print(f"Bad Request Error: {str(e)}")
            print("The request sent to OpenAI was invalid.")
            return

        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return

    if response is None:
        print("Failed to get a response from the API.")
        return

    try:
        raw_json = response.choices[0].message.content
        itinerary = json.loads(raw_json)
    except json.JSONDecodeError:
        print("The response was incomplete or invalid JSON.")
        print("Finish reason:", response.choices[0].finish_reason)
        return

    try:
        validate_itinerary(itinerary)
    except ValueError as e:
        print(f"Validation failed: {e}")
        return

    print_itinerary(itinerary, response)


# ============ TEST SECTION ============
# Uncomment below to test validate_itinerary() with a broken test case

# def test_broken_itinerary():
#     bad_test = {
#         ...
#     }
#
#     try:
#         validate_itinerary(bad_test)
#         print("ERROR: Validation should have failed!")
#     except ValueError as e:
#         print(f"Correctly caught validation error: {e}")
#
# test_broken_itinerary() 


if __name__ == "__main__":
    main()