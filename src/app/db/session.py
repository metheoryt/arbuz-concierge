from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(str(settings.postgres_url))
Session = sessionmaker(engine)
