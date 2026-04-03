from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def detect_intent(instruction: str):

    prompt = f"""
Classify the following instruction into one of these intents:

simple
conditional
loop
complex

Instruction:
{instruction}

Return only the intent word.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {"role": "system", "content": "Return only the intent word."},
            {"role": "user", "content": prompt}
        ]
    )

    intent = response.choices[0].message.content.strip().lower()

    if intent not in ["simple", "conditional", "loop", "complex"]:
        intent = "simple"

    return intent