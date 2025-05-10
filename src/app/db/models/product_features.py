from sqlalchemy import Column, ForeignKey, Table

from .base import Base

product_features = Table(
    "product_features",
    Base.metadata,
    Column("product_id", ForeignKey("product.id"), primary_key=True),
    Column("feature_id", ForeignKey("feature.id"), primary_key=True),
)
