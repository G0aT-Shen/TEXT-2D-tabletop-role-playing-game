"""阵营声望系统 — 三大阵营 + 被动奖励."""

from enum import Enum
from typing import Dict


class Faction(Enum):
    SHADOW = ("暗影之民", "🌑", "中立/务实 — 每回合恢复5%MP")
    DAWN = ("晨曦余烬", "☀️", "善良/牺牲 — 受致命伤时保留1HP（每章1次）")
    OBSERVER = ("观测者", "⚖️", "旁观/智慧 — 可看到检定DC和成功概率")

    def __init__(self, display_name: str, icon: str, description: str):
        self.display_name = display_name
        self.icon = icon
        self.description = description


# 阵营声望等级
FACTION_TIERS = {
    0: "中立",     # 0-49 点
    1: "友善",     # 50-149 点
    2: "尊敬",     # 150-299 点
    3: "崇敬",     # 300+ 点 → 获得被动
}

# 阵营被动奖励
FACTION_PASSIVES: Dict[str, dict] = {
    "SHADOW": {
        "name": "暗影亲和",
        "desc": "每回合战斗开始时恢复5%最大MP",
        "effect": {"regen_mp_pct": 5},
    },
    "DAWN": {
        "name": "晨曦加护",
        "desc": "受到致命伤害时保留1HP（每章可用1次）",
        "effect": {"death_save": True, "per_chapter": 1},
    },
    "OBSERVER": {
        "name": "洞悉之眼",
        "desc": "事件检定时可以看到DC和成功概率",
        "effect": {"show_dc": True},
    },
}


def get_faction_tier(reputation: int) -> int:
    """根据声望值返回等级（0-3）。"""
    if reputation >= 300:
        return 3
    if reputation >= 150:
        return 2
    if reputation >= 50:
        return 1
    return 0


def has_passive(reputation: int) -> bool:
    """是否已解锁阵营被动。"""
    return get_faction_tier(reputation) >= 3


# ── 建议的每个关键抉择的声望变化 ──
# 用于在事件 choice 中设置 faction change
FACTION_CHOICES = {
    # 第一章抉择: "拯救村民" vs "追击暗影狼"
    "c1_save_villagers": {"DAWN": 30},
    "c1_chase_wolf": {"SHADOW": 30},
    # 第二章抉择: "接受试炼" vs "强行突破"
    "c2_trial": {"OBSERVER": 30, "DAWN": 15},
    "c2_breakthrough": {"SHADOW": 30},
    # 通用: 保护他人 / 直接战斗 / 探索发现
    "protect_others": {"DAWN": 15},
    "direct_combat": {"SHADOW": 10},
    "seek_knowledge": {"OBSERVER": 15},
}
