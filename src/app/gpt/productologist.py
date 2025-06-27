import logging
from textwrap import dedent
from typing import Annotated

import marvin
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from app.db import Session
from app.db.models import Category, Product, ProductCategory as ProductCategoryModel, ProductEmbedding
from app.gpt.embeddings import get_embeddings

log = logging.getLogger(__name__)


def format_vector(vector: list[float]) -> str:
    return f"'[{', '.join(str(x) for x in vector)}]'"


ProductQuery = Annotated[str, Field(description="Запрос в каталог продуктов")]


class SearchProductsContext(BaseModel):
    query: str = Field(description="Запрос клиента")


class ProductNutrition(BaseModel):
    calories: float = Field(description="количество ккал")
    fats: float | None = Field(description="жиров")
    proteins: float | None = Field(description="белков")
    carbs: float | None = Field(description="углеводов")


class ProductRating(BaseModel):
    value: float = Field(description="Усреднённый рейтинг продукта, от 1 до 5")
    reviews_count: int = Field(description="Количество обзоров, на которых построен рейтинг")


class ProductCategory(BaseModel):
    name: str = Field(description="Название категории")
    position: int = Field(description="Позиция продукта в категории")


class SelectedProduct(BaseModel):
    id: int = Field(description="ID продукта")
    reason: str = Field(description="По какой причине выбран продукт")
    amount: int = Field(description="Выбранное количество продукта")
    alternative_ids: list[int] = Field(
        description="ID других подходящих продуктов, если такие есть", default_factory=list
    )

    def get_alternatives(self):
        if not self.alternative_ids:
            return []
        with Session() as session:
            return session.scalars(select(Product).where(Product.id.in_(self.alternative_ids))).all()


class ProductCart(BaseModel):
    products: list[SelectedProduct] = Field(description="Список выбранных продуктов", default_factory=list)
    missing_products: list[str] = Field(
        description="Список недостающих продуктов, если такие есть", default_factory=list
    )

    def get_products(self):
        if not self.products:
            return []
        with Session() as session:
            return session.scalars(select(Product).where(Product.id.in_([p.id for p in self.products]))).all()


class ProductOut(BaseModel):
    id: int = Field(description="Уникальный ID продукта")
    name: str = Field(description="Название продукта")
    price: float = Field(description="Цена товара, в казахстанских тенге")
    producer_country: str | None = Field(description="Страна-производитель")
    brand_name: str | None = Field(description="Название бренда")
    rating: ProductRating | None = Field(description="Рейтинг продукта")
    ingredients: str | None = Field(description="Состав продукта")
    features: list[str] | None = Field(description="Особенности продукта")
    nutrition: ProductNutrition | None = Field(description="Пищевая ценность продукта на 100гр.")
    categories: list[ProductCategory] | None = Field(description="Категории продукта")


class ProductSearchFilters(BaseModel):
    max_amount: int = Field(description="Максимальная сумма продукта")


