from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .product_category import ProductCategory

if TYPE_CHECKING:
    from .category import Category
    from .feature import Feature


class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_categories: Mapped[list["ProductCategory"]] = relationship(
        back_populates="product",
        foreign_keys=[ProductCategory.product_id],
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
    description: Mapped[str]
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
