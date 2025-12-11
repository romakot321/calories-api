from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, BaseMixin


class UserDB(Base, BaseMixin):
    __tablename__ = "users"

    apphud_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    gender: Mapped[str | None]
    age: Mapped[int | None]
    height: Mapped[int | None]
    target: Mapped[str | None]

    tasks: Mapped[list["TaskDB"]] = relationship(back_populates="user", lazy="selectin")
