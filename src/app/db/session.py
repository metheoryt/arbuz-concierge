from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings

engine = create_engine(str(settings.database_url))
Session = sessionmaker(engine)
