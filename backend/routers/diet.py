import json
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from deps import get_db, get_current_user
from models import User, Food, DietRecord, DietRecordItem
from services import parser, nutrition, llm

router = APIRouter()


class ParseReq(BaseModel):
    text: str


class RecordItemIn(BaseModel):
    name: str
    matched_name: str | None = None
    weight_g: float
    confidence: float = 0.0
    nutrition: dict | None = None


class RecordIn(BaseModel):
    record_date: str
    meal_type: str
    raw_text: str = ""
    items: list[RecordItemIn]


class EstimateWeightReq(BaseModel):
    name: str
    context: str = ""


class EstimateNutritionReq(BaseModel):
    name: str
    weight_g: float
    context: str = ""


@router.post("/diet/parse")
async def parse_diet(req: ParseReq):
    result = await parser.deconstruct_diet(req.text)
    nutr = nutrition.calc_meal_nutrition(result["items"])
    result["items"] = nutr["items"]
    result["totals"] = nutr["totals"]
    return result


@router.post("/diet/estimate-weight")
async def estimate_weight(req: EstimateWeightReq):
    if req.context:
        prompt = (
            f'用户原本这样描述自己吃的一餐："{req.context}"\n'
            f'现在用户补充说还吃了/加了"{req.name}"。\n'
            f'请先判断：这个"{req.name}"是"额外单独吃的"（不在原本那餐里），还是"加进了原本那餐里"的配料？\n'
            f'然后据此估计"{req.name}"大概多少克：\n'
            f'- 如果是额外单独吃，按"一份该食物"的常见量估；\n'
            f'- 如果是加进那餐里，按"配料"的量估。\n'
            f'只回复一个数字（克），不要单位、不要任何文字。'
        )
    else:
        prompt = (
            f'根据常见中式餐饮份量，估计"一份{req.name}"大概多少克。\n'
            f'只回复一个数字（克），不要单位、不要任何文字。'
        )
    raw = (await llm.chat([{"role": "user", "content": prompt}])).strip()
    try:
        return {"weight_g": float(raw)}
    except ValueError:
        return {"weight_g": 100.0}


@router.post("/diet/estimate-nutrition")
async def estimate_nutrition(req: EstimateNutritionReq):
    if req.context:
        prompt = (
            f'用户原本这样描述自己吃的一餐："{req.context}"\n'
            f'现在用户补充说还吃了/加了"{req.name}"（约 {req.weight_g} 克）。\n'
            f'请先判断它是"额外单独吃的"还是"加进了原本那餐里"，再据此估计它的营养成分。\n'
            f'只回复 JSON，不要解释。格式：'
            f'{{"calories": 千卡, "protein": 克, "fat": 克, "carbs": 克, "sodium": 毫克}}\n'
            f'数值要贴近真实、合理。'
        )
    else:
        prompt = (
            f'你是营养师。估计"{req.name}"（约 {req.weight_g} 克）的营养成分。\n'
            f'只回复 JSON，不要解释。格式：'
            f'{{"calories": 千卡, "protein": 克, "fat": 克, "carbs": 克, "sodium": 毫克}}\n'
            f'数值要贴近真实、合理。'
        )
    raw = await llm.chat([{"role": "user", "content": prompt}], json_mode=True)
    data = json.loads(raw)
    data["estimated"] = True
    return data


@router.post("/diet/records")
def save_record(req: RecordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = DietRecord(
        user_id=user.id,
        record_date=date.fromisoformat(req.record_date),
        meal_type=req.meal_type,
        raw_text=req.raw_text,
        structured_json=json.dumps([it.model_dump() for it in req.items], ensure_ascii=False),
        confirmed=True,
        total_calories=0, total_protein_g=0, total_fat_g=0, total_carbs_g=0, total_sodium_mg=0,
    )
    db.add(record)
    db.flush()

    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "sodium": 0.0}

    for it in req.items:
        nutr = None
        food_id = None
        if it.matched_name:
            food = db.execute(select(Food).where(Food.name == it.matched_name)).scalar()
            if food:
                food_id = food.id
                k = it.weight_g / 100
                nutr = {"calories": food.calories * k, "protein": food.protein * k,
                        "fat": food.fat * k, "carbs": food.carbs * k, "sodium": food.sodium * k}
        elif it.nutrition:
            nutr = {k: float(it.nutrition.get(k, 0) or 0) for k in ["calories", "protein", "fat", "carbs", "sodium"]}

        if nutr:
            for k in totals:
                totals[k] += nutr[k]
            db.add(DietRecordItem(
                record_id=record.id, food_name=it.name, matched_food_id=food_id,
                weight_g=it.weight_g, confidence=it.confidence,
                calories=round(nutr["calories"], 2), protein_g=round(nutr["protein"], 2),
                fat_g=round(nutr["fat"], 2), carbs_g=round(nutr["carbs"], 2),
                sodium_mg=round(nutr["sodium"], 2),
            ))

    record.total_calories = round(totals["calories"], 2)
    record.total_protein_g = round(totals["protein"], 2)
    record.total_fat_g = round(totals["fat"], 2)
    record.total_carbs_g = round(totals["carbs"], 2)
    record.total_sodium_mg = round(totals["sodium"], 2)

    db.commit()
    db.refresh(record)
    return {"record_id": record.id, "totals": {k: round(v, 2) for k, v in totals.items()}}


@router.get("/diet/records")
def list_records(record_date: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(DietRecord)
        .where(DietRecord.record_date == date.fromisoformat(record_date), DietRecord.user_id == user.id)
        .order_by(DietRecord.id)
    ).scalars().all()


