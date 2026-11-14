import json
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from deps import get_db, get_current_user
from models import User, DietRecord, DailyAdvice
from services import llm, rag

router = APIRouter()


class AdviceReq(BaseModel):
    record_date: str


def _situation_query(goal: str, intake: dict, targets: dict) -> str:
    """根据目标 + 当日摄入与目标的差距，构造检索句，召回最相关的指南切片。"""
    parts = []
    if goal == "lose_fat":
        parts.append("减脂期热量控制")
    elif goal == "build_muscle":
        parts.append("增肌期蛋白质与碳水")
    else:
        parts.append("平衡膳食 营养搭配")

    if intake.get("sodium", 0) > 2000:
        parts.append("控盐少钠")
    if targets.get("protein_g") and intake.get("protein", 0) < targets["protein_g"] * 0.8:
        parts.append("优质蛋白摄入不足 适量吃鱼禽蛋瘦肉")
    if targets.get("fat_g") and intake.get("fat", 0) > targets["fat_g"] * 1.2:
        parts.append("少油控脂 隐形脂肪")
    if targets.get("carbs_g") and intake.get("carbs", 0) > targets["carbs_g"] * 1.2:
        parts.append("主食粗细搭配 控糖")
    return " ".join(parts)


@router.post("/advice")
async def generate_advice(req: AdviceReq, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = date.fromisoformat(req.record_date)
    records = db.execute(
        select(DietRecord).where(DietRecord.record_date == d, DietRecord.user_id == user.id)
    ).scalars().all()

    intake = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0, "sodium": 0.0}
    for r in records:
        intake["calories"] += r.total_calories
        intake["protein"] += r.total_protein_g
        intake["fat"] += r.total_fat_g
        intake["carbs"] += r.total_carbs_g
        intake["sodium"] += r.total_sodium_mg

    targets = {
        "calories": user.target_calories,
        "protein_g": user.target_protein_g,
        "fat_g": user.target_fat_g,
        "carbs_g": user.target_carbs_g,
    }

    goal_label = {"lose_fat": "减脂", "build_muscle": "增肌", "maintain": "保持健康"}.get(user.goal, "保持健康")

    # ---- RAG：从本地膳食指南知识库召回最相关的权威依据 ----
    query = _situation_query(user.goal, intake, targets)
    hits = rag.search_guideline(query, top_k=3)
    if hits:
        evidence = "\n".join(
            f"- {g.title}（来源：{g.source}）：{g.content}" for g, _ in hits
        )
    else:
        evidence = "（本地知识库暂无匹配指南，请依据通用营养学常识回答）"
    refs = [{"title": g.title, "source": g.source, "content": g.content} for g, _ in hits]
    refs_json = json.dumps(refs, ensure_ascii=False)
    # ------------------------------------------------------

    prompt = (
        "你是一位温暖、专业的营养师，像朋友一样给用户建议。\n"
        f"用户当前目标：{goal_label}\n"
        f"当天摄入：{json.dumps(intake, ensure_ascii=False)}\n"
        f"目标：{json.dumps(targets, ensure_ascii=False)}\n\n"
        "以下是从本地权威知识库检索到的、与用户当前情况最相关的膳食指南，"
        "请务必以这些内容为依据给出建议，并可自然引用其中的原则：\n"
        f"{evidence}\n\n"
        "请结合用户目标来给建议：\n"
        "- 减脂目标：脂肪、碳水偏低是符合减脂方向的，不要建议盲目补充脂肪；重点看蛋白质够不够、热量缺口是否合理、会不会掉肌肉\n"
        "- 增肌目标：需要热量盈余、充足蛋白质，碳水是训练供能的关键，要看是否吃够\n"
        "- 保持目标：追求营养均衡\n"
        "要求：\n"
        "1. 先肯定和鼓励用户已经做到的部分\n"
        "2. 针对目标指出 1~2 个最值得调整的方向；几克、几十千卡的小偏差不要吹毛求疵\n"
        "3. 展望坚持调整几周后的积极变化（减脂看体脂体型，增肌看力量和肌肉量）\n"
        "用纯文本写 3 个自然段，不要 Markdown、不要编号，像朋友聊天一样自然。"
    )
    advice = await llm.chat([{"role": "user", "content": prompt}])

    row = db.execute(
        select(DailyAdvice).where(DailyAdvice.user_id == user.id, DailyAdvice.advice_date == d)
    ).scalar()
    if row:
        row.advice = advice
        row.refs_json = refs_json
    else:
        db.add(DailyAdvice(user_id=user.id, advice_date=d, advice=advice, refs_json=refs_json))
    db.commit()

    return {"intake": intake, "targets": targets, "advice": advice, "refs": refs}


@router.get("/advice")
def get_saved_advice(record_date: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    d = date.fromisoformat(record_date)
    row = db.execute(
        select(DailyAdvice).where(DailyAdvice.user_id == user.id, DailyAdvice.advice_date == d)
    ).scalar()
    refs = json.loads(row.refs_json) if (row and row.refs_json) else []
    return {"advice": row.advice if row else None, "refs": refs}
