"""成就系统 — 20个成就，覆盖战斗/探索/收集/里程碑."""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Any


@dataclass
class Achievement:
    id: str
    name: str
    description: str
    icon: str
    hidden: bool = False          # 隐藏成就（解锁前不显示描述）


# ── 成就定义 ──
ACHIEVEMENTS: List[Achievement] = [
    # 战斗类
    Achievement("first_blood", "初战告捷", "赢得第一场战斗", "⚔️"),
    Achievement("boss_slayer", "屠龙者", "击败第一章Boss暗影巨龙", "🐉"),
    Achievement("boss_hunter", "Boss猎手", "击败全部4个章节Boss", "🏆"),
    Achievement("flawless", "无伤之战", "一场战斗中不受任何伤害获胜", "🛡️", hidden=True),
    Achievement("close_call", "绝地反击", "HP低于10%时在战斗中获胜", "💀"),
    Achievement("escape_artist", "逃跑大师", "成功逃跑5次", "🏃"),
    Achievement("overkill", "一击致命", "单次攻击造成超过50点伤害", "💥"),
    Achievement("potion_master", "药水大师", "战斗中使用10次道具", "🧪"),

    # 探索/叙事类
    Achievement("chapter_one", "暗夜降临", "完成第一章", "🌅"),
    Achievement("chapter_two", "幽影迷途", "完成第二章", "🌫️"),
    Achievement("chapter_three", "深渊觉醒", "完成第三章", "🌑"),
    Achievement("chapter_four", "绝夜终章", "通关游戏", "☀️"),
    Achievement("truth_seeker", "真相追寻者", "在第四章中发现绝夜之神的真相", "📜", hidden=True),
    Achievement("both_paths", "两条道路", "分别以不同路线重玩同一章节", "🔀", hidden=True),

    # 收集/养成类
    Achievement("collector", "收藏家", "拥有传说级装备", "🟨"),
    Achievement("loaded", "富可敌国", "累计获得500金币", "💰"),
    Achievement("skill_master", "技能大师", "解锁5个进阶技能", "📜"),
    Achievement("level_five", "小有所成", "达到5级", "⬆️"),
    Achievement("faction_max", "阵营崇拜", "任一阵营声望达到崇敬", "🏛️"),
    Achievement("ng_plus", "新的旅程", "开始New Game+", "🔥"),
]

# 成就索引
ACHIEVEMENT_MAP: Dict[str, Achievement] = {a.id: a for a in ACHIEVEMENTS}


def check_achievements(player, trigger: str, data: Dict[str, Any] = None) -> List[str]:
    """检查并解锁成就。返回新解锁的成就ID列表。"""
    if data is None:
        data = {}
    unlocked = getattr(player, 'unlocked_achievements', set())
    newly_unlocked = []

    def unlock(aid: str) -> bool:
        if aid not in unlocked:
            unlocked.add(aid)
            newly_unlocked.append(aid)
            return True
        return False

    # ── 触发器分发 ──
    if trigger == "on_combat_win":
        unlock("first_blood")
        # 无伤
        if data.get("damage_taken", 999) == 0:
            unlock("flawless")
        # 低血量获胜
        if data.get("hp_percent", 100) < 10:
            unlock("close_call")
        # 道具使用次数
        if data.get("items_used", 0) >= 10:
            unlock("potion_master")

    elif trigger == "on_boss_kill":
        boss_name = data.get("boss_name", "")
        if "暗影巨龙" in boss_name:
            unlock("boss_slayer")
        # 所有Boss击败计数
        boss_count = data.get("boss_count", 0)
        if boss_count >= 4:
            unlock("boss_hunter")

    elif trigger == "on_hit":
        dmg = data.get("damage", 0)
        if dmg >= 50:
            unlock("overkill")

    elif trigger == "on_escape":
        escapes = data.get("escape_count", 0)
        if escapes >= 5:
            unlock("escape_artist")

    elif trigger == "on_chapter_complete":
        chapter = data.get("chapter", 0)
        if chapter == 1:
            unlock("chapter_one")
        elif chapter == 2:
            unlock("chapter_two")
        elif chapter == 3:
            unlock("chapter_three")
        elif chapter == 4:
            unlock("chapter_four")

    elif trigger == "on_truth_found":
        unlock("truth_seeker")

    elif trigger == "on_level_up":
        if player.level >= 5:
            unlock("level_five")

    elif trigger == "on_skill_unlock":
        advanced_count = data.get("advanced_count", 0)
        if advanced_count >= 5:
            unlock("skill_master")

    elif trigger == "on_equip_legendary":
        unlock("collector")

    elif trigger == "on_gold_collected":
        if data.get("total_gold", 0) >= 500:
            unlock("loaded")

    elif trigger == "on_faction_max":
        unlock("faction_max")

    elif trigger == "on_ng_plus":
        unlock("ng_plus")

    # 更新角色的成就集合
    if hasattr(player, 'unlocked_achievements'):
        player.unlocked_achievements = unlocked

    return newly_unlocked


def get_achievement_progress(player) -> dict:
    """获取成就进度摘要。"""
    unlocked = getattr(player, 'unlocked_achievements', set())
    total = len(ACHIEVEMENTS)
    done = len(unlocked)
    return {"total": total, "done": done, "percent": int(done / total * 100) if total > 0 else 0}