@router.get("/diet/records/{record_id}")
def get_record(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.execute(
        select(DietRecord).where(DietRecord.id == record_id, DietRecord.user_id == user.id)
    ).scalar()
    if not record:
        raise HTTPException(404, "记录不存在")

    items = db.execute(select(DietRecordItem).where(DietRecordItem.record_id == record_id)).scalars().all()
    result_items = []
    for it in items:
        matched_name = None
        if it.matched_food_id:
            food = db.execute(select(Food).where(Food.id == it.matched_food_id)).scalar()
            matched_name = food.name if food else None
        result_items.append({
            "name": it.food_name,
            "matched_name": matched_name,
            "weight_g": it.weight_g,
            "confidence": it.confidence,
            "nutrition": {
                "calories": it.calories, "protein": it.protein_g,
                "fat": it.fat_g, "carbs": it.carbs_g, "sodium": it.sodium_mg,
            },
        })

    return {
        "id": record.id,
        "record_date": str(record.record_date),
        "meal_type": record.meal_type,
        "raw_text": record.raw_text,
        "items": result_items,
    }


@router.delete("/diet/records/{record_id}")
def delete_record(record_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = db.execute(
        select(DietRecord).where(DietRecord.id == record_id, DietRecord.user_id == user.id)
    ).scalar()
    if not record:
        raise HTTPException(404, "记录不存在")
    db.execute(delete(DietRecordItem).where(DietRecordItem.record_id == record_id))
    db.delete(record)
    db.commit()
    return {"ok": True}


def compute_warnings(totals: dict) -> list[dict]:
    """基于当天摄入计算营养预警（钠 / 脂肪供能比 / 碳水供能比）。"""
    warnings = []
    cal = totals.get("calories", 0.0)
    sodium = totals.get("sodium", 0.0)
    fat = totals.get("fat", 0.0)
    carbs = totals.get("carbs", 0.0)

    if sodium > 2000:
        warnings.append({"type": "sodium", "level": "high", "title": "钠摄入超标",
                         "detail": f"今日钠 {sodium:.0f} 毫克，超过 2000 毫克建议上限，警惕隐形盐分。"})
    elif sodium > 1500:
        warnings.append({"type": "sodium", "level": "medium", "title": "钠摄入偏高",
                         "detail": f"今日钠 {sodium:.0f} 毫克，接近 2000 毫克上限，外卖、腌制食物要留意。"})

    if cal > 0:
        fat_pct = fat * 9 / cal * 100
        if fat_pct > 35:
            warnings.append({"type": "fat", "level": "high", "title": "脂肪供能比偏高",
                             "detail": f"脂肪供能占 {fat_pct:.0f}%，超过 30% 推荐上限，警惕油炸、干锅、麻辣烫等隐形油脂。"})
        elif fat_pct > 30:
            warnings.append({"type": "fat", "level": "medium", "title": "脂肪供能比偏高",
                             "detail": f"脂肪供能占 {fat_pct:.0f}%，略超 30% 推荐上限，可减少油脂烹饪。"})

        carb_pct = carbs * 4 / cal * 100
        if carb_pct > 65:
            warnings.append({"type": "carbs", "level": "high", "title": "碳水供能比偏高",
                             "detail": f"碳水供能占 {carb_pct:.0f}%，超过 65% 推荐上限，留意含糖饮料与精制主食。"})

    return warnings

@router.get("/diet/summary")
def summary(record_date: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    records = db.execute(
        select(DietRecord)
        .where(DietRecord.record_date == date.fromisoformat(record_date), DietRecord.user_id == user.id)
    ).scalars().all()

    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "sodium": 0.0}
    for r in records:
        totals["calories"] += r.total_calories
        totals["protein"] += r.total_protein_g
        totals["fat"] += r.total_fat_g
        totals["carbs"] += r.total_carbs_g
        totals["sodium"] += r.total_sodium_mg

    targets = {
        "calories": user.target_calories,
        "protein_g": user.target_protein_g,
        "fat_g": user.target_fat_g,
        "carbs_g": user.target_carbs_g,
    }

    return {
        "date": record_date,
        "totals": {k: round(v, 2) for k, v in totals.items()},
        "targets": targets,
        "record_count": len(records),
        "warnings": compute_warnings(totals),
    }


@router.get("/diet/trend")
def trend(start_date: str, end_date: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        start, end = end, start

    records = db.execute(
        select(DietRecord).where(
            DietRecord.user_id == user.id,
            DietRecord.record_date >= start,
            DietRecord.record_date <= end,
        )
    ).scalars().all()

    daily: dict[str, dict] = {}
    for r in records:
        d = str(r.record_date)
        daily.setdefault(d, {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "sodium": 0.0})
        daily[d]["calories"] += r.total_calories
        daily[d]["protein"] += r.total_protein_g
        daily[d]["fat"] += r.total_fat_g
        daily[d]["carbs"] += r.total_carbs_g
        daily[d]["sodium"] += r.total_sodium_mg

    days = []
    cur = start
    while cur <= end:
        d = str(cur)
        v = daily.get(d, {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "sodium": 0.0})
        days.append({"date": d, **{k: round(v[k], 2) for k in v}})
        cur += timedelta(days=1)

    return {
        "days": days,
        "targets": {
            "calories": round(user.target_calories, 2),
            "protein_g": round(user.target_protein_g, 2),
            "fat_g": round(user.target_fat_g, 2),
            "carbs_g": round(user.target_carbs_g, 2),
        },
    }

