from pydantic import BaseModel, ConfigDict

from .base import to_camel


class CategorySchema(BaseModel):
    id: int
    name: str
    uri: str
    parent_id: int | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")
