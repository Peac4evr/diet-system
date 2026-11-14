import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database import SessionLocal
from models import Food
from services.embedding import embed_passages


def to_float(s):
    """把 '—'、'Tr'、空串等统一转成 0.0"""
    s = (s or "").strip()
    if s in ("", "—", "Tr", "-", "..."):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def import_foods(csv_path: str):
    with open(csv_path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    # 过滤空名 + 按名去重
    seen = set()
    cleaned = []
    for r in rows:
        name = (r.get("foodName") or "").strip()
        if name and name not in seen:
            seen.add(name)
            cleaned.append(r)

    names = [r["foodName"].strip() for r in cleaned]
    vectors = embed_passages(names)  # 1677 条，GPU 上十几秒

    with SessionLocal() as db:
        for r, vec in zip(cleaned, vectors):
            db.add(Food(
                name=r["foodName"].strip(),
                category=r["category"].strip(),
                calories=to_float(r["energyKCal"]),
                protein=to_float(r["protein"]),
                fat=to_float(r["fat"]),
                carbs=to_float(r["CHO"]),
                sodium=to_float(r["Na"]),
                embedding=vec,
            ))
        db.commit()

    print(f"导入完成，共 {len(cleaned)} 条")


if __name__ == "__main__":
    import_foods(sys.argv[1] if len(sys.argv) > 1 else "foods.csv")