def get_products_by_queries(queries: list[ProductQuery], max_results: int = 20) -> list[Product]:
    log.info("serving queries %s", queries)
    embs = get_embeddings(queries)

    product_ids = set()
    with Session() as session:
        for emb in embs:
            query_ids = session.scalars(
                select(ProductEmbedding.product_id)
                .join(ProductEmbedding.product)
                .where(Product.is_available)
                .order_by(text(f"vector <=> {format_vector(emb.embedding)}"))
                .limit(max_results // len(embs))
            )
            product_ids.update(query_ids)

        # join all necessary data
        products = session.scalars(
            select(Product)
            .options(
                selectinload(Product.features),
                selectinload(Product.product_categories)
                .joinedload(ProductCategoryModel.category)
                .joinedload(Category.parent)
                .joinedload(Category.parent)
                .joinedload(Category.parent),  # 3 level deep ancestors
            )
            .where(Product.id.in_(product_ids))
            .limit(max_results)
        ).all()

    log.info("found: %r", products)
    return products


def search_products(queries: list[ProductQuery], max_results: int = 20) -> list[ProductOut]:
    """Вернуть список товаров, найденных по множеству текстовых запросов."""
    products = get_products_by_queries(queries, max_results)

    return [
        ProductOut(
            id=p.id,
            name=p.name,
            price=p.price_actual,
            producer_country=p.producer_country,
            brand_name=p.brand_name,
            rating=ProductRating(
                value=p.rating_value,
                reviews_count=p.rating_reviews,
            )
            if p.rating_value
            else None,
            ingredients=p.ingredients,
            features=[f.name for f in p.features],
            nutrition=ProductNutrition(
                calories=p.nutrition_kcal,
                fats=p.nutrition_fats,
                carbs=p.nutrition_carbs,
                proteins=p.nutrition_protein,
            )
            if p.nutrition_kcal
            and (p.nutrition_fats or 0) + (p.nutrition_carbs or 0) + (p.nutrition_protein or 0) <= 100
            else None,
            categories=[
                ProductCategory(
                    name=pc.category.text_embedding(),
                    position=pc.sort_pos,
                )
                for pc in p.product_categories
            ],
        )
        for p in products
    ]


if __name__ == "__main__":
    query = input("Введите просьбу: ")
    query = query or "Собери корзину для борща на 6 порций"
    print(f"Просьба: {query!r}")
    marketer = marvin.Agent(
        name="Персональный продуктолог",
        model="openai:gpt-4o-mini",
        instructions=dedent("""
            Ты — персональный помощник по подбору продуктов в супермаркете.

            У тебя есть доступ к каталогу товаров. Ты можешь выполнять векторный поиск по описаниям продуктов,
              и выбирать те, что подходят под запрос клиента.

            Ты **не выдумываешь** продукты и **не сочиняешь** их — ты только выбираешь из существующих товаров,
              которые доступны через функцию поиска.
            В ответ ты должен возвращать только ID выбранных продуктов.

            Твоя задача — собрать корзину под запрос пользователя, учитывая:
            - цели (диета, рацион, готовка, количество порций, семья и т.д.);
            - ограничения (например, «без глютена», «низкоуглеводная диета»);
            - адекватное количество продуктов (не больше и не меньше, чем нужно);
            - существующий контекст, если он есть (ранее добавленные продукты).

            ⚠️ ВАЖНО: когда ты формируешь поисковые запросы, знай,
                что они будут превращены в векторы через модель text-embedding-3-small.
            Это значит, что запросы должны быть короткими, конкретными и содержать ключевые слова,
                которые можно сопоставить с названиями или описаниями товаров.
            Не используй лишние слова или длинные фразы.
        """),
    )

    pids: ProductCart = marketer.run(
        dedent("""
            1. Прочитай запрос пользователя.
            2. Сформулируй несколько поисковых подзапросов (в текстовой форме) для поиска подходящих товаров.
            3. Вызови функцию поиска с этими подзапросами. Получи список товаров.
            4. Из полученных товаров выбери те, что подходят. Верни их ID.
            4.1 Если для позиции подошло несколько продуктов - помести их ID в список альтернативных ID.
            5. Если чего-то не хватает — скорректируй подзапросы и попробуй снова (до 4 итераций).
            6. Если нужного товара не нашлось — добавь его в список `недостающих` с кратким описанием.
            7. Перед завершением:
               - убедись, что товары соответствуют запросу,
               - что их достаточно (но не слишком много),
               - что список `недостающих` обоснован.

            ---

            ⚠️ Внимание:
            - Не повторяй товары.
            - Не выдумывай названия или бренды.
            - Не выбирай случайные продукты — только те, что реально подходят.
        """),
        tools=[search_products],
        result_type=ProductCart,
        context=SearchProductsContext(query=query).model_dump(),
    )
