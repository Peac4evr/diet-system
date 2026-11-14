from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from deps import get_db
from database import SessionLocal
from models import Food, Guideline
from services import rag, embedding, matcher

router = APIRouter()


class FoodIn(BaseModel):
    name: str
    category: str = "自定义"
    calories: float
    protein: float
    fat: float
    carbs: float
    sodium: float


class MatchReq(BaseModel):
    name: str


@router.get("/foods")
def list_foods(page: int = 1, page_size: int = 50, db: Session = Depends(get_db)):
    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    total = db.execute(select(func.count(Food.id))).scalar()
    rows = db.execute(
        select(Food).order_by(Food.id).offset((page - 1) * page_size).limit(page_size)
    ).scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [{"id": f.id, "name": f.name, "category": f.category,
                   "calories": f.calories, "protein": f.protein,
                   "fat": f.fat, "carbs": f.carbs, "sodium": f.sodium} for f in rows],
    }


@router.get("/foods/search")
def search_foods(q: str, db: Session = Depends(get_db)):
    results = {}
    for food, score in rag.search_food(q, top_k=30):
        results[food.name] = {"name": food.name, "category": food.category,
                              "calories": food.calories, "protein": food.protein,
                              "fat": food.fat, "carbs": food.carbs, "sodium": food.sodium,
                              "score": round(score, 3)}
    for food in db.execute(select(Food).where(Food.name.like(f"%{q}%")).limit(30)).scalars().all():
        if food.name not in results:
            results[food.name] = {"name": food.name, "category": food.category,
                                  "calories": food.calories, "protein": food.protein,
                                  "fat": food.fat, "carbs": food.carbs, "sodium": food.sodium,
                                  "score": 1.0}
    return list(results.values())


@router.post("/foods")
def add_food(req: FoodIn, db: Session = Depends(get_db)):
    vec = embedding.embed_passages([req.name])[0]
    food = Food(name=req.name, category=req.category,
                calories=req.calories, protein=req.protein,
                fat=req.fat, carbs=req.carbs, sodium=req.sodium,
                embedding=vec)
    db.add(food)
    db.commit()
    db.refresh(food)
    return {"id": food.id, "name": food.name, "category": food.category}


@router.post("/foods/match")
async def match_food_endpoint(req: MatchReq):
    name, score = await matcher.match_food(req.name)
    if name:
        with SessionLocal() as db:
            food = db.execute(select(Food).where(Food.name == name)).scalar()
            if food:
                return {"matched_name": name, "score": score,
                        "per100": {"calories": food.calories, "protein": food.protein,
                                   "fat": food.fat, "carbs": food.carbs, "sodium": food.sodium}}
    return {"matched_name": name, "score": score}

class GuidelineIn(BaseModel):
    title: str
    content: str
    source: str = "用户导入"


@router.get("/guidelines")
def list_guidelines(q: str | None = None, db: Session = Depends(get_db)):
    if q and q.strip():
        qs = q.strip()
        results = {}
        for g, score in rag.search_guideline(qs, top_k=20):
            results[g.id] = {"id": g.id, "title": g.title, "content": g.content,
                             "source": g.source, "score": round(score, 3)}
        for g in db.execute(
            select(Guideline).where(or_(Guideline.title.like(f"%{qs}%"), Guideline.content.like(f"%{qs}%")))
        ).scalars().all():
            if g.id not in results:
                results[g.id] = {"id": g.id, "title": g.title, "content": g.content,
                                 "source": g.source, "score": 1.0}
        return list(results.values())

    rows = db.execute(select(Guideline).order_by(Guideline.id)).scalars().all()
    return [{"id": g.id, "title": g.title, "content": g.content, "source": g.source} for g in rows]


@router.post("/guidelines")
def add_guideline(req: GuidelineIn, db: Session = Depends(get_db)):
    title = req.title.strip()
    content = req.content.strip()
    if not title or not content:
        raise HTTPException(400, "标题和内容不能为空")
    text = title + "：" + content
    vec = embedding.embed_passages([text])[0]
    g = Guideline(title=title, content=content,
                  source=req.source.strip() or "用户导入", embedding=vec)
    db.add(g)
    db.commit()
    db.refresh(g)
    return {"id": g.id, "title": g.title, "source": g.source}


@router.delete("/guidelines/{guideline_id}")
def delete_guideline(guideline_id: int, db: Session = Depends(get_db)):
    g = db.get(Guideline, guideline_id)
    if not g:
        raise HTTPException(404, "文献不存在")
    db.delete(g)
    db.commit()
    return {"ok": True}

