import asyncio
from services import parser

SENTENCE = ("中午吃了一碗加了肥牛卷、宽粉、鸡胸肉和洋芋的麻辣烫，"
            "配半碗米饭、一个西红柿、半个红薯、一把白菜、一个花卷和两个鸡翅，"
            "喝了杯酸奶，炒菜时放了点油和盐，还蒸了个地瓜")

async def main():
    result = await parser.deconstruct_diet(SENTENCE)
    print("meal_type:", result.get("meal_type"))
    for it in result.get("items", []):
        print(f"{it['name']:<10} {it['weight_g']}g   ->   {it['matched_name']}")

asyncio.run(main())