import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    entity_type: Mapped[str] = mapped_column(String(50))
    action: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20))
    model: Mapped[str] = mapped_column(String(100))
    duration_ms: Mapped[int] = mapped_column(Integer)
    input_length: Mapped[int] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Nullable — systémová volání nemají uživatele
    # FK na users se přidá migrací, zatím jen string
    user_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
