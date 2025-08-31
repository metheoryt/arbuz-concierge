from sqlalchemy import select

from app.gpt.embeddings import batch, get_embeddings

from .db import Session
from .db.models import Product
from .db.models.product_embedding import ProductEmbedding


def generate_embeddings():
    i = 0
    with Session() as session:
        qs = select(Product).where(Product.embedding.is_(None))
        products = session.scalars(qs).all()
        for product_batch in batch(products, size=100):
            texts = [p.text_embedding() for p in product_batch]
            embs = get_embeddings(texts)
            for product, emb, text in zip(
                product_batch,
                embs,
                texts,
                strict=False,
            ):
                embedding = ProductEmbedding(vector=emb.embedding, text=text, product=product)
                session.add(embedding)
            session.commit()
            i += len(embs)
            print(f"{i} embeddings generated")
