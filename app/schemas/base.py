from typing import Any

import html2text


def to_camel(string: str) -> str:
    parts = string.split("_")
    return parts[0] + "".join(word.capitalize() for word in parts[1:])


def html_to_markdown(html_text: str) -> str:
    handler = html2text.HTML2Text()
    handler.ignore_links = False  # or True if you want to strip them
    handler.body_width = 0  # no automatic line breaks
    return handler.handle(html_text).strip()


def parse_comma_float(v: Any) -> float | None | Any:
    if isinstance(v, str):
        if not v:
            return None
        try:
            return float(v.replace(",", "."))
        except ValueError:
            # there might be some random text instead
            return None
    return v
