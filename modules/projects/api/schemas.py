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
    default_persona_id: int | None = None
    # Phase 30 (2.5.2026): parent v stromu, NULL = root
    parent_project_id: int | None = None


class CreateProjectRequest(BaseModel):
    name: str
    # Phase 30: optional parent pro tree (Marti-AI's autonomy + lidske projekty)
    parent_project_id: int | None = None


class CreateProjectResponse(BaseModel):
    id: int
    name: str
    parent_project_id: int | None = None


class MoveProjectRequest(BaseModel):
    """Phase 30: presun projektu pod jineho parenta (None = na root)."""
    new_parent_project_id: int | None = None


class MoveProjectResponse(BaseModel):
    project_id: int
    new_parent_project_id: int | None


class SwitchProjectRequest(BaseModel):
    """project_id = None znamena 'bez projektu' (clear)."""
    project_id: int | None = None


class SwitchProjectResponse(BaseModel):
    project_id: int | None
    project_name: str | None


class RenameProjectRequest(BaseModel):
    name: str


class ProjectMemberInfo(BaseModel):
    user_id: int
    full_name: str
    role: str                        # owner | admin | member
    added_at: datetime
    email: str = ""                  # primarni email (nebo prazdny string)


class AddMemberRequest(BaseModel):
    user_id: int
    role: str = "member"


class SetDefaultPersonaRequest(BaseModel):
    """persona_id=None znamena vycisteni overridu (globalni default)."""
    persona_id: int | None = None


class SetDefaultPersonaResponse(BaseModel):
    project_id: int
    default_persona_id: int | None
    default_persona_name: str | None
