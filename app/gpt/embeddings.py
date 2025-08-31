from openai.types import Embedding

from .openai import client


def batch(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def get_embeddings(texts: list[str]) -> list[Embedding]:
    rs = client.embeddings.create(input=texts, model="text-embedding-3-small")
    return rs.data
