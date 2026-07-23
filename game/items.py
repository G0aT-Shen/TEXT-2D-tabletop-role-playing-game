"""道具系统 — 道具定义、效果、使用."""

from typing import Dict, List, Optional

# 所有道具定义：{道具名: {name, desc, effect}}
ITEM_DB: Dict[str, dict] = {
    "圣水": {
        "name": "圣水",
        "desc": "受过祝福的圣水，恢复30HP并驱散负面状态",
        "effect": {"heal": 30, "cure": True},
    },
    "祖传怀表": {
        "name": "祖传怀表",
        "desc": "能短暂扭曲时间的怀表，下回合行动次数+1",
        "effect": {"buff": "extra_action"},
    },
    "急救包": {
        "name": "急救包",
        "desc": "标准医疗用品，恢复50HP",
        "effect": {"heal": 50},
    },
    "附魔匕首": {
        "name": "附魔匕首",
        "desc": "附有魔法的匕首，对敌人造成40点无视防御伤害",
        "effect": {"damage": 40},
    },
    "暗夜斗篷": {
        "name": "暗夜斗篷",
        "desc": "融入暗影的斗篷，本回合完全回避敌人攻击",
        "effect": {"buff": "dodge_all"},
    },
    "圣殿之剑": {
        "name": "圣殿之剑",
        "desc": "圣骑士的遗物，对恶魔伤害×3（一次性使用）",
        "effect": {"damage_mult": 3.0},
    },
    "破魔之弩": {
        "name": "破魔之弩",
        "desc": "专门克制魔物的弩，造成60点伤害",
        "effect": {"damage": 60},
    },
    "黎明之刃": {
        "name": "黎明之刃",
        "desc": "承载黎明之光的神器，造成80点伤害",
        "effect": {"damage": 80},
    },
    "虚空披风": {
        "name": "虚空披风",
        "desc": "用虚空能量编织的披风，恢复全部HP",
        "effect": {"heal_pct": 100},
    },
    "大治疗药水": {
        "name": "大治疗药水",
        "desc": "强力治疗药水，恢复80HP",
        "effect": {"heal": 80},
    },
    "晨曦徽章": {
        "name": "晨曦徽章",
        "desc": "带有晨曦之力的徽章，恢复40HP和20MP",
        "effect": {"heal": 40, "mp_restore": 20},
    },
    "晨曦碎片(蓝)": {
        "name": "晨曦碎片(蓝)",
        "desc": "散发蓝色光芒的碎片，全属性+1持续3回合",
        "effect": {"buff": "all_stats", "buff_value": 1, "duration": 3},
    },
    "狩猎工具": {
        "name": "狩猎工具",
        "desc": "老猎人特制的工具，对敌人造成30点伤害并使其减速",
        "effect": {"damage": 30, "debuff": "slow"},
    },
}

# 初始道具（最多持有10个）
INITIAL_ITEMS: List[dict] = [
    ITEM_DB["急救包"],
    ITEM_DB["圣水"],
]


def get_item(name_or_dict) -> dict:
    """获取道具定义。支持名称字符串或已有字典。"""
    if isinstance(name_or_dict, dict):
        return name_or_dict
    return ITEM_DB.get(name_or_dict, {"name": name_or_dict, "desc": "", "effect": {}})


def create_item(item_name: str) -> Optional[dict]:
    """根据名称创建道具副本。"""
    tmpl = ITEM_DB.get(item_name)
    if tmpl is None:
        return None
    return dict(tmpl)  # 浅拷贝足够


def use_item(item: dict, target, combat_log: List[str] = None, enemy=None) -> str:
    """使用道具，返回使用结果文本。

    Args:
        item: 道具数据字典
        target: 使用道具的角色（通常是玩家自身）
        combat_log: 战斗日志列表
        enemy: 敌方对象（伤害类道具需要）
    """
    if combat_log is None:
        combat_log = []

    effect = item.get("effect", {})
    name = item.get("name", "道具")
    result_parts = [f"🎒 使用: {name}"]

    # 治疗效果
    heal = effect.get("heal", 0)
    if heal > 0:
        old_hp = target.hp
        target.hp = min(target.stats.max_hp, target.hp + heal)
        actual = target.hp - old_hp
        result_parts.append(f"回复 {actual} HP")

    heal_pct = effect.get("heal_pct", 0)
    if heal_pct > 0:
        target.hp = target.stats.max_hp
        result_parts.append("HP全回复！")

    mp_restore = effect.get("mp_restore", 0)
    if mp_restore > 0:
        target.mp = min(target.stats.max_mp, target.mp + mp_restore)
        result_parts.append(f"回复 {mp_restore} MP")

    # 伤害效果（对敌人造成直接伤害）
    damage = effect.get("damage", 0)
    if damage > 0 and enemy:
        enemy.hp = max(0, enemy.hp - damage)
        result_parts.append(f"对 {enemy.name} 造成 {damage} 点伤害")

    # 伤害倍率（一次性伤害加成）
    damage_mult = effect.get("damage_mult", 0)
    if damage_mult > 0 and enemy:
        # 使用目标的攻击力作为基础伤害
        base = getattr(target, 'attack_bonus', 5) + 5
        dmg = int(base * damage_mult)
        enemy.hp = max(0, enemy.hp - dmg)
        result_parts.append(f"对 {enemy.name} 造成 {dmg} 点伤害(x{damage_mult})")

    # 减益效果
    debuff = effect.get("debuff")
    if debuff and enemy:
        effect_map = {"slow": "减速"}
        debuff_name = effect_map.get(debuff, debuff)
        enemy.status_effects.append({"type": debuff, "duration": 2})
        result_parts.append(f"{enemy.name} 受到{debuff_name}效果")

    return " | ".join(result_parts)
