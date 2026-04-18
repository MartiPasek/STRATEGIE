from pydantic import BaseModel


class SaveMemoryRequest(BaseModel):
    content: str
    project_id: int | None = None


class SaveMemoryResponse(BaseModel):
    id: int
    content: str


class MemoryListResponse(BaseModel):
    memories: list[str]
