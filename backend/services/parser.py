import json

from services import llm, matcher


DECONSTRUCT_PROMPT = """你是营养学助手。把用户口语化的饮食描述拆解成结构化 JSON。
只输出 JSON，不要输出任何解释、标点或多余文字。格式必须严格如下：
{"meal_type": "breakfast|lunch|dinner|snack", "items": [{"name": "食材名", "weight_g": 克数, "confidence": 0到1之间的小数}]}

规则：
1. 把复合菜拆成基础食材（例如"麻辣烫"要拆成肥牛卷、宽粉、汤底等）
2. 模糊量词按参考克重映射：一平勺油≈10克、一拳头米饭≈150克、一掌心肉≈100克、一小碗≈200克、一把≈30克
3. meal_type 只能是 breakfast / lunch / dinner / snack 之一
4. weight_g 是纯数字（不带单位），confidence 是 0 到 1 的小数
5. 只拆用户明确提到的食材，严禁添加用户没提到的任何食材或配料

示例：用户说"麻辣烫加了肥牛和宽粉"，只能拆出肥牛卷、宽粉、汤底，绝不能加"蔬菜""香菜"这类用户没说的东西。

用户输入："""


async def deconstruct_diet(text: str) -> dict:
    """口语化饮食 → 结构化原料清单（LLM 拆解 + 向量对齐）"""
    prompt = DECONSTRUCT_PROMPT + text
    raw = await llm.chat([{"role": "user", "content": prompt}], json_mode=True)
    data = json.loads(raw)

    for item in data.get("items", []):
        name, score = await matcher.match_food(item["name"])
        item["matched_name"] = name
        item["matched_score"] = score

    return data