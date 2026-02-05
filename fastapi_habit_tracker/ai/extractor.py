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

SYSTEM_PROMPT = (
    "You are an assistant that maps user text to a STRICTLY DEFINED list of habits.\n"
    "Rules:\n"
    "1. Your priority is to select exactly one name from the provided "
    '"Available habits" list.\n'
    "2. NEVER return a name that is not on the list.\n"
    "3. If the activity does not match perfectly, choose the habit from the list that "
    'is semantically closest (e.g., if the user writes "ran" and "Workout" is on the '
    'list, select "Workout"; if "crawl" and "Pool" is on the list, select "Pool").\n'
)

USER_PROMPT = (
    "Analyze the following user text and match it to one of the available habits.\n\n"
    "Available habits (CHOOSE ONLY FROM THIS LIST):\n"
    "[{habits_list}]\n\n"
    "User text:\n"
    '"{user_input}"\n\n'
    'Return JSON. Remember: the "habit_name" field MUST contain a string identical to '
    "one of the elements in the habit list above. Do not invent new names.\n"
    "{format_instructions}\n"
)

prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT.strip()),
        (
            "human",
            "I swam 800m crawl today, I'm exhausted. Available habits: [Running, "
            "Swimming, Reading]",
        ),
        (
            "ai",
            '{{"habit_name": "Swimming", "value": 800, "note": "Freestyle (crawl), '
            'exhaustion"}}',
        ),
        ("human", "I drank a glass of water. Available habits: [Drink Water, Walk]"),
        ("ai", '{{"habit_name": "Drink Water", "value": 1, "note": "Glass of water"}}'),
        ("user", USER_PROMPT.strip()),
    ]
)

habit_extraction_chain = prompt_template | llm | parser


def extract_habit_data(user_input: str, available_habits: list[str]) -> HabitLogData:
    """
    Synchronous function to invoke the chain.
    """
    response = habit_extraction_chain.invoke(
        {
            "user_input": user_input,
            "habits_list": ", ".join(available_habits),
            "format_instructions": parser.get_format_instructions(),
        }
    )
    return response
