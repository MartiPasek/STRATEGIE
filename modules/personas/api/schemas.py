from pydantic import BaseModel


class PersonaInfo(BaseModel):
    id: int
    name: str
    description: str | None = None
    is_default: bool
    tenant_id: int | None = None
    is_global: bool


class SwitchPersonaRequest(BaseModel):
    conversation_id: int
    persona_id: int


class SwitchPersonaResponse(BaseModel):
    persona_id: int
    persona_name: str
    already_active: bool


class CreatePersonaRequest(BaseModel):
    name: str
    description: str | None = None
    system_prompt: str


class CreatePersonaResponse(BaseModel):
    id: int
    name: str


class UpdatePersonaRequest(BaseModel):
    """PATCH semantika -- None = nemenit. description '' = vycisti na NULL."""
    name: str | None = None
    description: str | None = None
    system_prompt: str | None = None


class PersonaDetail(BaseModel):
    id: int
    name: str
    description: str | None = None
    system_prompt: str
    tenant_id: int | None = None
    is_global: bool
    is_default: bool
