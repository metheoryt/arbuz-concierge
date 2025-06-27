from datetime import datetime
from typing import TYPE_CHECKING

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, utc_now

if TYPE_CHECKING:
    from .product import Product


class ProductEmbedding(Base):
    __tablename__ = "product_embedding"
    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    text: Mapped[str]
    vector: Mapped[list[float]] = mapped_column(Vector(1536))  # for text-embedding-3-small

    product_id: Mapped[int] = mapped_column(ForeignKey("product.id"), unique=True)
    product: Mapped["Product"] = relationship(back_populates="embedding", lazy="joined")
