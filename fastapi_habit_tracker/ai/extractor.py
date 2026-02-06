import textwrap

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from ..config import get_settings


class HabitLogData(BaseModel):
    habit_name: str = Field(
        description="The exact name of the habit from the provided list."
    )
    value: int | None = Field(
        description=(
            "The numerical value associated with the activity (e.g., minutes, pages, "
            "liters). 0 if not specified."
        )
    )
    note: str | None = Field(
        description="A short note or summary of the activity extracted from the text."
    )


settings = get_settings()
llm = ChatOllama(model="llama3", temperature=0, base_url=settings.ollama_base_url)

parser = PydanticOutputParser(pydantic_object=HabitLogData)

SYSTEM_PROMPT = textwrap.dedent("""
    You are an assistant that maps user text to a STRICTLY DEFINED list of habits.
    Rules:
    1. You must select exactly one name from the provided list.
    2. If the activity does not match perfectly, choose the semantically closest option from the list (e.g., "ran" -> "Workout", "crawl" -> "Pool").
    3. Output strictly valid JSON.
""")  # noqa: E501

USER_PROMPT = textwrap.dedent("""
    Available habits:
    [{habits_list}]

    User text:
    "{user_input}"

    Analyze the text and return the corresponding JSON object.
    Reminder: The "habit_name" must be an exact string match from the list above.
    {format_instructions}
""")

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT.strip()),
        (
            "human",
            "I swam 800m crawl today, I'm exhausted. Available habits: [Running, Swimming, Reading]",  # noqa: E501
        ),
        (
            "ai",
            '{{"habit_name": "Swimming", "value": 800, "note": "Freestyle (crawl), exhaustion"}}',  # noqa: E501
        ),
        ("human", "I drank a glass of water. Available habits: [Drink Water, Walk]"),
        ("ai", '{{"habit_name": "Drink Water", "value": 1, "note": "Glass of water"}}'),
        ("user", USER_PROMPT.strip()),
    ]
)

habit_extraction_chain = prompt_template | llm | parser


def extract_habit_data(user_input: str, available_habits: list[str]) -> HabitLogData:
    response = habit_extraction_chain.invoke(
        {
            "user_input": user_input,
            "habits_list": ", ".join(available_habits),
            "format_instructions": parser.get_format_instructions(),
        }
    )
    return response
