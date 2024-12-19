from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    phase: str = Field(..., description="Translation phase")
    language: str = Field(..., description="Tranlate to language")


class TranslateResponse(BaseModel):
    result: str
