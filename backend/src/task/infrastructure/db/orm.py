from uuid import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base, BaseMixin


class TaskProductIngredientDB(BaseMixin, Base):
    __tablename__ = "task_ingredients"

    product_id: Mapped[UUID] = mapped_column(ForeignKey("task_products.id", ondelete="CASCADE"))

    name: Mapped[str | None]
    weight: Mapped[float | None]
    kilocalories: Mapped[float | None]
    proteins: Mapped[float | None] = mapped_column(doc="Белки")
    fats: Mapped[float | None]
    carbohydrates: Mapped[float | None]
    fiber: Mapped[float | None] = mapped_column(doc="Клетчатка")

    product: Mapped['TaskProductDB'] = relationship(back_populates="ingredients", lazy="noload")


class TaskProductDB(BaseMixin, Base):
    __tablename__ = "task_products"

    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))

    name: Mapped[str | None]
    weight: Mapped[float | None]
    calories: Mapped[float | None]
    proteins: Mapped[float | None] = mapped_column(doc="Белки")
    fats: Mapped[float | None]
    carbohydrates: Mapped[float | None]
    fiber: Mapped[float | None] = mapped_column(doc="Клетчатка")

    ingredients: Mapped[list["TaskProductIngredientDB"]] = relationship(back_populates="product", lazy="selectin")
    task: Mapped['TaskDB'] = relationship(back_populates="products")


class TaskSportDB(BaseMixin, Base):
    __tablename__ = "task_sports"

    task_id: Mapped[UUID] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"))
    name: Mapped[str | None]
    calories: Mapped[float | None]
    length: Mapped[int | None]

    task: Mapped['TaskDB'] = relationship(back_populates="sports")


class TaskDB(BaseMixin, Base):
    __tablename__ = "tasks"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    app_bundle: Mapped[str]
    status: Mapped[str]
    error: Mapped[str | None]
    request_text: Mapped[str | None]
    request_filename: Mapped[str | None]

    products: Mapped[list['TaskProductDB']] = relationship(back_populates="task", lazy="selectin")
    sports: Mapped[list['TaskSportDB']] = relationship(back_populates="task", lazy="selectin")
    user: Mapped["UserDB"] = relationship(back_populates="tasks")
