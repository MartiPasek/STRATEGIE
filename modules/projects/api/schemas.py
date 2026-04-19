from datetime import datetime
from pydantic import BaseModel


class ProjectInfo(BaseModel):
    """Polozka v dropdownu projektu."""
    id: int
    name: str
    owner_user_id: int | None = None
    created_at: datetime
    last_activity_at: datetime | None = None
    my_role: str | None = None      # owner | admin | member | owner_tenant | None


class CreateProjectRequest(BaseModel):
    name: str


class CreateProjectResponse(BaseModel):
    id: int
    name: str


class SwitchProjectRequest(BaseModel):
    """project_id = None znamena 'bez projektu' (clear)."""
    project_id: int | None = None


class SwitchProjectResponse(BaseModel):
    project_id: int | None
    project_name: str | None


class RenameProjectRequest(BaseModel):
    name: str
