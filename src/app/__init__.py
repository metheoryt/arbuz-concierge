import logging

from app.db import engine
from app.db.models import Base

LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# temporarily put it here to enable logging unconditionally
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
)


def setup():
    Base.metadata.create_all(engine)


def teardown():
    Base.metadata.drop_all(engine)
