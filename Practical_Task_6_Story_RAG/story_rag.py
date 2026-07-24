import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

with open("story.txt", "r") as f:
    story = f.read()


system_prompt = f"""You are a helpful assistant. You have been given a story to read and analyze.

Here is the story:

{story}

Answer questions about this story based only on what is written in the text above."""


def ask_about_story(question):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=256,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content


while True:
    question = input("\nAsk a question about the story (or 'quit' to exit): ")
    if question.lower() == "quit":
        break
    answer = ask_about_story(question)
    print(f"\nAnswer: {answer}\n")