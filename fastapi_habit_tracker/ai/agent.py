import textwrap
from typing import Literal, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from ..config import get_settings
from ..schemas.ai import AgentDecision, ExtractionStatus

settings = get_settings()
llm = ChatOllama(model="llama3", temperature=0, base_url=settings.ollama_base_url)

structured_llm = llm.with_structured_output(AgentDecision)


class AgentState(TypedDict):
    user_input: str
    chat_history: list[str]
    available_habits: list[str]
    decision: AgentDecision | None
    question: str | None
    attempt_count: int


EXTRACTOR_SYSTEM = textwrap.dedent("""
    You are a precise habit tracking assistant.
    Your goal is to map user text to a STRICTLY DEFINED list of habits.

    Available habits: {habits_list}

    Rules:
    1. If the text clearly matches a habit, set status to "match" and fill 'habit_data'.
    2. If the text is ambiguous (e.g., user said "training" but has both "Gym" and "Running"), set status to "ambiguous". DO NOT GUESS.
    3. If the text is unrelated or creates no match, set status to "no_match".
    4. You have access to chat history to resolve ambiguity.
""")  # noqa: E501

QUESTION_SYSTEM = textwrap.dedent("""
    You are a helpful assistant. The user input was ambiguous regarding their habits.

    Context (available habits): {habits_list}
    Ambiguity reason: {reason}

    Generate a SHORT, direct question to clarify which habit the user meant.
    Example: "Did you mean 'Gym' or 'Running'?"
""")


def extractor_node(state: AgentState):
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
    result: AgentDecision = chain.invoke({"habits_list": habits_str})

    return {
        "decision": result,
        "attempt_count": state["attempt_count"],
    }


def question_generator_node(state: AgentState):
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


def human_input_node(state: AgentState):
    return {"attempt_count": state["attempt_count"] + 1}


def check_confidence(state: AgentState) -> Literal["success", "question", "fail"]:
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


workflow = StateGraph(AgentState)

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

# Replace with PostgresSaver (async)
checkpointer = MemorySaver()

habit_graph = workflow.compile(
    checkpointer=checkpointer, interrupt_before=["human_input"]
)
