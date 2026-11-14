from sentence_transformers import SentenceTransformer

from config import settings

_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.embedding_model, local_files_only=True)
    return _model


def embed_passages(texts: list[str]) -> list[list[float]]:
    """存库侧：不加前缀"""
    return get_model().encode(texts, normalize_embeddings=True).tolist()


def embed_query(text: str) -> list[float]:
    """查询侧：加前缀"""
    return get_model().encode(
        [settings.embedding_query_prefix + text], normalize_embeddings=True
    ).tolist()[0]