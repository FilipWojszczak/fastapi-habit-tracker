from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain_core.tools import tool
from langgraph.checkpoint.postgres import PostgresSaver
from sqlmodel import Session

from ..db import get_session


@tool
def execute_sql(query: str) -> str:
    """Execute a SQL query and return the result as a string."""
    session: Session = get_session()
    result = session.exec(query).all()
    session.close()
    return result


SYSTEM_PROMPT = """You are a SQL analyst.

Rules:
- Think step-by-step.
- When you need data, call the tool `execute_sql` with ONE SELECT query.
- Use only read-only queries - no INSERT/UPDATE/DELETE/ALTER/DROP/CREATE/REPLACE/TRUNCATE.
- If the tool returns 'Error:', revise the SQL and try again.
"""  # noqa: E501


def get_info_agent(conn):
    return create_agent(
        model="google_genai:gemini-3-flash-preview",
        tools=[execute_sql],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=PostgresSaver(conn),
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "execute_sql": {"allowed_decisions": ["approve", "reject"]}
                }
            )
        ],
    )
