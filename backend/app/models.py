from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    prompt: str
    file_id: str

class ChatResponse(BaseModel):
    output: Optional[str] = None
    image: Optional[str] = None