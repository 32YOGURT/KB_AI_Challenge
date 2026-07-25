from app.clients.openai_client import get_client

EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072


def embed_text(text: str) -> list[float]:
    response = get_client().embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding
