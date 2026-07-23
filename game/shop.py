"""商店系统 — 神秘商人在章节过渡时出现."""

from typing import List, Dict, Optional
from dataclasses import dataclass
import random


@dataclass
class ShopItem:
    """商店中的一件商品。"""
    id: str
    name: str
    description: str
    price: int             # 金币价格
    currency: str = "gold"  # gold / shadow_essence
    item_type: str = "consumable"  # consumable / equipment / info
    stock: int = 1          # 库存（-1表示无限）
    data: dict = None       # 附加数据

    def __post_init__(self):
        if self.data is None:
            self.data = {}


# ── 消耗品商店物品 ──
SHOP_CONSUMABLES: List[ShopItem] = [
    ShopItem("potion_small", "小治疗药水", "回复30HP", 25, stock=-1,
             data={"item_name": "急救包"}),
    ShopItem("potion_large", "大治疗药水", "回复80HP", 60, stock=-1,
             data={"item_name": "大治疗药水"}),
    ShopItem("holy_water", "圣水", "回复30HP并驱散负面状态", 50, stock=-1,
             data={"item_name": "圣水"}),
    ShopItem("dawn_badge", "晨曦徽章", "回复40HP+20MP", 80, stock=3,
             data={"item_name": "晨曦徽章"}),
    ShopItem("hunting_tool", "狩猎工具", "造成30伤害+减速", 40, stock=-1,
             data={"item_name": "狩猎工具"}),
    ShopItem("void_cloak", "虚空披风", "完全回复HP", 150, stock=1,
             data={"item_name": "虚空披风"}),
    ShopItem("dagger", "附魔匕首", "造成40无视防御伤害", 70, stock=2,
             data={"item_name": "附魔匕首"}),
    ShopItem("crossbow", "破魔之弩", "造成60伤害", 100, stock=1,
             data={"item_name": "破魔之弩"}),
    ShopItem("night_cloak", "暗夜斗篷", "本回合完全回避", 120, stock=1,
             data={"item_name": "暗夜斗篷"}),
]

# ── 装备商店（按章节解锁不同等级装备）──
def get_equipment_shop_items(chapter_id: int, player_class: str) -> List[ShopItem]:
    """根据章节和玩家职业生成装备商店物品。"""
    from .equipment import generate_equipment, Rarity, EquipmentSlot
    items = []
    # 稀有度随章节提升
    rarity_pool = {
        1: [Rarity.COMMON, Rarity.RARE],
        2: [Rarity.COMMON, Rarity.RARE],
        3: [Rarity.RARE, Rarity.EPIC],
        4: [Rarity.RARE, Rarity.EPIC, Rarity.LEGENDARY],
    }
    rarities = rarity_pool.get(chapter_id, [Rarity.COMMON, Rarity.RARE])
    # 价格系数
    price_by_rarity = {"COMMON": 50, "RARE": 120, "EPIC": 250, "LEGENDARY": 500}

    for _ in range(3):
        rarity = random.choice(rarities)
        slot = random.choice([EquipmentSlot.WEAPON, EquipmentSlot.ARMOR, EquipmentSlot.ACCESSORY_1])
        eq = generate_equipment(player_class, preferred_slot=slot, rarity=rarity)
        if eq:
            price = price_by_rarity.get(eq.rarity.name, 100)
            items.append(ShopItem(
                id=f"eq_{eq.name}_{random.randint(1000,9999)}",
                name=eq.full_name,
                description=f"攻+{eq.attack} 防+{eq.defense}",
                price=price,
                currency="gold",
                item_type="equipment",
                data={"equipment": eq},
            ))
    return items

# ── 暗影精华商店 ──
SHADOW_ESSENCE_ITEMS: List[ShopItem] = [
    ShopItem("se_skill_point", "技能之书", "获得1个技能点", 5, currency="shadow_essence",
             item_type="info", data={"reward": "skill_point"}),
    ShopItem("se_attribute", "属性秘药", "获得2点自由属性", 3, currency="shadow_essence",
             item_type="info", data={"reward": "attr_points", "amount": 2}),
    ShopItem("se_legendary", "传说锻造", "随机获得一件传说装备", 8, currency="shadow_essence",
             item_type="info", data={"reward": "legendary_item"}),
    ShopItem("se_full_heal", "生命之泉", "全队完全回复", 2, currency="shadow_essence",
             item_type="info", data={"reward": "full_heal"}),
]


def can_afford(item: ShopItem, gold: int, shadow_essence: int) -> bool:
    """检查是否能购买。"""
    if item.currency == "gold":
        return gold >= item.price
    elif item.currency == "shadow_essence":
        return shadow_essence >= item.price
    return False
