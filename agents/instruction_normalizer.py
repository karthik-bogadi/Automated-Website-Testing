from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# number words → digits
number_map = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10
}


def convert_number_words(text):

    words = text.lower().split()

    for i, w in enumerate(words):
        if w in number_map:
            words[i] = str(number_map[w])

    return " ".join(words)


def normalize_instruction(instruction: str):

    instruction = convert_number_words(instruction)

    prompt = f"""
    You convert messy natural language testing instructions into clear normalized instructions.

    IMPORTANT RULES:
    1. Do NOT remove important information.
    2. Do NOT invent new actions.
    3. Preserve search text, usernames, passwords, and values.
    4. Only rewrite the instruction to make it clear and structured.

    Normalization rules:

    Loop format:
    Repeat <action> <number> times

    Conditional format:
    If <condition> then <action>

    Examples:

    Input:
    Login three times
    Output:
    Repeat login 3 times

    Input:
    If login fails show error
    Output:
    If login fails then verify error message

    Input:
    Open youtube and search telugu
    Output:
    Open youtube website
    Type telugu in search bar
    Submit search

    Input:
    Open github and look for langgraph repo
    Output:
    Open GitHub website
    Type langgraph repo in search bar
    Submit search

    Instruction:
    {instruction}

    Return only the normalized instruction.
    """

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {"role": "system", "content": "Return only normalized instruction."},
            {"role": "user", "content": prompt}
        ]
    )

    normalized = response.choices[0].message.content.strip()

    return normalized