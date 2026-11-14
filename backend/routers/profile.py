from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from deps import get_db, get_current_user
from models import User
from services import nutrition

router = APIRouter()


class ProfileIn(BaseModel):
    name: str
    gender: str
    age: int
    height_cm: float
    weight_kg: float
    activity_level: str
    goal: str


def profile_public(u: User):
    """只返回安全字段，绝不返回 password_hash 和 token"""
    return {
        "id": u.id, "username": u.username, "name": u.name,
        "gender": u.gender, "age": u.age, "height_cm": u.height_cm,
        "weight_kg": u.weight_kg, "activity_level": u.activity_level, "goal": u.goal,
        "bmr": u.bmr, "tdee": u.tdee,
        "target_calories": u.target_calories, "target_protein_g": u.target_protein_g,
        "target_fat_g": u.target_fat_g, "target_carbs_g": u.target_carbs_g,
    }


@router.post("/profile")
def save_profile(p: ProfileIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    bmr = nutrition.calc_bmr(p.gender, p.weight_kg, p.height_cm, p.age)
    tdee = bmr * nutrition.ACTIVITY[p.activity_level]
    t = nutrition.calc_targets(tdee, p.goal)
    user.name = p.name
    user.gender = p.gender
    user.age = p.age
    user.height_cm = p.height_cm
    user.weight_kg = p.weight_kg
    user.activity_level = p.activity_level
    user.goal = p.goal
    user.bmr = round(bmr, 2)
    user.tdee = round(tdee, 2)
    user.target_calories = t["calories"]
    user.target_protein_g = t["protein_g"]
    user.target_fat_g = t["fat_g"]
    user.target_carbs_g = t["carbs_g"]
    db.commit()
    db.refresh(user)
    return profile_public(user)


@router.get("/profile")
def get_profile(user: User = Depends(get_current_user)):
    return profile_public(user)