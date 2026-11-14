import re

from sqlalchemy import select

from database import SessionLocal
from models import Food
from services import llm, rag


MANUAL_ALIASES = {
    "西红柿": "番茄",
    "蛋": "鸡蛋",
    "油": "花生油",
    "盐": "食盐",
    "糖": "白糖",
}


NORMALIZE_PROMPT = """把口语食材名翻译成"规范标准名"（成分表会用的正式叫法）。
规则：
1. 去掉形状/做法/分量的字（卷、丝、块、片、丁），保留部位和品类字
2. 用规范全称而不是简称：白菜→大白菜、西红柿→番茄
3. 例子：肥牛卷→牛肉、宽粉→粉条、鸡胸肉→鸡胸、白菜→大白菜
4. 如果它不是具体食材（如汤底、蘸料、酱汁这类复合物），只回复：无
只回复那个词本身，不要解释。

食材名："""


PICK_PROMPT = """把口语食材"{query}"匹配到下面候选里最接近的"数据库标准食物名"。
规则：
1. 只选和它是"同一种食物"的。切法/形态不同（片、丝、卷、块）营养一样，算同一种：肥牛卷=牛肉、牛肉片=牛肉、鸡胸肉=鸡胸
2. "加工方式"不同（脱水、油炸、腌制、熏烤）会改变营养，不算同一种：白菜≠白菜（脱水）
3. "品种"不同也不算：紫薯≠甘薯（红心）、白菜≠娃娃菜、火鸡≠鸡（"火鸡腿肉"≠"鸡腿肉"、"火鸡胸脯肉"≠"鸡胸脯肉"）
4. 多个候选都像时，优先选带"（代表值）"或"（均值）"的
5. 如果是复合物/底料/蘸料（汤底、蘸料、酱汁），或没有同一种，回"无匹配"
候选：
{candidates}

只回复那个标准名本身（原样照抄），或"无匹配"。"""


_alias_cache = None


def _build_alias_map():
    m = dict(MANUAL_ALIASES)
    with SessionLocal() as db:
        for (name,) in db.execute(select(Food.name)).all():
            for grp in re.findall(r"［([^］]+)］", name):
                for a in re.split(r"[、，,;；]", grp):
                    a = a.strip()
                    if a:
                        m.setdefault(a, name)
    return m


def _get_alias_map():
    global _alias_cache
    if _alias_cache is None:
        _alias_cache = _build_alias_map()
    return _alias_cache


def _exact(name):
    with SessionLocal() as db:
        return db.execute(select(Food.name).where(Food.name == name)).scalar()


def _retrieve_candidates(query: str, normalized: str, top_k: int = 20) -> list[str]:
    """用原始词 + 干净词，向量 + LIKE + 别名，三路捞候选"""
    cands = {}
    for food, _ in rag.search_food(query, top_k=8):
        cands[food.name] = 1
    for food, _ in rag.search_food(normalized, top_k=8):
        cands[food.name] = 1
    aliases = _get_alias_map()
    for k, v in aliases.items():
        if query in k or k in query or normalized in k or k in normalized:
            cands[v] = 1
    with SessionLocal() as db:
        for (n,) in db.execute(
            select(Food.name).where(Food.name.like(f"%{normalized}%")).limit(30)
        ).all():
            cands[n] = 1
    return list(cands.keys())[:top_k]


async def _llm_pick(query: str, candidates: list[str]):
    if not candidates:
        return None, None
    numbered = "\n".join(f"{i+1}. {n}" for i, n in enumerate(candidates))
    prompt = PICK_PROMPT.format(query=query, candidates=numbered)
    reply = (await llm.chat([{"role": "user", "content": prompt}])).strip()
    if "无匹配" in reply:
        return None, None

    # 1) 先精确匹配（LLM 原样返回的候选名）
    for n in candidates:
        if n == reply:
            return n, 1.0
    # 2) 再找"回复是候选的子串"（LLM 回了简称，如"大白菜"，候选是"大白菜（代表值）"）
    for n in candidates:
        if reply in n:
            return n, 1.0
    # 3) 反向（候选是回复的子串）
    for n in candidates:
        if n in reply:
            return n, 1.0
    return None, None

async def match_food(query: str):
    aliases = _get_alias_map()
    if query in aliases:
        return aliases[query], 1.0
    f = _exact(query)
    if f:
        return f, 1.0
    normalized = (await llm.chat([{"role": "user", "content": NORMALIZE_PROMPT + query}])).strip()
    if normalized == "无":
        return None, None
    candidates = _retrieve_candidates(query, normalized)
    return await _llm_pick(query, candidates)