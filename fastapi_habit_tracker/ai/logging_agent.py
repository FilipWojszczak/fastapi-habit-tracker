import textwrap
from typing import Literal, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, StateGraph

from ..config import get_settings
from .schemas import ExtractionStatus, LoggingAgentDecision

settings = get_settings()
llm = ChatOllama(model="llama3", temperature=0, base_url=settings.ollama_base_url)

structured_llm = llm.with_structured_output(LoggingAgentDecision)


class LoggingAgentState(TypedDict):
    user_input: str
    chat_history: list[str]
    available_habits: list[str]
    decision: LoggingAgentDecision | None
    question: str | None
    attempt_count: int


EXTRACTOR_SYSTEM = textwrap.dedent("""
    You are a strict data extraction assistant.
    Your goal is to map user text to a STRICTLY DEFINED list of habits.

    Available habits: {habits_list}

    Rules:
    1. EXACT MATCH: Set status to "match" ONLY if the user explicitly names the habit or uses a specific, unique synonym (e.g., "treadmill" -> "Gym", "jogging" -> "Running").
    2. ALMOST MATCH: If you are not sure about the match but there are clear hints towards one habit, set status to "ambiguous" and ask the user about this specific habit (e.g. "vacuuming" -> "Clean the house").
    3. AMBIGUITY TRAP: Generic verbs like "training", "working out", "exercising", "did sport" MUST be marked as "ambiguous" if multiple physical habits exist (e.g., both "Gym" and "Running"). DO NOT GUESS based on probability.
    4. NO ASSUMPTIONS: Do not invent context. If the chat history does not explicitly clarify the habit, treat it as ambiguous.
    5. REASONING: Always explain why you chose the status in the 'reasoning' field.
    6. Output strictly valid JSON in the format:
    {{
        "status": "match" | "ambiguous" | "no_match",
        "habit_data": {{
            "habit_name": str,  # EXACT string from the list if status is "match", otherwise null
            "value": int or null,  # Numerical value if specified (for example time, quantity etc.), otherwise null
            "note": str or null  # Short note extracted from the text (some additional information that was not used as "habit_name" and "value", it can be feelings about activity), otherwise null
        }} or null,
        "reasoning": str  # Explanation for the decision
    }}
""")  # noqa: E501

QUESTION_SYSTEM = textwrap.dedent("""
    You are a helpful assistant. The user input was ambiguous regarding their habits.

    Context (available habits): {habits_list}
    Ambiguity reason: {reason}

    Generate a SHORT, direct question to clarify which habit the user meant.
    Example: "Did you mean 'Gym' or 'Running'?"
""")


def extractor_node(state: LoggingAgentState):
    habits_str = ", ".join(state["available_habits"])

    full_context = "\n".join(state.get("chat_history", []))
    current_input = f"User currently said: {state['user_input']}"

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", EXTRACTOR_SYSTEM),
            ("human", f"History:\n{full_context}\n\n{current_input}"),
        ]
    )

    chain = prompt | structured_llm
    result: LoggingAgentDecision = chain.invoke({"habits_list": habits_str})

    return {
        "decision": result,
        "attempt_count": state["attempt_count"],
    }


def question_generator_node(state: LoggingAgentState):
    habits_str = ", ".join(state["available_habits"])
    reason = state["decision"].reasoning or "Unclear input"

    prompt = ChatPromptTemplate.from_messages(
        [("system", QUESTION_SYSTEM), ("human", state["user_input"])]
    )

    response = (prompt | llm).invoke({"habits_list": habits_str, "reason": reason})

    return {
        "question": response.content,
        "chat_history": [f"User: {state['user_input']}", f"AI: {response.content}"],
    }


def human_input_node(state: LoggingAgentState):
    return {"attempt_count": state["attempt_count"] + 1}


def check_confidence(
    state: LoggingAgentState,
) -> Literal["success", "question", "fail"]:
    decision = state["decision"]
    attempts = state["attempt_count"]

    if decision.status == ExtractionStatus.MATCH:
        return "success"

    if decision.status == ExtractionStatus.NO_MATCH:
        return "fail"

    # Status AMBIGUOUS
    if attempts == 0:
        return "question"
    else:
        return "fail"


workflow = StateGraph(LoggingAgentState)

workflow.add_node("extractor", extractor_node)
workflow.add_node("question_generator", question_generator_node)
workflow.add_node("human_input", human_input_node)

workflow.set_entry_point("extractor")

workflow.add_conditional_edges(
    "extractor",
    check_confidence,
    {"success": END, "fail": END, "question": "question_generator"},
)

workflow.add_edge("question_generator", "human_input")
workflow.add_edge("human_input", "extractor")


def get_compiled_graph(conn):
    checkpointer = PostgresSaver(conn)

    return workflow.compile(checkpointer=checkpointer, interrupt_before=["human_input"])
