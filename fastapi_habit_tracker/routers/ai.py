import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from ..ai.info_agent import get_compiled_info_graph
from ..ai.logging_agent import get_compiled_graph
from ..ai.schemas import ExtractionStatus
from ..db import get_langgraph_pool, get_session
from ..dependencies.auth import get_current_user
from ..models import Habit, HabitLog, User
from ..schemas.ai import InfoAgentResponse, LoggingAgentResponse

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post(
    "/chat-logging-agent",
    response_model=LoggingAgentResponse,
    summary="Create habit log with AI",
    description=(
        "Analyzes natural language text to log a habit.\n\n"
        "1. Fetches user's available habits.  \n"
        "2. Uses LLM to match text to a habit (asks if text is ambiguous) and extract "
        "details.  \n"
        "3. Saves the new log to the database.  \n"
    ),
)
async def chat_with_logging_agent(
    text: Annotated[str, Body(embed=True)],
    session: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    thread_id: Annotated[str | None, Body(embed=True)] = None,
):
    statement = select(Habit).where(Habit.user_id == user.id)
    habits = await session.exec(statement).all()
    if not habits:
        raise HTTPException(
            status_code=400, detail="No habits found. Create one first."
        )
    habit_names = [h.name for h in habits]

    pool = get_langgraph_pool()

    async with pool.connection() as conn:
        habit_graph = get_compiled_graph(conn)

        if not thread_id:
            thread_id = f"log-{uuid.uuid4()}"
            initial_state = {
                "user_input": text,
                "chat_history": [],
                "available_habits": habit_names,
                "attempt_count": 0,
            }
            config = {"configurable": {"thread_id": thread_id}}
            result = await habit_graph.ainvoke(initial_state, config=config)
        else:
            config = {"configurable": {"thread_id": thread_id}}

            current_state_snapshot = await habit_graph.aget_state(config)
            if not current_state_snapshot.next:
                raise HTTPException(status_code=400, detail="Thread closed or expired.")

            await habit_graph.aupdate_state(
                config,
                {"user_input": text},
                as_node="human_input",
            )

            result = await habit_graph.ainvoke(None, config=config)

    final_decision = result.get("decision")

    if final_decision.status == ExtractionStatus.AMBIGUOUS:
        return LoggingAgentResponse(
            status="question",
            message=result.get("question", "Could you clarify?"),
            thread_id=thread_id,
        )

    if not final_decision or final_decision.status == ExtractionStatus.NO_MATCH:
        return LoggingAgentResponse(
            status="error",
            message="I couldn't match this to any of your habits.",
            thread_id=None,
        )

    if final_decision.status == ExtractionStatus.MATCH and final_decision.habit_data:
        data = final_decision.habit_data

        matched_habit = next((h for h in habits if h.name == data.habit_name), None)
        if not matched_habit:
            return LoggingAgentResponse(
                status="error", message=f"Habit {data.habit_name} not found in DB."
            )

        new_log = HabitLog(habit_id=matched_habit.id, value=data.value, note=data.note)
        await session.add(new_log)
        await session.commit()
        await session.refresh(new_log)

        return LoggingAgentResponse(
            status="success",
            log=data,
            message=f"Logged: {data.habit_name}",
            thread_id=None,
        )

    return LoggingAgentResponse(status="error", message="Unknown AI error.")


@router.post(
    "/chat-info-agent",
    response_model=InfoAgentResponse,
    summary="Get information about yourself with AI",
    description=(
        "Analyzes natural language text to return information or statistics about the "
        "user.\n\n"
        "The Agent proposes SQL queries for retrieving data. User can accept or reject "
        "it. If accepted, the agent prepares statement based on result of the query (or"
        " queries, if needed more)."
    ),
)
async def chat_with_info_agent(
    text: Annotated[str, Body(embed=True)],
    user: Annotated[User, Depends(get_current_user)],
    thread_id: Annotated[str | None, Body(embed=True)] = None,
):
    pool = get_langgraph_pool()

    async with pool.connection() as conn:
        info_agent = get_compiled_info_graph(conn)
        if not thread_id:
            thread_id = f"info-{uuid.uuid4()}"
            initial_state = {
                "messages": [{"role": "user", "content": text}],
                "user_id": user.id,
            }
            config = {"configurable": {"thread_id": thread_id}}
            result = await info_agent.ainvoke(initial_state, config=config)
        else:
            config = {"configurable": {"thread_id": thread_id}}

            current_state_snapshot = await info_agent.aget_state(config)
            if not current_state_snapshot.next:
                raise HTTPException(status_code=400, detail="Thread closed or expired.")

            if hasattr(
                current_state_snapshot.values.get("messages", [])[-1], "tool_calls"
            ):
                await info_agent.aupdate_state(config, {"user_decision_text": text})
            else:
                await info_agent.aupdate_state(
                    config, {"messages": [{"role": "user", "content": text}]}
                )

            result = await info_agent.ainvoke(None, config=config)

        if result.get("messages") and len(result["messages"]) > 0:
            if (
                hasattr(result.get("messages")[-1], "tool_calls")
                and len(result.get("messages")[-1].tool_calls) > 0
            ):
                query = result.get("messages")[-1].tool_calls[0]["args"]["query"]
                message = f"Do you agree to send the following SQL query: '{query}'?"
            else:
                message = (
                    result["messages"][-1].content[0]["text"]
                    if isinstance(result["messages"][-1].content, list)
                    else result["messages"][-1].content
                )

            return InfoAgentResponse(
                message=message,
                thread_id=thread_id,
            )
        return InfoAgentResponse(
            message="Unknown AI error.",
            thread_id=None,
        )
