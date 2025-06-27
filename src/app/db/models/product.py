from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, utc_now
from .product_category import ProductCategory

if TYPE_CHECKING:
    from .category import Category
    from .feature import Feature
    from .product_embedding import ProductEmbedding


class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_categories: Mapped[list["ProductCategory"]] = relationship(
        back_populates="product",
        foreign_keys=[ProductCategory.product_id],
        lazy="selectin",
    )
    categories: Mapped[list["Category"]] = relationship(
        secondary=ProductCategory.__table__,
        primaryjoin=id == ProductCategory.product_id,
        secondaryjoin="Category.id == ProductCategory.category_id",
        viewonly=True,
        back_populates="products",
        lazy="selectin",
    )
    name: Mapped[str]
    producer_country: Mapped[str | None]
    brand_name: Mapped[str | None]
    description: Mapped[str]  # usually empty
    image_url: Mapped[str | None]
    measure: Mapped[str]
    is_weighted: Mapped[bool]
    weight_avg: Mapped[float]
    weight_min: Mapped[float]
    weight_max: Mapped[float]
    weight: Mapped[str | None]
    piece_weight_max: Mapped[float]
    piece_weight_min: Mapped[float]
    sell_by_piece: Mapped[bool]
    quantity_min_step: Mapped[float]
    price_actual: Mapped[float]
    price_special: Mapped[int | None]
    price_previous: Mapped[str | None]
    is_available: Mapped[bool]
    is_local: Mapped[bool]
    nutrition_fats: Mapped[float | None]
    nutrition_carbs: Mapped[float | None]
    nutrition_protein: Mapped[float | None]
    nutrition_kcal: Mapped[float | None]
    ingredients: Mapped[str | None]
    storage_conditions: Mapped[str | None]
    features: Mapped[list["Feature"]] = relationship(
        secondary="product_features",
        back_populates="products",
        lazy="selectin",
    )
    information: Mapped[str]
    rating_value: Mapped[float | None]
    rating_reviews: Mapped[int | None]

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    embedding: Mapped[Optional["ProductEmbedding"]] = relationship(
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="joined",
    )

    def text_embedding(self):  # noqa C901
        """
        Text embedding of the product in a form:

        {name}
        Бренд: {brand_name}
        Страна: {producer_country}
        Продукт находится в категориях:
        - Category.text_embedding()
        - ...
        Состав: {ingredients}
        Пищевая ценность на 100 г: {nutrition_kcal} ккал,
            жиры: {nutrition_fats} г, белки: {nutrition_protein} г, углеводы: {nutrition_carbs} г
        Рейтинг: {rating_value} из 5, по {rating_reviews} оценкам
        """
        # name
        parts = [self.name]

        # brand and country
        if self.brand_name:
            parts.append(f"Бренд: {self.brand_name}")
        if self.producer_country:
            parts.append(f"Страна: {self.producer_country}")

        # Categories with sort position
        cat_parts = []
        for pc in self.product_categories:
            cat: Category = pc.category
            cat_parts.append(f"- {cat.text_embedding()} (позиция №{pc.sort_pos})")
        if cat_parts:
            parts.append("Продукт находится в категориях: \n" + "\n".join(cat_parts))

        # Features
        if self.features:
            parts.append("Особенности: " + ", ".join([feat.name for feat in self.features]))

        # Ingredients
        if self.ingredients:
            ing = f"Состав: {self.ingredients}"
            ing = ing.rstrip(".")
            parts.append(ing)

        # Nutrition (simplified)
        nutrition_parts = []
        if self.nutrition_protein or self.nutrition_fats or self.nutrition_carbs:
            total_nut = (self.nutrition_protein or 0) + (self.nutrition_fats or 0) + (self.nutrition_carbs or 0)
            if total_nut <= 100:
                # some products have totals bigger than 100g, that's should be a bug in arbuz
                # ignore such cases
                if self.nutrition_kcal is not None:
                    nutrition_parts.append(f"{int(self.nutrition_kcal)} ккал")

                if self.nutrition_fats is not None:
                    nutrition_parts.append(f"жиры: {self.nutrition_fats:.1f} г")
                if self.nutrition_protein is not None:
                    nutrition_parts.append(f"белки: {self.nutrition_protein:.1f} г")
                if self.nutrition_carbs is not None:
                    nutrition_parts.append(f"углеводы: {self.nutrition_carbs:.1f} г")
        if nutrition_parts:
            parts.append("Пищевая ценность на 100 г: " + ", ".join(nutrition_parts))

        # Ratings
        if self.rating_value and self.rating_reviews:
            parts.append(f"Рейтинг: {self.rating_value} из 5, по {self.rating_reviews} оценкам")

        return "\n".join(parts)

    def __repr__(self):
        return f"<Product id={self.id} name={self.name!r} >"
