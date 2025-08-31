# import asyncio
import logging

# from asyncio import WindowsSelectorEventLoopPolicy
from dotenv import load_dotenv

load_dotenv()

# windows hack for marvin
# asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())


LOG_FORMAT = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# temporarily put it here to enable logging unconditionally
logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    datefmt=DATE_FORMAT,
)
