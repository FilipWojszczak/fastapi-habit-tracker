import textwrap
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from sqlalchemy import text
from sqlmodel import Session

from ..db import engine
from .schemas import InfoAgentState, UserDecision


@tool
def execute_sql(query: str) -> str:
    """Execute a SQL query and return the result as a string."""
    try:
        with Session(engine) as session:
            result = session.exec(text(query)).all()
            return str(result)
    except Exception as e:
        return f"Error: {e!s}"


llm = ChatGoogleGenerativeAI(model="gemini-3-flash-preview")
llm_with_tools = llm.bind_tools([execute_sql])


def info_generator_node(state: InfoAgentState) -> InfoAgentState:
    system_prompt = textwrap.dedent(f"""
    You are a SQL analyst. Your goal is to return information about the user, their habits, and related logs.

    Rules:
    - Think step-by-step and analyze the user's message.
    - ALWAYS filter all your SQL queries using WHERE user_id = {state["user_id"]}.
    - Use only read-only queries - no INSERT/UPDATE/DELETE/ALTER/DROP/CREATE/REPLACE/TRUNCATE.

    Decision path:
    1. CLEAR REQUEST: If the user's request is clear and understandable, use the `execute_sql` tool to generate and execute ONE SELECT query.
    2. AMBIGUOUS REQUEST: If the request is related to the domain (habits, users, logs) but is ambiguous or misses details, DO NOT call the tool. Instead, ask the user a specific clarifying question to get the missing information.
    3. INCOMPREHENSIBLE REQUEST: If the request is completely incomprehensible, irrelevant, or makes no sense at all, DO NOT call the tool. Inform the user that you cannot understand the request and cannot help.
    """)  # noqa: E501

    messages = [SystemMessage(content=system_prompt)] + state["messages"]
    response = llm_with_tools.invoke(messages)
    return {"messages": [response], "user_decision": None}


def route_info_generator(
    state: InfoAgentState,
) -> Literal["interpret_decision", "__end__"]:
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0:
        return "interpret_decision"
    return END


def interpret_decision_node(state: InfoAgentState) -> InfoAgentState:
    system_prompt = textwrap.dedent("""
    You need to interpret user's response and decide if user accepted or rejected the proposed SQL query.
    """)  # noqa: E501
    structured_llm = llm.with_structured_output(UserDecision)
    user_input = state["user_decision_text"]

    result = structured_llm.invoke(
        [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input),
        ]
    )
    return {"user_decision": result}


def route_decision(
    state: InfoAgentState,
) -> Literal["tools", "handle_rejection"]:
    if state["user_decision"].decision == "approve":
        return "tools"
    return "handle_rejection"


def handle_rejection_node(state: InfoAgentState) -> InfoAgentState:
    last_message = state["messages"][-1]
    tool_messages = []

    if hasattr(last_message, "tool_calls"):
        for tool_call in last_message.tool_calls:
            tool_messages.append(
                ToolMessage(
                    tool_call_id=tool_call["id"],
                    name=tool_call["name"],
                    content="Query rejected by the user.",
                )
            )
    tool_messages.append(
        AIMessage(
            content="The SQL query was rejected. Agent's processing will be terminated."
        )
    )

    return {"messages": tool_messages}


workflow = StateGraph(InfoAgentState)

workflow.add_node("info_generator", info_generator_node)
workflow.add_node("interpret_decision", interpret_decision_node)
workflow.add_node("handle_rejection", handle_rejection_node)
tool_node = ToolNode([execute_sql])
workflow.add_node("tools", tool_node)

workflow.add_edge(START, "info_generator")
workflow.add_conditional_edges("info_generator", route_info_generator)
workflow.add_conditional_edges("interpret_decision", route_decision)
workflow.add_edge("tools", "info_generator")
workflow.add_edge("handle_rejection", END)


def get_compiled_info_graph(conn):
    checkpointer = PostgresSaver(conn)
    return workflow.compile(
        checkpointer=checkpointer, interrupt_before=["interpret_decision"]
    )
