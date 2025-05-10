from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .category import Category
    from .product import Product


class ProductCategory(Base):
    __tablename__ = "product_category"

    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), primary_key=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("category.id"), primary_key=True)
    product: Mapped["Product"] = relationship(back_populates="product_categories", foreign_keys=[product_id])
    category: Mapped["Category"] = relationship(back_populates="product_categories", foreign_keys=[category_id])

    sort_pos: Mapped[int]
