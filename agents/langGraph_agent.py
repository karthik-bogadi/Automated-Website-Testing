from langgraph.graph import StateGraph, END
from typing import TypedDict

from agents.intent_detector import detect_intent
from agents.instruction_normalizer import normalize_instruction
from agents.instruction_parser import parse_instruction_llm
from agents.playwright_executor import run_playwright_test


class AgentState(TypedDict, total=False):
    input: str
    intent: str
    normalized: str
    parsed_output: dict
    execution_result: dict


# -------------------------
# Intent Detection Node
# -------------------------
def intent_node(state):

    instruction = state.get("input", "")

    intent = detect_intent(instruction)

    return {"intent": intent}


# -------------------------
# Instruction Normalization Node
# -------------------------
def normalize_node(state):

    instruction = state.get("input", "")

    normalized = normalize_instruction(instruction)

    return {"normalized": normalized}


# -------------------------
# Parser Node
# -------------------------
def parser_node(state):

    normalized_instruction = state.get("normalized", "")

    parsed = parse_instruction_llm(normalized_instruction)

    return {"parsed_output": parsed}


# -------------------------
# Playwright Execution Node
# -------------------------
def executor_node(state):

    parsed = state.get("parsed_output", {})

    result = run_playwright_test(parsed)

    return {"execution_result": result}


# -------------------------
# Build LangGraph
# -------------------------
builder = StateGraph(AgentState)

builder.add_node("intent", intent_node)
builder.add_node("normalize", normalize_node)
builder.add_node("parser", parser_node)
builder.add_node("executor", executor_node)

builder.set_entry_point("intent")

builder.add_edge("intent", "normalize")
builder.add_edge("normalize", "parser")
builder.add_edge("parser", "executor")
builder.add_edge("executor", END)

graph = builder.compile()