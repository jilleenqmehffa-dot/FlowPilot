from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, RecordMixin

if TYPE_CHECKING:
    from backend.app.models.company import Company


class Contact(RecordMixin, Base):
    __tablename__ = "contacts"

    company_id: Mapped[int] = mapped_column(
        ForeignKey("companies.id", ondelete="RESTRICT"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(50))

    company: Mapped[Company] = relationship(back_populates="contacts")
