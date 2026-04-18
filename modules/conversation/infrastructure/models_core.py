from sqlalchemy import BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from core.database_core import BaseCore


class SystemPrompt(BaseCore):
    __tablename__ = "system_prompts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text)
