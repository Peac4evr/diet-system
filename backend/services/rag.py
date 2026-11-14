from sqlalchemy import select

from database import SessionLocal
from models import Food, Guideline
from services.embedding import embed_query


def search_food(query: str, top_k: int = 5):
    """按名字语义搜索食物，返回 [(Food, 相似度), ...]"""
    qv = embed_query(query)  # 查询侧：自动加前缀
    with SessionLocal() as db:
        rows = db.execute(
            select(Food, (1 - Food.embedding.cosine_distance(qv)).label("score"))
            .order_by(Food.embedding.cosine_distance(qv))
            .limit(top_k)
        ).all()
    return [(row[0], float(row[1])) for row in rows]


def search_guideline(query: str, top_k: int = 3):
    """按语义搜索膳食指南切片，返回 [(Guideline, 相似度), ...]"""
    qv = embed_query(query)
    with SessionLocal() as db:
        rows = db.execute(
            select(Guideline, (1 - Guideline.embedding.cosine_distance(qv)).label("score"))
            .order_by(Guideline.embedding.cosine_distance(qv))
            .limit(top_k)
        ).all()
    return [(row[0], float(row[1])) for row in rows]