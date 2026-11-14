import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete

from database import SessionLocal
from models import Guideline
from services.embedding import embed_passages

MD_PATH = Path(__file__).parent / "dietary_guidelines_2022.md"
SOURCE_DG = "《中国居民膳食指南（2022）》"


def parse_guidelines(text: str) -> list[dict]:
    """从《中国居民膳食指南（2022）》markdown 深解析：核心推荐 + 关键事实 + 各实践/知识小节。"""
    lines = text.split("\n")
    criterion = re.compile(r"^# (准则[一二三四五六七八九十]\s+.+)$")
    sub = re.compile(r"^\*\*（([一二三四五六七八九十]+)）(.+?)\*\*$")

    criteria = []
    cur = None
    for ln in lines:
        s = ln.strip()
        m = criterion.match(s)
        if m:
            if cur:
                criteria.append(cur)
            cur = {"title": m.group(1).strip(), "lines": []}
            continue
        if cur is not None:
            cur["lines"].append(s)
    if cur:
        criteria.append(cur)

    slices = []
    for c in criteria:
        core = [x.lstrip("●").strip() for x in c["lines"] if x.startswith("●")]
        if core:
            slices.append({"title": c["title"] + " · 核心推荐", "content": "\n".join(core)})

        facts = [x.lstrip("■").strip() for x in c["lines"] if x.startswith("■")]
        if facts:
            slices.append({"title": c["title"] + " · 关键事实", "content": "\n".join(facts)})

        for i, s in enumerate(c["lines"]):
            m = sub.match(s)
            if not m:
                continue
            st = "（" + m.group(1) + "）" + m.group(2)
            body = []
            j = i + 1
            while j < len(c["lines"]):
                t = c["lines"][j]
                if sub.match(t) or t.startswith("**【") or t.startswith("■") or t.startswith("●"):
                    break
                if (t and not t.startswith("<img") and not t.startswith("![")
                        and not re.match(r"^(表|图)\d", t) and not t.startswith("**")
                        and not t.startswith("作者") and not t.startswith("点此下载")):
                    body.append(t)
                j += 1
            content = "\n".join(body).strip()
            if content and len(content) >= 15:
                slices.append({"title": c["title"] + " · " + st, "content": content})

    return slices


def import_guidelines():
    text = MD_PATH.read_text(encoding="utf-8")
    items = parse_guidelines(text)
    for it in items:
        it["source"] = SOURCE_DG
    if not items:
        raise SystemExit("未能从 markdown 中解析出准则，请检查文件格式")

    # 附加 WHO 健康膳食建议
    who_path = Path(__file__).parent / "who_guidelines.json"
    who_items = []
    if who_path.exists():
        who_items = json.loads(who_path.read_text(encoding="utf-8"))
        items.extend(who_items)

    texts = [it["title"] + "：" + it["content"] for it in items]
    vectors = embed_passages(texts)

    with SessionLocal() as db:
        db.execute(delete(Guideline))
        for it, vec in zip(items, vectors):
            db.add(Guideline(title=it["title"], content=it["content"],
                             source=it.get("source", SOURCE_DG), embedding=vec))
        db.commit()

    print(f"文献导入完成，共 {len(items)} 条（膳食指南 {len(items) - len(who_items)} 条 + WHO {len(who_items)} 条）")


if __name__ == "__main__":
    import_guidelines()
