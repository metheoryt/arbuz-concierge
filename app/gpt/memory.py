import marvin
from langchain_openai.embeddings import OpenAIEmbeddings
from marvin.memory.providers.postgres import PostgresMemory
from marvin.settings import settings as marvin_settings

provider = PostgresMemory(
    database_url=str(marvin_settings.database_url), embedding_fn=lambda: OpenAIEmbeddings("text-embedding-3-small")
)

memory = marvin.Memory(key="test", provider=provider)
