from typing import Literal

from pydantic import BaseModel, ConfigDict, HttpUrl, field_validator

from .base import html_to_markdown, parse_comma_float, to_camel


class ProductCharacteristic(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")
    id: int
    name: str


class ProductNutrition(BaseModel):
    carbs: float | None
    fats: float | None
    protein: float | None
    kcal: float | None

    @field_validator("carbs", "fats", "protein", "kcal", mode="before")
    @classmethod
    def parse_comma_float_fields(cls, v: str | None) -> float | None:
        return parse_comma_float(v)


class ProductRating(BaseModel):
    reviews: int
    value: float

    @field_validator("value", mode="before")
    @classmethod
    def parse_comma_float_fields(cls, v: str | None) -> float | None:
        return parse_comma_float(v)

    @field_validator("reviews", mode="before")
    @classmethod
    def strip_text(cls, v: str | None) -> int | None:
        # strip "12 оценок" into just 12.
        if isinstance(v, str):
            rating, _ = v.split(maxsplit=1)
            return int(rating)
        return v


class ProductSchema(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")

    id: int
    sort_pos: int | None
    brand_name: str | None
    catalog_id: int
    characteristics: list[ProductCharacteristic]
    discount: str
    image: HttpUrl | None
    information: str
    ingredients: str | None
    is_available: bool
    is_express_available: bool
    is_local: bool
    is_main: bool
    is_new: bool
    is_promotional: bool
    is_recommended: bool
    is_verified: bool
    is_weighted: bool
    measure: Literal["шт", "кг"]
    name: str
    nutrition: ProductNutrition | None
    parent_catalog_id: int | None
    piece_weight_max: float
    piece_weight_min: float
    price_actual: float
    price_previous: int | None
    price_special: int | None
    producer_country: str | None
    quantity_express: float
    quantity_min_step: float
    rating: ProductRating | None
    sell_by_piece: bool
    storage_conditions: str | None
    uri: str
    weight: str | None
    weight_avg: float
    weight_max: float
    weight_min: float

    @field_validator("characteristics", mode="before")
    @classmethod
    def default_empty_list(cls, v: list | None) -> list:
        if v is None:
            return []
        return v

    @field_validator("storage_conditions", "information", "ingredients", mode="after")
    @classmethod
    def clear_html(cls, val: str | None) -> str | None:
        if val:
            val = html_to_markdown(val)
        return val
