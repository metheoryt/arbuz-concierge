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
    name: Mapped[str]  # name 'Пробиотик Arbuz Select x Dr.Galamilk из козьего молока 240 мл'
    producer_country: Mapped[str | None]  # producerCountry 'Казахстан'
    brand_name: Mapped[str | None]  # brandName 'Arbuz Select x Dr.Galamilk'
    description: Mapped[str]  # description ''
    image_url: Mapped[str | None]
    measure: Mapped[str]  # measure 'шт'
    is_weighted: Mapped[bool]  # isWeighted False
    weight_avg: Mapped[float]  # weightAvg 0
    weight_min: Mapped[float]  # weightMin 1
    weight_max: Mapped[float]  # weightMax 52
    weight: Mapped[str | None]  # weight '1 шт'
    piece_weight_max: Mapped[float]  # pieceWeightMax 0
    piece_weight_min: Mapped[float]  # pieceWeightMin 1
    sell_by_piece: Mapped[bool]  # sellByPiece False
    quantity_min_step: Mapped[float]  # quantityMinStep 1
    price_actual: Mapped[float]  # priceActual 2090
    price_special: Mapped[int | None]  # priceSpecial None
    price_previous: Mapped[str | None]  # pricePrevious 2345
    is_available: Mapped[bool]  # isAvailable True
    is_local: Mapped[bool]
    nutrition_fats: Mapped[float | None]  # nutrition {'fats': '4,7', 'kcal': '72', 'carbs': '3,7', 'protein': '5,2'}
    nutrition_carbs: Mapped[float | None]
    nutrition_protein: Mapped[float | None]
    nutrition_kcal: Mapped[float | None]
    ingredients: Mapped[str | None]  # ingredients 'Цельное козье молоко, закваска молочных культур'
    storage_conditions: Mapped[str | None]  # storageConditions '14 дней, от +2&deg;С до +4&deg;С'
    features: Mapped[list["Feature"]] = relationship(
        secondary="product_features",
        back_populates="products",
        lazy="selectin",
    )
    information: Mapped[str]
    rating_value: Mapped[float | None]  # rating {'value': '4,6', 'reviews': '16 оценок'}
    rating_reviews: Mapped[int | None]
