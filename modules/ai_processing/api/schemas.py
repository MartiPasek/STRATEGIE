from pydantic import BaseModel, Field


class AnalyseRequest(BaseModel):
    """HTTP vstup — co přijde od klienta."""
    text: str = Field(
        ...,
        min_length=10,
        description="Text to analyse (e.g. meeting transcript or voice note).",
        examples=["We met with Ondra and Kristy. We agreed to finish the database schema by Friday."],
    )


class AnalyseResponse(BaseModel):
    """HTTP výstup — co dostane klient."""
    summary: str
    action_items: list[str]
    persons: list[str]
    recommendations: list[str]
