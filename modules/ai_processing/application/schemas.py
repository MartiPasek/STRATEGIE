from pydantic import BaseModel


class AnalysisInput(BaseModel):
    """Interní vstup pro analýzu — nezávislý na HTTP vrstvě."""
    text: str


class AnalysisOutput(BaseModel):
    """Interní výstup analýzy — strukturovaný výsledek."""
    summary: str
    action_items: list[str]
    persons: list[str]
    recommendations: list[str]
