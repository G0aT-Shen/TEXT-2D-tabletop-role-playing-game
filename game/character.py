"""角色系统 — 职业、属性、技能、升级."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .equipment import Equipment


class CharClass(Enum):
    WARRIOR = ("战士", "🛡️", "近战专精，拥有强大的攻击力和生命力")
    ASSASSIN = ("刺客", "🗡️", "暗影中的杀手，敏捷与幸运过人")
    KNIGHT = ("骑士", "⚔️", "钢铁堡垒，守护队友的坚盾")
    PRIEST = ("牧师", "✝️", "神圣的治愈者，驱散黑暗")
    MAGE = ("法师", "🔮", "奥术大师，掌控元素之力")

    def __init__(self, display_name: str, icon: str, description: str):
        self.display_name = display_name
        self.icon = icon
        self.description = description


@dataclass
class Skill:
    """职业技能（支持技能树系统）。"""
    name: str
    description: str
    mp_cost: int
    cooldown: int           # 冷却回合数
    damage_mult: float = 1.0  # 伤害倍率
    heal_amount: int = 0     # 治疗量
    buff_effect: Optional[Dict] = None  # 增益效果
    debuff_effect: Optional[Dict] = None  # 减益效果
    current_cooldown: int = 0
    # 技能树系统字段
    skill_id: str = ""           # 唯一标识
    required_level: int = 1      # 解锁所需等级
    parent_id: Optional[str] = None  # 前置技能ID
    branch_name: str = ""        # 分支名称
    is_ultimate: bool = False    # 是否为终极技能
    is_locked: bool = True       # 是否未解锁

    def can_use(self, current_mp: int) -> bool:
        return not self.is_locked and self.current_cooldown == 0 and current_mp >= self.mp_cost

    def use(self):
        self.current_cooldown = self.cooldown

    def tick_cooldown(self):
        if self.current_cooldown > 0:
            self.current_cooldown -= 1


@dataclass
class Stats:
    """角色属性。"""
    max_hp: int
    max_mp: int
    hp: int
    mp: int
    strength: int      # STR — 物理攻击
    dexterity: int     # DEX — 命中/闪避
    intelligence: int  # INT — 魔法攻击
    wisdom: int        # WIS — 魔法防御/感知
    charisma: int      # CHA — 交涉
    luck: int          # LUK — 幸运


# 职业基础属性模板
CLASS_STATS: Dict[CharClass, dict] = {
    CharClass.WARRIOR: {"max_hp": 130, "max_mp": 35, "str": 17, "dex": 12, "int": 8, "wis": 10, "cha": 10, "luk": 10},
    CharClass.ASSASSIN: {"max_hp": 100, "max_mp": 45, "str": 10, "dex": 19, "int": 12, "wis": 10, "cha": 8, "luk": 16},
    CharClass.KNIGHT: {"max_hp": 155, "max_mp": 40, "str": 15, "dex": 10, "int": 10, "wis": 12, "cha": 14, "luk": 9},
    CharClass.PRIEST: {"max_hp": 110, "max_mp": 65, "str": 8, "dex": 10, "int": 14, "wis": 19, "cha": 12, "luk": 10},
    CharClass.MAGE: {"max_hp": 90, "max_mp": 85, "str": 6, "dex": 12, "int": 19, "wis": 14, "cha": 10, "luk": 13},
}


def _make_skills(char_class: CharClass) -> List[Skill]:
    """从技能树系统加载所有技能节点（默认仅解锁基础技能）。"""
    from .skill_tree import get_skill_tree, get_base_skills
    tree = get_skill_tree(char_class.name)
    base_indices = get_base_skills(char_class.name)

    skills = []
    for i, node in enumerate(tree):
        skill = Skill(
            name=node.name, description=node.description,
            mp_cost=node.mp_cost, cooldown=node.cooldown,
            damage_mult=node.damage_mult, heal_amount=node.heal_amount,
            buff_effect=node.buff_effect, debuff_effect=node.debuff_effect,
            skill_id=node.id, required_level=node.required_level,
            parent_id=node.parent_id, branch_name=node.branch_name,
            is_ultimate=node.is_ultimate,
            is_locked=(i not in base_indices),
        )
        skills.append(skill)
    return skills


# 职业自动加点属性映射
CLASS_AUTO_ATTR: Dict[CharClass, str] = {
    CharClass.WARRIOR: "strength",
    CharClass.ASSASSIN: "dexterity",
    CharClass.KNIGHT: "strength",
    CharClass.PRIEST: "wisdom",
    CharClass.MAGE: "intelligence",
}


def get_modifier(stat: int) -> int:
    """根据属性值计算调整值 (D&D风格)。"""
    return (stat - 10) // 2


class Character:
    """玩家角色。"""

    def __init__(self, name: str, char_class: CharClass, level: int = 1):
        self.name = name
        self.char_class = char_class
        self.level = level
        self.xp = 0
        self.xp_to_next = 70

        base = CLASS_STATS[char_class]
        self.stats = Stats(
            max_hp=base["max_hp"],
            max_mp=base["max_mp"],
            hp=base["max_hp"],
            mp=base["max_mp"],
            strength=base["str"],
            dexterity=base["dex"],
            intelligence=base["int"],
            wisdom=base["wis"],
            charisma=base["cha"],
            luck=base["luk"],
        )
        self.skills = _make_skills(char_class)
        self.status_effects: List[Dict] = []  # 状态效果列表
        self.items: List[Dict] = []           # 道具列表（每个元素是dict: {name, desc, effect}）
        self.defending: bool = False           # 是否在防御
        self.guaranteed_crit: bool = False     # 下次攻击必暴击
        self.equipment: Dict[str, "Equipment"] = {}  # slot_name → Equipment

        # ── 技能树系统 ──
        self.skill_points: int = 0       # 可用技能点数
        self._levels_gained: int = 0     # 已获得等级总数（用于计算技能点）

        # ── 属性分配 ──
        self.pending_attr_points: int = 0  # 待分配属性点

        # ── 经济系统 ──
        self.gold: int = 0              # 金币
        self.shadow_essence: int = 0    # 暗影精华

        # ── Phase 3: 阵营声望 ──
        self.faction_reputation: Dict[str, int] = {"SHADOW": 0, "DAWN": 0, "OBSERVER": 0}
        self.dawn_shards: int = 0        # 晨曦碎片（章节奖励）

        # ── Phase 3: New Game+ ──
        self.is_ng_plus: bool = False    # 是否为二周目
        self.ng_plus_level: int = 0      # 第几周目

    # --- 便捷属性访问 ---
    @property
    def hp(self) -> int:
        return self.stats.hp

    @hp.setter
    def hp(self, value: int):
        self.stats.hp = max(0, min(value, self.stats.max_hp))

    @property
    def mp(self) -> int:
        return self.stats.mp

    @mp.setter
    def mp(self, value: int):
        self.stats.mp = max(0, min(value, self.stats.max_mp))

    # --- 属性调整值 ---
    @property
    def str_mod(self) -> int:
        return get_modifier(self.stats.strength)

    @property
    def dex_mod(self) -> int:
        return get_modifier(self.stats.dexterity)

    @property
    def int_mod(self) -> int:
        return get_modifier(self.stats.intelligence)

    @property
    def wis_mod(self) -> int:
        return get_modifier(self.stats.wisdom)

    @property
    def cha_mod(self) -> int:
        return get_modifier(self.stats.charisma)

    @property
    def attack_bonus(self) -> int:
        """物理攻击加值。"""
        if self.char_class in (CharClass.MAGE, CharClass.PRIEST):
            return self.int_mod
        if self.char_class == CharClass.ASSASSIN:
            return self.dex_mod
        return self.str_mod

    @property
    def defense(self) -> int:
        """防御值。"""
        base = 10 + self.dex_mod
        if self.defending:
            base += 4
        return base

    @property
    def is_alive(self) -> bool:
        return self.stats.hp > 0

    # --- 装备 ---
    def equip(self, eq: "Equipment") -> Optional["Equipment"]:
        """装备一件装备，返回被替换的旧装备（如有）。"""
        from .equipment import EquipmentSlot
        slot_key = eq.slot.value
        # 检查职业限制
        if eq.class_restriction and eq.class_restriction != self.char_class.name:
            return None  # 职业不符
        old = self.equipment.pop(slot_key, None)
        self.equipment[slot_key] = eq
        self._recalc_stats()
        return old

    def unequip(self, slot_name: str) -> Optional["Equipment"]:
        """卸下指定槽位装备。"""
        eq = self.equipment.pop(slot_name, None)
        if eq:
            self._recalc_stats()
        return eq

    def get_equipment_attack(self) -> int:
        """装备提供的攻击力。"""
        total = 0
        for eq in self.equipment.values():
            total += eq.attack
            # 检查词缀
            for a in eq.affixes:
                total += a["effect"].get("attack_bonus", 0)
        return total

    def get_equipment_defense(self) -> int:
        """装备提供的防御力。"""
        total = 0
        for eq in self.equipment.values():
            total += eq.defense
            for a in eq.affixes:
                total += a["effect"].get("defense_bonus", 0)
        return total

    def get_equipment_stat_bonus(self, stat_name: str) -> int:
        """装备提供的某项属性加值。"""
        total = 0
        for eq in self.equipment.values():
            total += eq.stat_bonuses.get(stat_name, 0)
            for a in eq.affixes:
                key_map = {"str": "strength", "dex": "dexterity", "int": "intelligence",
                            "wis": "wisdom", "cha": "charisma", "luk": "luck"}
                total += a["effect"].get(f"{stat_name}_bonus", 0)
                # 兼容短名
                short = {v: k for k, v in key_map.items()}
                total += a["effect"].get(f"{short.get(stat_name, stat_name)}_bonus", 0)
        return total

    def has_equipment_affix(self, affix_name: str) -> bool:
        """检查是否拥有某个词缀。"""
        for eq in self.equipment.values():
            for a in eq.affixes:
                if a["name"] == affix_name:
                    return True
        return False

    def get_equipment_affix_values(self) -> Dict:
        """获取所有装备词缀的合并效果。"""
        result: Dict = {}
        for eq in self.equipment.values():
            for a in eq.affixes:
                for k, v in a["effect"].items():
                    if isinstance(v, bool):
                        result[k] = v
                    elif isinstance(v, (int, float)):
                        result[k] = result.get(k, 0) + v
        return result

    def _recalc_stats(self):
        """重新计算装备影响后的属性（不改base stats，只调整hp/mp上限）。"""
        base = CLASS_STATS[self.char_class]
        eq_hp_bonus = sum(eq.stat_bonuses.get("max_hp", 0) for eq in self.equipment.values())
        eq_mp_bonus = self.get_equipment_stat_bonus("max_mp") + sum(
            a["effect"].get("max_mp_bonus", 0) for eq in self.equipment.values()
            for a in eq.affixes
        )
        level_hp_bonus = (self.level - 1) * 10
        level_mp_bonus = (self.level - 1) * 6

        old_max_hp = self.stats.max_hp
        old_max_mp = self.stats.max_mp

        self.stats.max_hp = base["max_hp"] + level_hp_bonus + eq_hp_bonus
        self.stats.max_mp = base["max_mp"] + level_mp_bonus + eq_mp_bonus

        # 保留当前HP/MP比例
        if old_max_hp > 0:
            ratio_hp = self.stats.hp / old_max_hp
            self.stats.hp = int(self.stats.max_hp * ratio_hp)
        if old_max_mp > 0:
            ratio_mp = self.stats.mp / old_max_mp
            self.stats.mp = int(self.stats.max_mp * ratio_mp)

    # --- 道具 ---
    def add_item(self, item):
        """添加道具。接收字符串名称或字典。"""
        from .items import get_item
        item_dict = get_item(item)
        if item_dict:
            self.items.append(dict(item_dict))

    # --- 经验值与升级 ---
    def add_xp(self, amount: int):
        self.xp += amount
        while self.xp >= self.xp_to_next:
            self.xp -= self.xp_to_next
            self._level_up()

    def _level_up(self):
        """升级：增加HP/MP上限，获得自由属性点和技能点。"""
        self.level += 1
        self.xp_to_next = int(self.xp_to_next * 1.35)
        self._levels_gained += 1

        # HP/MP成长（不再全属性+1）
        self.stats.max_hp += 10
        self.stats.max_mp += 6
        self.stats.hp = self.stats.max_hp  # 升级满血满蓝
        self.stats.mp = self.stats.max_mp

        # 自由属性点：基础3点 + 每4级额外1点
        base_attr = 3
        bonus = 1 if self.level % 4 == 0 else 0
        self.pending_attr_points += base_attr + bonus

        # 职业自动加点：1点自动加到职业主属性
        auto_attr = CLASS_AUTO_ATTR.get(self.char_class, "strength")
        setattr(self.stats, auto_attr, getattr(self.stats, auto_attr) + 1)

        # 技能点：每2级获得1点
        while self._levels_gained >= 2:
            self._levels_gained -= 2
            self.skill_points += 1

    def allocate_attr(self, attr_name: str) -> bool:
        """分配1点属性到指定属性。返回是否成功。"""
        if self.pending_attr_points <= 0:
            return False
        valid_attrs = ["strength", "dexterity", "intelligence", "wisdom", "charisma", "luck"]
        if attr_name not in valid_attrs:
            return False
        setattr(self.stats, attr_name, getattr(self.stats, attr_name) + 1)
        self.pending_attr_points -= 1
        return True

    # --- 技能树 ---
    def get_usable_skills(self) -> List[Skill]:
        return [s for s in self.skills if s.can_use(self.mp)]

    def get_unlocked_skills(self) -> List[Skill]:
        """获取所有已解锁的技能。"""
        return [s for s in self.skills if not s.is_locked]

    def unlock_skill(self, skill_index: int) -> bool:
        """解锁指定索引的技能节点。返回是否成功。"""
        if skill_index < 0 or skill_index >= len(self.skills):
            return False
        skill = self.skills[skill_index]
        if not skill.is_locked:
            return False  # 已解锁
        if self.skill_points < 1:
            return False  # 技能点不足
        if skill.required_level > self.level:
            return False  # 等级不足

        # 检查前置技能
        if skill.parent_id:
            parent_unlocked = False
            for s in self.skills:
                if s.skill_id == skill.parent_id and not s.is_locked:
                    parent_unlocked = True
                    break
            if not parent_unlocked:
                return False

        # 检查二选一冲突（同一父节点的兄弟已被解锁的不允许再解锁）
        if skill.parent_id:
            from .skill_tree import get_skill_tree, get_branch_children
            tree = get_skill_tree(self.char_class.name)
            parent_idx = -1
            for i, s in enumerate(self.skills):
                if s.skill_id == skill.parent_id:
                    parent_idx = i
                    break
            if parent_idx >= 0:
                siblings = get_branch_children(tree, parent_idx)
                for sib_idx in siblings:
                    if sib_idx != skill_index and not self.skills[sib_idx].is_locked:
                        return False  # 已选择另一个分支

        # 终极技能消耗3点
        cost = 3 if skill.is_ultimate else 1
        if self.skill_points < cost:
            return False

        self.skill_points -= cost
        skill.is_locked = False
        return True

    def get_available_branches(self) -> List[int]:
        """获取当前可解锁的技能索引列表。"""
        from .skill_tree import get_skill_tree, get_branch_children
        tree = get_skill_tree(self.char_class.name)
        available = []
        unlocked_ids = {s.skill_id for s in self.skills if not s.is_locked}
        for i, skill in enumerate(self.skills):
            if not skill.is_locked:
                continue
            if skill.required_level > self.level:
                continue
            # 有前置技能的，检查前置是否解锁
            if skill.parent_id:
                if skill.parent_id not in unlocked_ids:
                    continue
                # 检查兄弟冲突
                parent_idx = -1
                for pi, s in enumerate(self.skills):
                    if s.skill_id == skill.parent_id:
                        parent_idx = pi
                        break
                if parent_idx >= 0:
                    siblings = get_branch_children(tree, parent_idx)
                    conflict = False
                    for sib_idx in siblings:
                        if sib_idx != i and not self.skills[sib_idx].is_locked:
                            conflict = True
                            break
                    if conflict:
                        continue
            available.append(i)
        return available

    def use_skill(self, skill_index: int):
        skill = self.skills[skill_index]
        if not skill.can_use(self.mp):
            return False
        self.mp -= skill.mp_cost
        skill.use()
        return True

    def tick_cooldowns(self):
        for s in self.skills:
            s.tick_cooldown()

    # --- 状态效果 ---
    def apply_effect(self, effect: Dict):
        self.status_effects.append(effect)

    def tick_effects(self):
        """处理持续效果（每回合）。"""
        for effect in self.status_effects[:]:
            effect["duration"] -= 1
            if effect.get("type") == "poison":
                self.hp -= effect.get("damage", 5)
            if effect["duration"] <= 0:
                self.status_effects.remove(effect)

    def has_effect(self, effect_type: str) -> bool:
        return any(e.get("type") == effect_type for e in self.status_effects)

    # --- 道具使用 ---
    def remove_item(self, index: int) -> Optional[Dict]:
        """移除并返回指定索引的道具。"""
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def use_item(self, index: int) -> Optional[Dict]:
        """使用道具（移除并返回效果数据）。"""
        return self.remove_item(index)

    # --- 阵营声望 ---
    def add_faction_reputation(self, faction: str, amount: int):
        """增加指定阵营声望。"""
        if faction in self.faction_reputation:
            self.faction_reputation[faction] += amount

    def get_faction_tier(self, faction: str) -> int:
        """获取阵营声望等级（0-3）。"""
        from .faction import get_faction_tier
        return get_faction_tier(self.faction_reputation.get(faction, 0))

    def has_faction_passive(self, faction: str) -> bool:
        """是否已解锁阵营被动。"""
        from .faction import has_passive
        return has_passive(self.faction_reputation.get(faction, 0))

    def get_active_faction_passives(self) -> Dict:
        """获取所有已激活的阵营被动效果。"""
        from .faction import FACTION_PASSIVES, has_passive
        passives = {}
        for fac in ["SHADOW", "DAWN", "OBSERVER"]:
            if has_passive(self.faction_reputation.get(fac, 0)):
                passives[fac] = FACTION_PASSIVES.get(fac, {}).get("effect", {})
        return passives

    # --- 序列化 ---
    def to_dict(self) -> dict:
        eq_data = {k: v.to_dict() for k, v in self.equipment.items()} if self.equipment else {}
        return {
            "name": self.name,
            "char_class": self.char_class.name,
            "level": self.level,
            "xp": self.xp,
            "xp_to_next": self.xp_to_next,
            "stats": {
                "max_hp": self.stats.max_hp, "max_mp": self.stats.max_mp,
                "hp": self.stats.hp, "mp": self.stats.mp,
                "strength": self.stats.strength, "dexterity": self.stats.dexterity,
                "intelligence": self.stats.intelligence, "wisdom": self.stats.wisdom,
                "charisma": self.stats.charisma, "luck": self.stats.luck,
            },
            "skills_cooldown": [s.current_cooldown for s in self.skills],
            "skills_locked": [s.is_locked for s in self.skills],
            "skill_points": self.skill_points,
            "_levels_gained": self._levels_gained,
            "pending_attr_points": self.pending_attr_points,
            "gold": self.gold,
            "shadow_essence": self.shadow_essence,
            "faction_reputation": self.faction_reputation,
            "dawn_shards": self.dawn_shards,
            "is_ng_plus": self.is_ng_plus,
            "ng_plus_level": self.ng_plus_level,
            "items": self.items,
            "equipment": eq_data,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        char = cls(
            name=data["name"],
            char_class=CharClass[data["char_class"]],
            level=data["level"],
        )
        char.xp = data["xp"]
        char.xp_to_next = data["xp_to_next"]
        s = data["stats"]
        char.stats = Stats(**s)
        # 向后兼容：旧存档物品是字符串列表
        from .items import get_item
        raw_items = data.get("items", [])
        char.items = [get_item(it) for it in raw_items if get_item(it)]
        # 恢复技能冷却
        for i, cd in enumerate(data.get("skills_cooldown", [])):
            if i < len(char.skills):
                char.skills[i].current_cooldown = cd
        # 恢复技能锁定状态
        for i, locked in enumerate(data.get("skills_locked", [])):
            if i < len(char.skills):
                char.skills[i].is_locked = locked
        # 恢复 Phase 2 新字段
        char.skill_points = data.get("skill_points", 0)
        char._levels_gained = data.get("_levels_gained", 0)
        char.pending_attr_points = data.get("pending_attr_points", 0)
        char.gold = data.get("gold", 0)
        char.shadow_essence = data.get("shadow_essence", 0)
        # 恢复 Phase 3 新字段
        char.faction_reputation = data.get("faction_reputation", {"SHADOW": 0, "DAWN": 0, "OBSERVER": 0})
        char.dawn_shards = data.get("dawn_shards", 0)
        char.is_ng_plus = data.get("is_ng_plus", False)
        char.ng_plus_level = data.get("ng_plus_level", 0)
        # 恢复装备
        eq_data = data.get("equipment", {})
        if eq_data:
            from .equipment import Equipment
            for slot_key, eq_dict in eq_data.items():
                try:
                    char.equipment[slot_key] = Equipment.from_dict(eq_dict)
                except Exception:
                    pass
        return char
