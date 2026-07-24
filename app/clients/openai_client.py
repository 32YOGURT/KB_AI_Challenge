from functools import lru_cache

from openai import OpenAI

from app.config import OPENAI_API_KEY


@lru_cache
def get_client() -> OpenAI:
    return OpenAI(api_key=OPENAI_API_KEY)
