from pydantic import BaseModel, ConfigDict, field_validator

from .base import html_to_markdown, to_camel


class CategorySchema(BaseModel):
    id: int
    name: str
    uri: str
    parent_id: int | None = None

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="allow")

    @field_validator("name")
    @classmethod
    def clear_html(cls, val: str) -> str:
        return html_to_markdown(val)
