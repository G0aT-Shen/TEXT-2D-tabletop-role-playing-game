"""战斗系统 — 回合制战斗."""

import random
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Tuple

from .dice import Dice, RollResult
from .character import Character


# 难度设置
DIFFICULTY_SETTINGS = {
    "easy": {"name": "简单", "hp_mult": 0.7, "atk_mult": 0.8, "def_mult": 0.8,
             "xp_mult": 0.9, "gold_mult": 0.8, "desc": "敌人较弱，适合轻松体验剧情"},
    "normal": {"name": "标准", "hp_mult": 1.0, "atk_mult": 1.0, "def_mult": 1.0,
               "xp_mult": 1.0, "gold_mult": 1.0, "desc": "均衡的战斗体验"},
    "hard": {"name": "硬核", "hp_mult": 1.3, "atk_mult": 1.2, "def_mult": 1.2,
             "xp_mult": 1.1, "gold_mult": 1.3, "desc": "敌人更强大，奖励更丰厚"},
}

# 全局难度设置
_current_difficulty: str = "normal"


def set_difficulty(difficulty: str):
    global _current_difficulty
    if difficulty in DIFFICULTY_SETTINGS:
        _current_difficulty = difficulty


def get_difficulty() -> str:
    return _current_difficulty


def get_difficulty_settings() -> dict:
    return DIFFICULTY_SETTINGS.get(_current_difficulty, DIFFICULTY_SETTINGS["normal"])


def apply_difficulty(enemy_dict: dict) -> dict:
    """根据当前难度缩放敌人属性。"""
    settings = get_difficulty_settings()
    scaled = dict(enemy_dict)
    scaled["max_hp"] = int(scaled["max_hp"] * settings["hp_mult"])
    scaled["attack"] = int(scaled["attack"] * settings["atk_mult"])
    scaled["defense"] = int(scaled["defense"] * settings["def_mult"])
    scaled["xp_reward"] = int(scaled["xp_reward"] * settings["xp_mult"])
    return scaled


class CombatAction(Enum):
    ATTACK = "attack"
    SKILL = "skill"
    DEFEND = "defend"
    ITEM = "item"


