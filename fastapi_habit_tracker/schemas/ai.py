from pydantic import BaseModel


class AILogRequest(BaseModel):
    text: str
