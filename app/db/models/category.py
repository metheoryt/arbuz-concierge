from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .product_category import ProductCategory

if TYPE_CHECKING:
    from .product import Product


class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(primary_key=True)
    updated_at: Mapped[datetime | None]

    name: Mapped[str]
    uri: Mapped[str]
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("category.id"), nullable=True)

    parent: Mapped[Optional["Category"]] = relationship(
        back_populates="children", remote_side="Category.id", lazy="joined"
    )
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent",
        lazy="selectin",
    )

    product_categories: Mapped[list["ProductCategory"]] = relationship(
        back_populates="category",
        foreign_keys=[ProductCategory.category_id],
    )
    products: Mapped[list["Product"]] = relationship(
        secondary=ProductCategory.__table__,
        primaryjoin=id == ProductCategory.category_id,
        secondaryjoin="Product.id == ProductCategory.product_id",
        viewonly=True,
        back_populates="categories",
    )

    def text_embedding(self):
        return f"{self.parent.text_embedding() + ' > ' if self.parent_id else ''}{self.name}"

    def __repr__(self):
        return f"<Category name={self.name!r} parent_id={self.parent_id} updated_at={self.updated_at}>"
