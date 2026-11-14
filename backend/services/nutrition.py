from sqlalchemy import select

from database import SessionLocal
from models import Food


def calc_meal_nutrition(items: list[dict]) -> dict:
    """把拆解结果里的 (matched_name, weight_g) 算成营养。
    返回 {"totals": {...}, "items": [每项带 nutrition 或 computed=False]}"""
    totals = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "sodium": 0.0}
    out_items = []

    with SessionLocal() as db:
        for it in items:
            name = it.get("matched_name")
            weight = float(it.get("weight_g") or 0)
            food = db.execute(select(Food).where(Food.name == name)).scalar() if name else None
            if food is None:                      # 没匹配到的（如汤底），跳过
                out_items.append({**it, "computed": False})
                continue
            k = weight / 100                      # 每100g → 实际克重
            nutr = {
                "calories": food.calories * k,
                "protein": food.protein * k,
                "fat": food.fat * k,
                "carbs": food.carbs * k,
                "sodium": food.sodium * k,
            }
            for key in totals:
                totals[key] += nutr[key]
            out_items.append({**it, "computed": True,
                              "nutrition": {kk: round(vv, 2) for kk, vv in nutr.items()}})

    return {"totals": {k: round(v, 2) for k, v in totals.items()}, "items": out_items}

ACTIVITY = {"sedentary": 1.2, "light": 1.375, "moderate": 1.55, "active": 1.725, "very_active": 1.9}


def calc_bmr(gender, weight_kg, height_cm, age):
    if gender == "male":
        return 88.362 + 13.397 * weight_kg + 4.799 * height_cm - 5.677 * age
    return 447.593 + 9.247 * weight_kg + 3.098 * height_cm - 4.330 * age


def calc_targets(tdee, goal):
    delta = 300 if goal == "build_muscle" else (-400 if goal == "lose_fat" else 0)
    cal = tdee + delta
    return {
        "calories": round(cal, 2),
        "protein_g": round(cal * 0.20 / 4, 2),
        "fat_g": round(cal * 0.25 / 9, 2),
        "carbs_g": round(cal * 0.55 / 4, 2),
    }