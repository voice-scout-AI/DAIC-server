import os

from dotenv import load_dotenv

load_dotenv()

UPSTAGE_API_KEY = os.getenv("UPSTAGE_API_KEY")
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT"))
ENV = os.getenv("ENV")
DEBUG = ENV != "production"

os.environ["UPSTAGE_API_KEY"] = UPSTAGE_API_KEY
