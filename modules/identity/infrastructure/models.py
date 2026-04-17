import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    identities: Mapped[list["UserIdentity"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserIdentity(Base):
    __tablename__ = "user_identities"

    # Unikátnost: stejný typ + hodnota nesmí existovat dvakrát
    __table_args__ = (
        UniqueConstraint("type", "value", name="uq_identity_type_value"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE")
    )
    # MVP typy: "email" | "phone"
    type: Mapped[str] = mapped_column(String(20))
    value: Mapped[str] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user: Mapped["User"] = relationship(back_populates="identities")
