import uuid
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session, select

from ..ai.logging_agent import get_compiled_graph
from ..ai.schemas import ExtractionStatus
from ..db import get_langgraph_pool, get_session
from ..dependencies.auth import get_current_user
from ..models import Habit, HabitLog, User
from ..schemas.ai import LoggingAgentResponse

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
def chat_with_logging_agent(
    text: Annotated[str, Body(embed=True)],
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    thread_id: Annotated[str | None, Body(embed=True)] = None,
):
    statement = select(Habit).where(Habit.user_id == user.id)
    habits = session.exec(statement).all()
    if not habits:
        raise HTTPException(
            status_code=400, detail="No habits found. Create one first."
        )
    habit_names = [h.name for h in habits]

    pool = get_langgraph_pool()

    with pool.connection() as conn:
        habit_graph = get_compiled_graph(conn)

        if not thread_id:
            thread_id = str(uuid.uuid4())
            initial_state = {
                "user_input": text,
                "chat_history": [],
                "available_habits": habit_names,
                "attempt_count": 0,
            }
            config = {"configurable": {"thread_id": thread_id}}
            result = habit_graph.invoke(initial_state, config=config)
        else:
            config = {"configurable": {"thread_id": thread_id}}

            current_state_snapshot = habit_graph.get_state(config)
            if not current_state_snapshot.next:
                raise HTTPException(status_code=400, detail="Thread closed or expired.")

            habit_graph.update_state(
                config,
                {"user_input": text},
                as_node="human_input",
            )

            result = habit_graph.invoke(None, config=config)

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
        session.add(new_log)
        session.commit()
        session.refresh(new_log)

        return LoggingAgentResponse(
            status="success",
            log=data,
            message=f"Logged: {data.habit_name}",
            thread_id=None,
        )

    return LoggingAgentResponse(status="error", message="Unknown AI error.")
