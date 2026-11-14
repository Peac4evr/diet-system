from datetime import date

from sqlalchemy import String, Float, Integer, Date, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(200))
    token: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    name: Mapped[str] = mapped_column(String(50), default="")
    gender: Mapped[str] = mapped_column(String(10), default="")
    age: Mapped[int] = mapped_column(Integer, default=0)
    height_cm: Mapped[float] = mapped_column(Float, default=0)
    weight_kg: Mapped[float] = mapped_column(Float, default=0)
    activity_level: Mapped[str] = mapped_column(String(20), default="moderate")
    goal: Mapped[str] = mapped_column(String(20), default="maintain")
    bmr: Mapped[float] = mapped_column(Float, default=0)
    tdee: Mapped[float] = mapped_column(Float, default=0)
    target_calories: Mapped[float] = mapped_column(Float, default=0)
    target_protein_g: Mapped[float] = mapped_column(Float, default=0)
    target_fat_g: Mapped[float] = mapped_column(Float, default=0)
    target_carbs_g: Mapped[float] = mapped_column(Float, default=0)


class Food(Base):
    __tablename__ = "foods"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(50))
    calories: Mapped[float] = mapped_column(Float)
    protein: Mapped[float] = mapped_column(Float)
    fat: Mapped[float] = mapped_column(Float)
    carbs: Mapped[float] = mapped_column(Float)
    sodium: Mapped[float] = mapped_column(Float)
    embedding: Mapped[list] = mapped_column(Vector(1024))


class DietRecord(Base):
    __tablename__ = "diet_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    record_date: Mapped[date] = mapped_column(Date)
    meal_type: Mapped[str] = mapped_column(String(20))
    raw_text: Mapped[str] = mapped_column(Text)
    structured_json: Mapped[str] = mapped_column(Text)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    total_calories: Mapped[float] = mapped_column(Float, default=0)
    total_protein_g: Mapped[float] = mapped_column(Float, default=0)
    total_fat_g: Mapped[float] = mapped_column(Float, default=0)
    total_carbs_g: Mapped[float] = mapped_column(Float, default=0)
    total_sodium_mg: Mapped[float] = mapped_column(Float, default=0)


class DietRecordItem(Base):
    __tablename__ = "diet_record_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("diet_records.id"))
    food_name: Mapped[str] = mapped_column(String(100))
    matched_food_id: Mapped[int | None] = mapped_column(ForeignKey("foods.id"), nullable=True)
    weight_g: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, default=0)
    calories: Mapped[float] = mapped_column(Float, default=0)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    fat_g: Mapped[float] = mapped_column(Float, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0)
    sodium_mg: Mapped[float] = mapped_column(Float, default=0)


class Guideline(Base):
    __tablename__ = "guidelines"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list] = mapped_column(Vector(1024))
    source: Mapped[str] = mapped_column(String(100))


class DailyAdvice(Base):
    __tablename__ = "daily_advice"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    advice_date: Mapped[date] = mapped_column(Date)
    advice: Mapped[str] = mapped_column(Text)
    refs_json: Mapped[str | None] = mapped_column(Text, nullable=True)