@dataclass
class Enemy:
    """敌人数据。"""
    name: str
    description: str
    max_hp: int
    hp: int
    attack: int       # 攻击力
    defense: int      # 防御力
    level: int = 1
    xp_reward: int = 30
    gold_reward: int = 10  # 金币奖励
    skills: List[Dict] = field(default_factory=list)
    status_effects: List[Dict] = field(default_factory=list)
    is_boss: bool = False
    template_id: str = ""  # 模板ID，用于图鉴追踪

    @property
    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, amount: int, armor_pen: int = 0) -> int:
        """受到伤害，返回实际伤害值。armor_pen 为破甲值。"""
        effective_def = max(0, self.defense - armor_pen)
        actual = max(0, amount - effective_def // 2)
        self.hp = max(0, self.hp - actual)
        return actual

    def has_effect(self, effect_type: str) -> bool:
        return any(e.get("type") == effect_type for e in self.status_effects)

    def tick_effects(self):
        for effect in self.status_effects[:]:
            effect["duration"] -= 1
            if effect.get("type") == "poison":
                self.hp = max(0, self.hp - effect.get("damage", 5))
            if effect["duration"] <= 0:
                self.status_effects.remove(effect)


# -------- 预设敌人模板 --------

ENEMY_TEMPLATES = {
    "shadow_wolf": {
        "name": "暗影狼", "description": "被黑暗腐蚀的森林之狼，双眼泛着血红的光芒",
        "max_hp": 28, "attack": 10, "defense": 4, "level": 1, "xp_reward": 25,
        "gold_reward": 15,
        "skills": [{"name": "暗影撕咬", "damage_mult": 1.3, "mp_cost": 0}],
    },
    "dark_spirit": {
        "name": "黑暗游魂", "description": "漂浮在空中的亡灵，散发着不祥的气息",
        "max_hp": 25, "attack": 8, "defense": 3, "level": 1, "xp_reward": 20,
        "gold_reward": 12,
        "skills": [{"name": "灵魂吸取", "damage_mult": 1.2, "heal_self": 6, "mp_cost": 0}],
    },
    "corrupted_knight": {
        "name": "堕落骑士", "description": "曾经荣耀的骑士，如今被黑暗力量扭曲",
        "max_hp": 48, "attack": 12, "defense": 10, "level": 2, "xp_reward": 40,
        "gold_reward": 25,
        "skills": [
            {"name": "暗黑斩", "damage_mult": 1.6, "mp_cost": 0},
            {"name": "黑暗护盾", "buff_defense": 5, "duration": 2, "mp_cost": 0},
        ],
    },
    "demon_imp": {
        "name": "恶魔小鬼", "description": "来自深渊的小型恶魔，狡猾而恶毒",
        "max_hp": 20, "attack": 6, "defense": 2, "level": 1, "xp_reward": 15,
        "gold_reward": 10,
        "skills": [{"name": "火焰弹", "damage_mult": 1.1, "mp_cost": 0}],
    },
    "necromancer": {
        "name": "亡灵法师", "description": "操控亡灵的黑魔法师",
        "max_hp": 40, "attack": 13, "defense": 6, "level": 2, "xp_reward": 50,
        "gold_reward": 35,
        "skills": [
            {"name": "死亡缠绕", "damage_mult": 1.7, "mp_cost": 0},
            {"name": "召唤骷髅", "summon_minion": True, "mp_cost": 0},
        ],
    },
    "shadow_dragon": {  # 第一章Boss
        "name": "暗影巨龙", "description": "盘踞在黑暗城堡顶端的远古巨龙，第一章的最终守护者",
        "max_hp": 90, "attack": 15, "defense": 10, "level": 3, "xp_reward": 200, "is_boss": True,
        "gold_reward": 100,
        "skills": [
            {"name": "暗影吐息", "damage_mult": 2.2, "mp_cost": 0},
            {"name": "龙翼风暴", "damage_mult": 1.3, "debuff": "stun", "duration": 1, "mp_cost": 0},
        ],
    },
    "forest_lord": {  # 第二章Boss
        "name": "腐化树灵", "description": "被黑暗力量腐蚀的远古树灵，根系遍布整片森林",
        "max_hp": 120, "attack": 16, "defense": 14, "level": 4, "xp_reward": 350, "is_boss": True,
        "gold_reward": 180,
        "skills": [
            {"name": "根须缠绕", "damage_mult": 1.5, "debuff": "slow", "duration": 2, "mp_cost": 0},
            {"name": "腐化孢子", "damage_mult": 1.3, "debuff": "poison", "damage": 8, "duration": 3, "mp_cost": 0},
            {"name": "自然之怒", "damage_mult": 2.2, "mp_cost": 0},
        ],
    },
    "abyssal_lord": {  # 第三章Boss
        "name": "深渊领主", "description": "深渊军团的统帅，手持燃着黑色火焰的巨剑",
        "max_hp": 160, "attack": 20, "defense": 16, "level": 5, "xp_reward": 500, "is_boss": True,
        "gold_reward": 300,
        "skills": [
            {"name": "深渊斩击", "damage_mult": 1.8, "mp_cost": 0},
            {"name": "黑暗降临", "damage_mult": 1.4, "debuff": "stun", "duration": 1, "mp_cost": 0},
            {"name": "军团号令", "summon_minion": True, "mp_cost": 0},
        ],
    },
    "night_god": {  # 第四章最终Boss
        "name": "绝夜之神·诺克斯", "description": "暗黑世界的至高存在，绝夜的主宰者，周身环绕着吞噬一切光明的黑暗",
        "max_hp": 220, "attack": 25, "defense": 20, "level": 7, "xp_reward": 1000, "is_boss": True,
        "gold_reward": 500,
        "skills": [
            {"name": "终末之暗", "damage_mult": 2.5, "mp_cost": 0},
            {"name": "虚空吞噬", "damage_mult": 1.7, "heal_self": 25, "mp_cost": 0},
            {"name": "绝夜诅咒", "damage_mult": 1.3, "debuff": "poison", "damage": 12, "duration": 3, "mp_cost": 0},
            {"name": "黑暗降临", "damage_mult": 1.8, "debuff": "stun", "duration": 1, "mp_cost": 0},
        ],
    },
    "night_reaver": {
        "name": "暗夜掠夺者", "description": "黑暗中的猎手，专门袭击落单的旅客",
        "max_hp": 42, "attack": 12, "defense": 8, "level": 3, "xp_reward": 45,
        "gold_reward": 30,
        "skills": [{"name": "暗袭", "damage_mult": 1.7, "mp_cost": 0}],
    },
    "void_walker": {
        "name": "虚空行者", "description": "从虚空裂隙中诞生的怪物，形态不断扭曲",
        "max_hp": 55, "attack": 15, "defense": 10, "level": 4, "xp_reward": 60,
        "gold_reward": 40,
        "skills": [{"name": "虚空之触", "damage_mult": 1.3, "debuff": "slow", "duration": 1, "mp_cost": 0}],
    },
}


def create_enemy(template_id: str) -> Optional[Enemy]:
    """根据模板创建敌人（应用难度缩放）。"""
    tmpl = ENEMY_TEMPLATES.get(template_id)
    if not tmpl:
        return None
    scaled = apply_difficulty(tmpl)
    return Enemy(
        name=scaled["name"],
        description=scaled["description"],
        max_hp=scaled["max_hp"],
        hp=scaled["max_hp"],
        attack=scaled["attack"],
        defense=scaled["defense"],
        level=scaled["level"],
        xp_reward=scaled["xp_reward"],
        gold_reward=scaled.get("gold_reward", 10),
        skills=scaled.get("skills", []),
        is_boss=scaled.get("is_boss", False),
        template_id=template_id,
    )


class CombatEngine:
    """战斗引擎 — 支持单人和双人模式。"""

    def __init__(self, players: List[Character], enemy: Enemy):
        self.players = players      # 所有玩家角色（1人或2人）
        self.player = players[0]    # 向后兼容：第一个玩家
        self.enemy = enemy
        self.turn: int = 0
        self.log: List[str] = []
        self.combat_over: bool = False
        self.player_won: bool = False
        self.escaped: bool = False
        self.current_player_index: int = 0  # 当前行动中的玩家

    @property
    def current_player(self) -> Character:
        return self.players[self.current_player_index]

    @property
    def is_multiplayer(self) -> bool:
        return len(self.players) > 1

    def start(self):
        p_names = " & ".join(p.name for p in self.players)
        self.log = [
            f"⚔️ 战斗开始！{p_names} VS {self.enemy.name}",
            f"📖 {self.enemy.description}",
        ]

    def player_action(self, player_index: int, action: CombatAction,
                      skill_index: int = 0) -> List[str]:
        """执行指定玩家的行动，返回本轮日志。"""
        round_log = []
        player = self.players[player_index]
        self.current_player_index = player_index

        if self.turn == 0 and player_index == 0:
            round_log.append(f"━━━ 第 1 回合 ━━━")
        elif player_index == 0:
            round_log.append(f"━━━ 第 {self.turn + 1} 回合 ━━━")

        # --- 处理玩家状态效果 ---
        if player.has_effect("stun"):
            round_log.append(f"💫 [{player.name}] 被眩晕了，无法行动！")
            self._advance_turn(round_log)
            self.log.extend(round_log)
            return round_log

        # --- 玩家行动 ---
        if action == CombatAction.ATTACK:
            self._player_attack(player, round_log)
        elif action == CombatAction.SKILL:
            self._player_skill(player, skill_index, round_log)
        elif action == CombatAction.DEFEND:
            # 词缀: 每回合回复
            self._apply_regen(player, round_log)
            player.defending = True
            round_log.append(f"🛡️ [{player.name}] 进入防御姿态，防御力提升！")
        elif action == CombatAction.ITEM:
            # 物品效果由 engine 层处理，这里跳过（engine 会先处理物品再调用 player_action）
            pass

        # --- 检查敌人是否存活 ---
        if not self.enemy.is_alive:
            round_log.append(f"💀 {self.enemy.name} 被击败了！")
            self.combat_over = True
            self.player_won = True
            self._end_round_for_all(round_log)
            self.log.extend(round_log)
            return round_log

        # --- 多人模式：轮到下一个玩家行动 ---
        if self.is_multiplayer:
            self._advance_turn(round_log)
        else:
            # 单人模式：直接进入敌人回合
            self._enemy_turn(round_log)
            if not self.player.is_alive:
                round_log.append("💀 你被击败了...")
                self.combat_over = True
                self.player_won = False
            self._end_round_for_all(round_log)

        self.log.extend(round_log)
        return round_log

    def _advance_turn(self, log: List[str]):
        """多人模式：切换到下一位玩家。如果是最后一位玩家，执行敌人行动。"""
        next_idx = self.current_player_index + 1
        if next_idx < len(self.players):
            # 还有未行动的玩家
            self.current_player_index = next_idx
        else:
            # 所有玩家已行动完毕 → 敌人回合
            self._enemy_turn(log)

            # 检查所有玩家是否全灭
            if all(not p.is_alive for p in self.players):
                log.append("💀 全队覆灭...")
                self.combat_over = True
                self.player_won = False
            self._end_round_for_all(log)
            self.current_player_index = 0

    def _apply_regen(self, player: Character, log: List[str]):
        """处理装备词缀: 每回合回复 + 阵营被动。"""
        if not hasattr(player, 'get_equipment_affix_values'):
            return
        affix_vals = player.get_equipment_affix_values()
        regen = affix_vals.get("regen_hp", 0)
        if regen > 0 and player.hp < player.stats.max_hp:
            player.hp = min(player.stats.max_hp, player.hp + regen)
            if regen >= 3:
                log.append(f"💚 [{player.name}] 装备效果回复 {regen} HP")

        # 阵营被动: 暗影亲和 — 每回合恢复5%MP
        if hasattr(player, 'has_faction_passive') and player.has_faction_passive("SHADOW"):
            mp_regen = max(1, int(player.stats.max_mp * 0.05))
            if player.mp < player.stats.max_mp:
                player.mp = min(player.stats.max_mp, player.mp + mp_regen)
                if self.turn > 0:
                    log.append(f"💎 [{player.name}] 暗影亲和恢复 {mp_regen} MP")

    def _player_attack(self, player: Character, log: List[str]):
        # 词缀: 每回合回复
        self._apply_regen(player, log)
        
        natural = Dice.d20()
        is_crit = natural == 20 or player.guaranteed_crit
        player.guaranteed_crit = False

        if natural == 1:
            log.append(f"❌ [{player.name}] 攻击失误！武器挥空了...")
            return

        atk_bonus = player.attack_bonus
        total = natural + atk_bonus

        if total >= self.enemy.defense:
            # 统一伤害公式: 基础攻击 + 属性修正 + 装备
            eq_atk = player.get_equipment_attack() if hasattr(player, 'get_equipment_attack') else 0
            base_dmg = 6 + atk_bonus + eq_atk
            dmg = base_dmg * 2 if is_crit else base_dmg
            # 词缀: 破甲
            armor_pen = 0
            affix_vals = player.get_equipment_affix_values() if hasattr(player, 'get_equipment_affix_values') else {}
            armor_pen = affix_vals.get("armor_pen", 0)
            # 对恶魔伤害加成
            demon_bonus = affix_vals.get("demon_dmg_pct", 0)
            if self.enemy.name in ("恶魔小鬼", "深渊领主", "绝夜之神·诺克斯", "黑暗游魂"):
                dmg = int(dmg * (1 + demon_bonus / 100))
            actual = self.enemy.take_damage(dmg, armor_pen)
            crit_text = " 💥暴击！" if is_crit else ""
            log.append(
                f"⚔️ [{player.name}] 攻击！出目={natural}+{atk_bonus}={total} | "
                f"造成 {actual} 点伤害{crit_text}"
            )
        else:
            log.append(f"🛡️ [{player.name}] 攻击未命中！出目={natural}+{atk_bonus}={total} < 防御={self.enemy.defense}")

    def _player_skill(self, player: Character, skill_index: int, log: List[str]):
        # 词缀: 每回合回复
        self._apply_regen(player, log)
        
        if skill_index >= len(player.skills):
            log.append("❌ 无效的技能选择")
            return

        skill = player.skills[skill_index]
        if not skill.can_use(player.mp):
            log.append(f"❌ 无法使用 {skill.name}：MP不足或冷却中")
            return

        player.use_skill(skill_index)
        log.append(f"✨ [{player.name}] 使用技能: {skill.name}！")

        # 治疗技能（治疗自己和所有队友）
        if skill.heal_amount > 0:
            for p in self.players:
                if p.is_alive:
                    heal = skill.heal_amount
                    p.hp = min(p.stats.max_hp, p.hp + heal)
                    log.append(f"💚 [{p.name}] 回复 {heal} 点生命值")

        # 伤害技能
        if skill.damage_mult > 0:
            natural = Dice.d20()
            is_crit = natural == 20 or player.guaranteed_crit
            player.guaranteed_crit = False

            if natural == 1:
                log.append(f"❌ [{player.name}] 技能释放失败！")
                return

            atk_bonus = player.attack_bonus
            total = natural + atk_bonus
            # 统一伤害公式
            eq_atk = player.get_equipment_attack() if hasattr(player, 'get_equipment_attack') else 0
            affix_vals = player.get_equipment_affix_values() if hasattr(player, 'get_equipment_affix_values') else {}
            base_dmg = int((6 + atk_bonus + eq_atk) * skill.damage_mult)
            # 刺客技能伤害加成
            assassin_bonus = affix_vals.get("assassin_skill_dmg_pct", 0)
            if player.char_class.name == "ASSASSIN" and assassin_bonus > 0:
                base_dmg = int(base_dmg * (1 + assassin_bonus / 100))
            # 对恶魔伤害加成
            demon_bonus = affix_vals.get("demon_dmg_pct", 0)
            if self.enemy.name in ("恶魔小鬼", "深渊领主", "绝夜之神·诺克斯", "黑暗游魂"):
                base_dmg = int(base_dmg * (1 + demon_bonus / 100))
            dmg = base_dmg * 2 if is_crit else base_dmg
            armor_pen = affix_vals.get("armor_pen", 0)
            actual = self.enemy.take_damage(dmg, armor_pen)
            # 吸血
            lifesteal = affix_vals.get("lifesteal_pct", 0)
            if lifesteal > 0:
                heal = int(actual * lifesteal / 100)
                player.hp = min(player.stats.max_hp, player.hp + heal)
                log.append(f"🩸 [{player.name}] 吸血回复 {heal} HP")
            crit_text = " 💥暴击！" if is_crit else ""
            log.append(
                f"💥 [{player.name}] 技能伤害！出目={natural}+{atk_bonus}={total} | "
                f"造成 {actual} 点伤害{crit_text}"
            )

        # 增益效果
        if skill.buff_effect:
            player.apply_effect(skill.buff_effect.copy())
            log.append(f"🔺 [{player.name}] 获得增益: {skill.buff_effect}")

        # 减益效果
        if skill.debuff_effect:
            self.enemy.status_effects.append(skill.debuff_effect.copy())
            log.append(f"🔻 对敌人施加: {skill.debuff_effect}")

    def _enemy_turn(self, log: List[str]):
        if self.enemy.has_effect("stun"):
            log.append(f"💫 {self.enemy.name} 被眩晕了，跳过行动！")
            return

        # 敌人AI：随机选择行动，随机选择目标
        if self.enemy.skills and random.random() < 0.4:
            skill = random.choice(self.enemy.skills)
            log.append(f"👹 {self.enemy.name} 使用 {skill['name']}！")
            dmg_mult = skill.get("damage_mult", 1.0)
        else:
            dmg_mult = 1.0
            log.append(f"👹 {self.enemy.name} 进行攻击！")

        # 伤害计算
        natural = Dice.d20()
        if natural == 1:
            log.append("😅 敌人的攻击失误了！")
            return

        # 随机选择一个活着的玩家作为目标
        alive_players = [p for p in self.players if p.is_alive]
        if not alive_players:
            return
        target = random.choice(alive_players)

        is_crit = natural == 20
        total = natural + (self.enemy.attack - 10) // 2

        if total >= target.defense or natural >= 17:
            base_dmg = max(1, random.randint(3, 9) + self.enemy.attack // 4)
            dmg = int(base_dmg * dmg_mult * (2 if is_crit else 1))
            if target.defending:
                dmg = dmg // 2
                log.append(f"🛡️ [{target.name}] 防御姿态减免了一半伤害！")
            dmg = max(1, dmg)
            target.hp -= dmg

            # DAWN 阵营被动：致命伤保留1HP（每章1次）
            if target.hp <= 0 and hasattr(target, 'has_faction_passive') and target.has_faction_passive("DAWN"):
                if not getattr(target, 'dawn_death_save_used', True):
                    target.dawn_death_save_used = True
                    target.hp = 1
                    log.append(f"☀️ [{target.name}] 晨曦加护发动！致命伤保留1HP！")

            crit_text = " 💥暴击！" if is_crit else ""
            target_mark = " → " + target.name if self.is_multiplayer else ""
            log.append(f"💔 [{target.name}] 受到 {dmg} 点伤害{crit_text}{target_mark}")
        else:
            target_mark = f" → [{target.name}]" if self.is_multiplayer else ""
            log.append(f"🙏 敌人的攻击未命中{target_mark}！")

    def _end_round_for_all(self, log: List[str]):
        for p in self.players:
            p.tick_cooldowns()
            p.tick_effects()
            p.defending = False
            # DAWN 免死也检查持续伤害（中毒等）
            if p.hp <= 0 and hasattr(p, 'has_faction_passive') and p.has_faction_passive("DAWN"):
                if not getattr(p, 'dawn_death_save_used', True):
                    p.dawn_death_save_used = True
                    p.hp = 1
                    log.append(f"☀️ [{p.name}] 晨曦加护抵挡了致命的中毒伤害！")
        self.enemy.tick_effects()
        self.turn += 1

    def get_rewards(self) -> Dict:
        """获取战斗奖励。每个玩家获得相同XP和金币，Boss战额外掉落装备和暗影精华。"""
        xp = self.enemy.xp_reward
        settings = get_difficulty_settings()
        gold = int(self.enemy.gold_reward * settings["gold_mult"])
        rewards = {"xp": xp, "gold": gold}
        if self.enemy.is_boss:
            rewards["loot"] = "boss"
            # Boss战奖励暗影精华
            rewards["shadow_essence"] = 2
        return rewards
