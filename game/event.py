"""事件系统 — 剧情选择、骰子检定、战斗触发."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Callable, Dict, Any, Tuple

from .dice import Dice, RollResult


class EventType(Enum):
    STORY = "story"         # 纯剧情
    CHOICE = "choice"       # 多选项
    DICE_CHECK = "dice"     # 骰子检定
    COMBAT = "combat"       # 战斗
    BOSS = "boss"           # Boss战
    TRAIN = "train"         # 列车事件（过渡）


@dataclass
class Choice:
    """事件中的一个选项。"""
    text: str                          # 选项文本
    result_text: str                   # 执行后的描述
    check_type: Optional[str] = None   # "str"|"dex"|"int"|"wis"|"cha"|"luck"
    dc: int = 10                       # 难度等级
    success_text: str = ""             # 成功文本
    failure_text: str = ""             # 失败文本
    critical_success_text: str = ""    # 大成功文本
    critical_failure_text: str = ""    # 大失败文本
    hp_change: int = 0                 # HP变化
    mp_change: int = 0                 # MP变化
    xp_reward: int = 0                 # 经验奖励
    item_reward: Optional[str] = None  # 道具奖励
    next_event: Optional[str] = None   # 跳转到的事件ID
    flags_set: Dict[str, Any] = field(default_factory=dict)  # 设置的标记
    trigger_combat: bool = False       # 是否触发战斗
    combat_enemy: Optional[str] = None # 战斗敌人ID
    faction_reputation: Dict[str, int] = field(default_factory=dict)  # 阵营声望变化
    dawn_shard_reward: int = 0         # 晨曦碎片奖励
    gold_reward: int = 0               # 金币奖励
    shadow_essence: int = 0            # 暗影精华奖励


@dataclass
class Event:
    """游戏事件。"""
    event_id: str
    title: str
    description: str                   # 事件描述
    event_type: EventType
    choices: List[Choice] = field(default_factory=list)
    # 纯检定用
    check_stat: Optional[str] = None
    check_dc: int = 10
    check_success: str = ""
    check_failure: str = ""
    # 战斗用
    enemy_data: Optional[Dict] = None
    # 标记
    required_flags: Dict[str, Any] = field(default_factory=dict)  # 触发条件
    auto_next: Optional[str] = None    # 自动跳转
    # 只有叙事上可互换的事件才应使用同一个分组名。
    shuffle_group: Optional[str] = None


class EventManager:
    """事件执行引擎。"""

    def __init__(self, character):
        self.character = character
        self.event_log: List[str] = []  # 事件日志
        self.last_roll_info: Optional[Dict] = None

    def execute_choice(self, event: Event, choice_index: int) -> Dict:
        """执行一个选项，返回结果字典。"""
        self.event_log = []
        choice = event.choices[choice_index]
        result = {
            "title": event.title,
            "choice_text": choice.text,
            "result_text": choice.result_text,
            "roll_info": None,
            "combat": None,
            "next_event": choice.next_event or event.auto_next,
            "hp_change": choice.hp_change,
            "mp_change": choice.mp_change,
            "xp_reward": choice.xp_reward,
            "item_reward": choice.item_reward,
            "flags_set": choice.flags_set,
            "is_critical_success": False,
            "is_critical_failure": False,
            "faction_reputation": choice.faction_reputation,
            "dawn_shard_reward": choice.dawn_shard_reward,
            "gold_reward": choice.gold_reward,
            "shadow_essence": choice.shadow_essence,
        }

        # 如果有骰子检定
        if choice.check_type:
            modifier = self._get_check_modifier(choice.check_type)
            roll_result, natural, total = Dice.check(choice.dc, modifier)
            result["roll_info"] = {
                "check_type": choice.check_type,
                "dc": choice.dc,
                "modifier": modifier,
                "natural": natural,
                "total": total,
                "result": roll_result,
            }

            if roll_result == RollResult.CRITICAL_SUCCESS:
                result["result_text"] = choice.critical_success_text or choice.success_text or choice.result_text
                result["xp_reward"] = int(result["xp_reward"] * 2)
                result["hp_change"] = 0
                result["mp_change"] = 0
                result["is_critical_success"] = True
            elif roll_result == RollResult.CRITICAL_FAILURE:
                result["result_text"] = choice.critical_failure_text or choice.failure_text or choice.result_text
                result["xp_reward"] = 0
                result["item_reward"] = None
                result["is_critical_failure"] = True
            elif roll_result == RollResult.SUCCESS:
                result["result_text"] = choice.success_text or choice.result_text
                result["hp_change"] = 0
                result["mp_change"] = 0
                result["item_reward"] = None
            else:
                result["result_text"] = choice.failure_text or choice.result_text
                result["hp_change"] = 0
                result["mp_change"] = 0
                result["xp_reward"] = 0
                result["item_reward"] = None

            self.last_roll_info = result["roll_info"]

        # 应用结果
        self.character.hp += result["hp_change"]
        self.character.mp += result["mp_change"]
        if result["xp_reward"] > 0:
            self.character.add_xp(result["xp_reward"])
        if result["item_reward"]:
            self.character.add_item(result["item_reward"])
        # 阵营声望
        if choice.faction_reputation:
            for fac, amt in choice.faction_reputation.items():
                self.character.add_faction_reputation(fac, amt)
                from .faction import Faction
                try:
                    fac_name = Faction[fac].display_name
                except KeyError:
                    fac_name = fac
                self.event_log.append(f"🏛 {fac_name} 声望 {'+' if amt > 0 else ''}{amt}")
        # 晨曦碎片
        if choice.dawn_shard_reward > 0:
            self.character.dawn_shards += choice.dawn_shard_reward
            self.event_log.append(f"✨ 获得 {choice.dawn_shard_reward} 晨曦碎片")
        # 金币
        if choice.gold_reward > 0:
            self.character.gold += choice.gold_reward
            self.event_log.append(f"💰 获得 {choice.gold_reward} 金币")
        # 暗影精华
        if choice.shadow_essence > 0:
            self.character.shadow_essence += choice.shadow_essence
            self.event_log.append(f"💎 获得 {choice.shadow_essence} 暗影精华")

        # 战斗触发
        if choice.trigger_combat and choice.combat_enemy:
            result["combat"] = choice.combat_enemy

        self.event_log.append(f"📜 {result['result_text']}")
        if result["roll_info"]:
            ri = result["roll_info"]
            self.event_log.append(
                f"🎲 {ri['check_type'].upper()}检定 DC={ri['dc']} | "
                f"出目={ri['natural']} + 加值={ri['modifier']} = {ri['total']} | "
                f"{Dice.result_text(ri['result'])}"
            )
        if result["hp_change"] != 0:
            change = result["hp_change"]
            sign = "+" if change > 0 else ""
            self.event_log.append(f"❤️ HP {sign}{change}")
        if result["mp_change"] != 0:
            change = result["mp_change"]
            sign = "+" if change > 0 else ""
            self.event_log.append(f"💙 MP {sign}{change}")
        if result["xp_reward"] > 0:
            self.event_log.append(f"⭐ 获得 {result['xp_reward']} 经验值")
        if result["item_reward"]:
            self.event_log.append(f"🎒 获得道具: {result['item_reward']}")

        return result

    def _get_check_modifier(self, check_type: str) -> int:
        mapping = {
            "str": self.character.str_mod,
            "dex": self.character.dex_mod,
            "int": self.character.int_mod,
            "wis": self.character.wis_mod,
            "cha": self.character.cha_mod,
            "luck": self.character.luck // 2,  # 幸运特殊处理
        }
        return mapping.get(check_type, 0)

    def get_event_log(self) -> List[str]:
        return self.event_log
