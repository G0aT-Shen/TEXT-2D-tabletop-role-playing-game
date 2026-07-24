"""装备系统 — 武器/护甲/饰品、稀有度、掉落池."""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List


class EquipmentSlot(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY_1 = "accessory_1"
    ACCESSORY_2 = "accessory_2"


class Rarity(Enum):
    COMMON = ("普通", "⬜", 1.0)        # 白
    RARE = ("精良", "🟦", 0.35)         # 蓝
    EPIC = ("稀有", "🟪", 0.12)          # 紫
    LEGENDARY = ("传说", "🟨", 0.03)     # 金

    def __init__(self, display_name: str, icon: str, weight: float):
        self.display_name = display_name
        self.icon = icon
        self.weight = weight

    @classmethod
    def roll(cls) -> "Rarity":
        """按权重随机生成稀有度。"""
        total = sum(r.weight for r in cls)
        r = random.random() * total
        cumulative = 0
        for rarity in cls:
            cumulative += rarity.weight
            if r <= cumulative:
                return rarity
        return cls.COMMON

    @property
    def stat_multiplier(self) -> float:
        """属性缩放系数: 普通1.0 / 精良1.3 / 稀有1.6 / 传说2.0"""
        return {Rarity.COMMON: 1.0, Rarity.RARE: 1.3, Rarity.EPIC: 1.6, Rarity.LEGENDARY: 2.0}[self]

    @property
    def affix_count(self) -> int:
        """词缀数量: 普通0 / 精良1 / 稀有2 / 传说3"""
        return {Rarity.COMMON: 0, Rarity.RARE: 1, Rarity.EPIC: 2, Rarity.LEGENDARY: 3}[self]


# ══════════════════════════════════════════════════
# 词缀池
# ══════════════════════════════════════════════════

AFFIX_POOL = [
    # (名称, 效果描述, 效果实现)
    {"name": "嗜血", "desc": "击杀回复 8% HP",
     "effect": {"on_kill_heal_pct": 8}},
    {"name": "暗影亲和", "desc": "暗杀类技能伤害+25%",
     "effect": {"assassin_skill_dmg_pct": 25}},
    {"name": "圣光裁决", "desc": "对恶魔伤害+40%",
     "effect": {"demon_dmg_pct": 40}},
    {"name": "希望之光", "desc": "每回合回复 3 HP",
     "effect": {"regen_hp": 3}},
    {"name": "精准", "desc": "命中率+15%",
     "effect": {"hit_pct": 15}},
    {"name": "荆棘", "desc": "受击时反弹 5 伤害",
     "effect": {"thorns": 5}},
    {"name": "奥术充能", "desc": "技能MP消耗-20%",
     "effect": {"mp_cost_reduce_pct": 20}},
    {"name": "破甲", "desc": "攻击忽视 4 防御",
     "effect": {"armor_pen": 4}},
    {"name": "不屈", "desc": "HP低于30%时获得15%减伤",
     "effect": {"low_hp_dmg_reduce_pct": 15}},
    {"name": "魔力涌动", "desc": "最大MP+20",
     "effect": {"max_mp_bonus": 20}},
    {"name": "巨力", "desc": "攻击力+6",
     "effect": {"attack_bonus": 6}},
    {"name": "铁壁", "desc": "防御力+8",
     "effect": {"defense_bonus": 8}},
    {"name": "幸运之星", "desc": "幸运+4",
     "effect": {"luck_bonus": 4}},
    {"name": "吸血", "desc": "造成伤害的15%转化为HP",
     "effect": {"lifesteal_pct": 15}},
    {"name": "先发制人", "desc": "首回合行动次数+1",
     "effect": {"first_turn_extra": True}},
    {"name": "重生", "desc": "每场战斗首次死亡时复活，保留30%HP",
     "effect": {"revive_once": True}},
]

# 职业专属词缀
CLASS_AFFIXES = {
    "WARRIOR": ["嗜血", "巨力", "不屈", "荆棘"],
    "ASSASSIN": ["暗影亲和", "精准", "先发制人", "吸血"],
    "KNIGHT": ["铁壁", "圣光裁决", "重生", "巨力"],
    "PRIEST": ["圣光裁决", "希望之光", "魔力涌动", "奥术充能"],
    "MAGE": ["魔力涌动", "奥术充能", "幸运之星", "暗影亲和"],
}

AFFIX_MAP = {a["name"]: a for a in AFFIX_POOL}


# ══════════════════════════════════════════════════
# 装备模板
# ══════════════════════════════════════════════════

@dataclass
class Equipment:
    """一件装备。"""
    name: str
    slot: EquipmentSlot
    rarity: Rarity
    base_attack: int = 0       # 武器攻击
    base_defense: int = 0      # 护甲防御
    stat_bonuses: Dict[str, int] = field(default_factory=dict)  # {"str": 2, "dex": 1, ...}
    affixes: List[Dict] = field(default_factory=list)
    class_restriction: Optional[str] = None  # 职业限制

    @property
    def full_name(self) -> str:
        return f"{self.rarity.icon} {self.name}"

    @property
    def attack(self) -> int:
        """经稀有度缩放后的攻击力。"""
        return int(self.base_attack * self.rarity.stat_multiplier)

    @property
    def defense(self) -> int:
        """经稀有度缩放后的防御力。"""
        return int(self.base_defense * self.rarity.stat_multiplier)

    def get_affix_description(self) -> List[str]:
        return [f"{a['name']}: {a['desc']}" for a in self.affixes]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "slot": self.slot.value,
            "rarity": self.rarity.name,
            "base_attack": self.base_attack,
            "base_defense": self.base_defense,
            "stat_bonuses": self.stat_bonuses,
            "affix_names": [a["name"] for a in self.affixes],
            "class_restriction": self.class_restriction,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Equipment":
        affixes = [AFFIX_MAP[n] for n in data.get("affix_names", []) if n in AFFIX_MAP]
        return cls(
            name=data["name"],
            slot=EquipmentSlot(data["slot"]),
            rarity=Rarity[data["rarity"]],
            base_attack=data.get("base_attack", 0),
            base_defense=data.get("base_defense", 0),
            stat_bonuses=data.get("stat_bonuses", {}),
            affixes=affixes,
            class_restriction=data.get("class_restriction"),
        )


# ══════════════════════════════════════════════════
# 装备生成器
# ══════════════════════════════════════════════════

WEAPON_TEMPLATES = [
    {"name": "暗夜之刃", "slot": EquipmentSlot.WEAPON, "base_attack": 14, "class_restriction": "ASSASSIN",
     "stat_bonuses": {"dex": 2}},
    {"name": "黎明圣锤", "slot": EquipmentSlot.WEAPON, "base_attack": 18, "class_restriction": "KNIGHT",
     "stat_bonuses": {"str": 2}},
    {"name": "战士重剑", "slot": EquipmentSlot.WEAPON, "base_attack": 16, "class_restriction": "WARRIOR",
     "stat_bonuses": {"str": 3}},
    {"name": "圣光权杖", "slot": EquipmentSlot.WEAPON, "base_attack": 12, "class_restriction": "PRIEST",
     "stat_bonuses": {"wis": 2, "int": 1}},
    {"name": "奥术法杖", "slot": EquipmentSlot.WEAPON, "base_attack": 10, "class_restriction": "MAGE",
     "stat_bonuses": {"int": 3}},
    # 通用武器
    {"name": "猎鹰匕首", "slot": EquipmentSlot.WEAPON, "base_attack": 12, "stat_bonuses": {"dex": 1, "luk": 1}},
    {"name": "旅者长剑", "slot": EquipmentSlot.WEAPON, "base_attack": 14, "stat_bonuses": {"str": 1}},
    {"name": "守卫短弓", "slot": EquipmentSlot.WEAPON, "base_attack": 13, "stat_bonuses": {"dex": 1, "str": 1}},
]

ARMOR_TEMPLATES = [
    {"name": "暗影斗篷", "slot": EquipmentSlot.ARMOR, "base_defense": 10, "class_restriction": "ASSASSIN",
     "stat_bonuses": {"dex": 2}},
    {"name": "圣殿板甲", "slot": EquipmentSlot.ARMOR, "base_defense": 18, "class_restriction": "KNIGHT",
     "stat_bonuses": {"str": 1}},
    {"name": "战斗锁甲", "slot": EquipmentSlot.ARMOR, "base_defense": 14, "class_restriction": "WARRIOR",
     "stat_bonuses": {"str": 1}},
    {"name": "圣典长袍", "slot": EquipmentSlot.ARMOR, "base_defense": 10, "class_restriction": "PRIEST",
     "stat_bonuses": {"wis": 2}},
    {"name": "奥术斗篷", "slot": EquipmentSlot.ARMOR, "base_defense": 8, "class_restriction": "MAGE",
     "stat_bonuses": {"int": 2}},
    # 通用护甲
    {"name": "皮质护胸", "slot": EquipmentSlot.ARMOR, "base_defense": 10},
    {"name": "锁子甲", "slot": EquipmentSlot.ARMOR, "base_defense": 13},
]

ACCESSORY_TEMPLATES = [
    {"name": "猎人护符", "slot": EquipmentSlot.ACCESSORY_1, "base_attack": 6, "base_defense": 4,
     "stat_bonuses": {"dex": 1}},
    {"name": "圣徒挂坠", "slot": EquipmentSlot.ACCESSORY_1, "base_defense": 8,
     "stat_bonuses": {"wis": 2}},
    {"name": "指挥官徽章", "slot": EquipmentSlot.ACCESSORY_1, "base_attack": 4, "base_defense": 6,
     "stat_bonuses": {"cha": 2}},
    {"name": "贤者戒指", "slot": EquipmentSlot.ACCESSORY_1, "base_attack": 4,
     "stat_bonuses": {"int": 2}},
    {"name": "幸运兔脚", "slot": EquipmentSlot.ACCESSORY_1, "base_defense": 2,
     "stat_bonuses": {"luk": 3}},
    {"name": "力量手环", "slot": EquipmentSlot.ACCESSORY_1, "base_attack": 8,
     "stat_bonuses": {"str": 2}},
]


def _pick_affixes(count: int, class_name: str) -> List[Dict]:
    """选取 count 个词缀，优先职业专属。"""
    picked = []
    pool = list(AFFIX_POOL)
    # 职业专属词缀权重翻倍
    class_prefer = set(CLASS_AFFIXES.get(class_name, []))
    weighted = []
    for a in pool:
        w = 3.0 if a["name"] in class_prefer else 1.0
        weighted.extend([a] * int(w * 10))
    while len(picked) < min(count, len(pool)):
        affix = random.choice(weighted)
        if affix["name"] not in [p["name"] for p in picked]:
            picked.append(affix)
            weighted = [candidate for candidate in weighted if candidate["name"] != affix["name"]]
    return picked


def generate_equipment(character_class: str, preferred_slot: Optional[EquipmentSlot] = None,
                       rarity: Optional[Rarity] = None) -> Equipment:
    """生成一件随机装备。

    Args:
        character_class: 角色职业名 (e.g. "WARRIOR")
        preferred_slot: 优先槽位，None则随机
        rarity: 指定稀有度，None则按权重随机

    Returns:
        Equipment 实例
    """
    if rarity is None:
        rarity = Rarity.roll()

    # 选择槽位
    if preferred_slot:
        slot = preferred_slot
    else:
        roll = random.random()
        if roll < 0.45:
            slot = EquipmentSlot.WEAPON
        elif roll < 0.80:
            slot = EquipmentSlot.ARMOR
        else:
            slot = random.choice([EquipmentSlot.ACCESSORY_1, EquipmentSlot.ACCESSORY_2])

    # 选择模板
    if slot == EquipmentSlot.WEAPON:
        pool = WEAPON_TEMPLATES
    elif slot == EquipmentSlot.ARMOR:
        pool = ARMOR_TEMPLATES
    else:
        pool = ACCESSORY_TEMPLATES

    # 优先匹配职业
    class_matched = [t for t in pool if t.get("class_restriction") == character_class]
    generic = [t for t in pool if not t.get("class_restriction")]
    candidates = class_matched + generic
    if not candidates:
        candidates = pool

    tmpl = random.choice(candidates)

    # 生成词缀
    affixes = _pick_affixes(rarity.affix_count, character_class)

    return Equipment(
        name=tmpl["name"],
        slot=slot,
        rarity=rarity,
        base_attack=tmpl.get("base_attack", 0),
        base_defense=tmpl.get("base_defense", 0),
        stat_bonuses=dict(tmpl.get("stat_bonuses", {})),
        affixes=affixes,
        class_restriction=tmpl.get("class_restriction"),
    )


def generate_boss_loot(character_class: str) -> Equipment:
    """Boss掉落: 保底稀有以上。"""
    rarity = Rarity.roll()
    while rarity == Rarity.COMMON:
        rarity = Rarity.roll()
    return generate_equipment(character_class, rarity=rarity)


def generate_legendary(character_class: str) -> Equipment:
    """生成一件传说装备（章节通关奖励）。"""
    return generate_equipment(character_class, rarity=Rarity.LEGENDARY)
