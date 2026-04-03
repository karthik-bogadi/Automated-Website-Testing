import os
import json
import logging
import re
from typing import List, Optional, Literal
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
from groq import Groq


# --------------------------------------------------
# Setup
# --------------------------------------------------
load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in .env")

client = Groq(api_key=api_key)

logging.basicConfig(
    filename="parser.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# --------------------------------------------------
# Schema
# --------------------------------------------------

AllowedAction = Literal[
    "open", "click", "enter", "type", "submit",
    "verify", "scroll", "hover", "wait",
    "navigate", "select", "upload", "download","assert"
]


class Action(BaseModel):
    action: AllowedAction
    target: str
    value: Optional[str] = None


class ConditionBlock(BaseModel):
    condition: str
    steps: List[Action]


class LoopBlock(BaseModel):
    count: int
    steps: List[Action]


class ParsedOutput(BaseModel):
    intent: Literal["simple", "conditional", "loop"]
    steps: Optional[List[Action]] = None
    conditional: Optional[ConditionBlock] = None
    loop: Optional[LoopBlock] = None


# --------------------------------------------------
# LLM Step Generator (ONLY generates steps)
# --------------------------------------------------

def generate_steps_with_llm(instruction: str):

    prompt = f"""
Convert this instruction into a JSON array of steps.

Allowed actions:
open, click, enter, type, submit,
verify, scroll, hover, wait,
navigate, select, upload, download,assert.

Rules:
- If instruction contains words like "check", "verify", "ensure", "confirm"
  → use action = "assert"
- For assertions:
  - target = element name
  - value = expected text (if any)

Each step must contain:
- action
- target
- value (nullable)

Return ONLY JSON array.

Instruction:
{instruction}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        temperature=0,
        messages=[
            {"role": "system", "content": "Return only JSON array. No explanation."},
            {"role": "user", "content": prompt}
        ]
    )

    content = response.choices[0].message.content.strip()

    logging.info(f"Raw LLM output: {content}")

    if not content:
        raise ValueError("LLM returned empty response")

    # 🔥 Extract JSON array safely
    start = content.find("[")
    end = content.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("No JSON array found in LLM response")

    json_str = content[start:end+1]

    steps = json.loads(json_str)

    # Repair missing fields
    for step in steps:

        if "action" not in step:
            step["action"] = "click"

        if "target" not in step or not step["target"]:
            step["target"] = "element"

        if "value" not in step:
            step["value"] = None

    return steps

# --------------------------------------------------
# MAIN PARSER
# --------------------------------------------------

def parse_instruction_llm(instruction: str):

    if not instruction or len(instruction.strip()) < 3:
        return {"error": "Invalid instruction"}

    instruction = instruction.strip()

    try:

        # ----------------------------
        # CONDITIONAL
        # ----------------------------
        if instruction.lower().startswith("if"):

            parts = instruction.split("then")

            if len(parts) != 2:
                return {"error": "Invalid conditional format. Use 'If ... then ...'"}

            condition_text = parts[0].replace("If", "").strip()
            action_text = parts[1].strip()

            steps = generate_steps_with_llm(action_text)

            result = {
                "intent": "conditional",
                "conditional": {
                    "condition": condition_text,
                    "steps": steps
                }
            }

            validated = ParsedOutput.model_validate(result)
            return validated.model_dump()

        # ----------------------------
        # LOOP
        # ----------------------------
        loop_match = re.search(r"repeat (.+?) (\d+) times", instruction.lower())

        if loop_match:

            action_text = loop_match.group(1)
            count = int(loop_match.group(2))

            steps = generate_steps_with_llm(action_text)

            result = {
                "intent": "loop",
                "loop": {
                    "count": count,
                    "steps": steps
                }
            }

            validated = ParsedOutput.model_validate(result)
            return validated.model_dump()

        # ----------------------------
        # SIMPLE
        # ----------------------------
        steps = generate_steps_with_llm(instruction)

        result = {
            "intent": "simple",
            "steps": steps
        }

        validated = ParsedOutput.model_validate(result)
        return validated.model_dump()

    except ValidationError as e:
        return {
            "error": "Schema validation failed",
            "details": str(e)
        }

    except Exception as e:
        return {
            "error": str(e)
        }