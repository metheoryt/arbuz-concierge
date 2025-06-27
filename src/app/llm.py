import marvin
from pydantic import BaseModel
from sqlalchemy import select

from app.db import Session
from app.db.models import Category


class LLMCategory(BaseModel):
    id: int
    """ID категории."""
    name: str
    """Имя категории."""
    parent_id: int | None = None
    """Родительская категория."""


class UserQueryContext(BaseModel):
    """Запрос пользователя."""

    query: str


class UserQueryOut(BaseModel):
    """Ответ агента со списком запросов к каталогу."""

    catalog_queries: list[str]


class MarketerContext(BaseModel):
    user_prompt: str
    available_categories: list[LLMCategory]


# Create a memory module
# preferences = marvin.Memory(key="user_preferences", instructions="Remember user preferences and style")

marketer = marvin.Agent(
    name="Персональный продуктолог",
    model="openai:gpt-4o-mini",
    instructions="""
Ты — персональный помощник по подбору продуктов в супермаркете.
У тебя есть доступ к каталогу, и ты можешь выбрать из него подходящие товары.
Ты учитываешь цели пользователя (питание, рацион, диета, семья и т.п.).
Ты не выдумываешь продукты — только выбираешь из предложенных.
Твоя цель — помочь собрать корзину из подходящих товаров.
    """,
)


instruction_prompt = ""

prompt = "Собери корзину для классического борща с говядиной на 6 порций"


marketer.run(prompt, context=UserQueryContext(query=prompt))

with Session() as s:
    cats = s.scalars(select(Category)).all()

context = MarketerContext(
    user_prompt=prompt,
    available_categories=[LLMCategory(id=cat.id, name=cat.name, parent_id=cat.parent_id) for cat in cats],
).model_dump()

res = marketer.run(
    "Выбери категории, в которых должны быть нужные товары.", context=context, result_type=list[LLMCategory]
)

print(res)
