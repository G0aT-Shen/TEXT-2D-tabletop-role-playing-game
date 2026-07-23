"""技能树系统 — 每职业9技能：4基础 + 4进阶（每基础2分支）+ 1终极."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum

from .character import CharClass


@dataclass
class SkillNode:
    """技能树中的一个节点。"""
    id: str                    # 唯一ID，如 "warrior_slash", "warrior_slash_power"
    name: str                  # 技能名
    description: str           # 技能描述
    mp_cost: int               # MP消耗
    cooldown: int              # 冷却回合
    damage_mult: float = 1.0   # 伤害倍率
    heal_amount: int = 0       # 治疗量
    buff_effect: Optional[Dict] = None    # 增益效果
    debuff_effect: Optional[Dict] = None  # 减益效果
    required_level: int = 1    # 需要等级
    parent_id: Optional[str] = None  # 进阶前置技能ID
    branch_name: str = ""      # 分支名称（进阶时选哪个分支）
    is_ultimate: bool = False  # 是否为终极技能
    skill_point_cost: int = 1  # 消耗技能点数


# ═══════════════════════════════════════════════════
# 技能树定义 — 每职业 9 个技能节点
# ═══════════════════════════════════════════════════

SKILL_TREES: Dict[str, List[SkillNode]] = {
    "WARRIOR": [
        # ── 基础技能 (Lv1自动解锁) ──
        SkillNode(
            id="warrior_slash", name="强力斩击",
            description="集中力量进行一次猛攻，伤害×2",
            mp_cost=10, cooldown=2, damage_mult=2.0, required_level=1,
        ),
        # 进阶分支A: 强化斩击（伤害+30%）
        SkillNode(
            id="warrior_slash_power", name="强化斩击",
            description="更强力的一击，伤害×2.6",
            mp_cost=12, cooldown=2, damage_mult=2.6, required_level=3,
            parent_id="warrior_slash", branch_name="威力之道",
        ),
        # 进阶分支B: 精准斩击（命中率+20%）
        SkillNode(
            id="warrior_slash_precise", name="精准斩击",
            description="精准打击要害，伤害×2.0，命中+20%",
            mp_cost=10, cooldown=1, damage_mult=2.0, required_level=3,
            parent_id="warrior_slash", branch_name="精准之道",
            buff_effect={"stat": "hit_bonus", "value": 20, "duration": 1},
        ),

        # ── 基础技能 ──
        SkillNode(
            id="warrior_roar", name="战吼",
            description="发出震天战吼，提升自身攻击力2回合",
            mp_cost=15, cooldown=3, required_level=2,
            buff_effect={"stat": "strength", "value": 4, "duration": 2},
        ),
        # 进阶A: 战争咆哮（全队受益）
        SkillNode(
            id="warrior_roar_team", name="战争咆哮",
            description="战吼鼓舞全队，所有队友攻击力+3持续2回合",
            mp_cost=18, cooldown=3, required_level=4,
            parent_id="warrior_roar", branch_name="指挥官",
            buff_effect={"stat": "strength", "value": 3, "duration": 2, "target": "all"},
        ),
        # 进阶B: 恐惧战吼（敌攻-3）
        SkillNode(
            id="warrior_roar_fear", name="恐惧战吼",
            description="震慑敌人的战吼，敌人攻击力-3持续2回合",
            mp_cost=15, cooldown=3, required_level=4,
            parent_id="warrior_roar", branch_name="威慑者",
            debuff_effect={"type": "attack_down", "value": 3, "duration": 2},
        ),

        # ── Lv4 基础技能（二选一分支） ──
        # 分支A: 旋风斩
        SkillNode(
            id="warrior_whirlwind", name="旋风斩",
            description="旋转攻击，伤害×1.5",
            mp_cost=20, cooldown=3, damage_mult=1.5, required_level=4,
            parent_id=None,
        ),
        # 分支B: 盾牌猛击
        SkillNode(
            id="warrior_shield_bash", name="盾牌猛击",
            description="盾击敌人，伤害×1.2并眩晕1回合",
            mp_cost=18, cooldown=3, damage_mult=1.2, required_level=4,
            parent_id=None, branch_name="防御大师",
            debuff_effect={"type": "stun", "duration": 1},
        ),

        # ── 基础技能 ──
        SkillNode(
            id="warrior_will", name="不屈意志",
            description="回复自身30%最大生命值",
            mp_cost=25, cooldown=5, heal_amount=30, required_level=6,
        ),
        # 进阶A: 钢铁意志（免疫眩晕）
        SkillNode(
            id="warrior_will_iron", name="钢铁意志",
            description="钢铁般的意志，回复30%HP并获得眩晕免疫3回合",
            mp_cost=25, cooldown=5, heal_amount=30, required_level=8,
            parent_id="warrior_will", branch_name="钢铁之躯",
            buff_effect={"stat": "stun_immune", "value": 1, "duration": 3},
        ),
        # 进阶B: 绝境反击（HP<30%伤害×2）
        SkillNode(
            id="warrior_will_counter", name="绝境反击",
            description="回复20%HP，若HP<30%则下回合伤害翻倍",
            mp_cost=22, cooldown=4, heal_amount=20, required_level=8,
            parent_id="warrior_will", branch_name="绝境求生",
            buff_effect={"stat": "low_hp_boost", "value": 2, "duration": 1},
        ),

        # ── 终极技能 ──
        SkillNode(
            id="warrior_ultimate", name="战神降临",
            description="化身战神，全属性+3，伤害×2.5持续2回合",
            mp_cost=40, cooldown=8, damage_mult=2.5, required_level=8,
            is_ultimate=True, skill_point_cost=3,
            buff_effect={"stat": "all_stats", "value": 3, "duration": 2},
        ),
    ],

    "ASSASSIN": [
        # ── 基础 ──
        SkillNode(
            id="assassin_murder", name="暗杀术",
            description="瞄准要害的致命一击，伤害×2.5",
            mp_cost=12, cooldown=3, damage_mult=2.5, required_level=1,
        ),
        SkillNode(
            id="assassin_murder_crit", name="致命暗杀",
            description="暴击伤害提升至×3.0",
            mp_cost=14, cooldown=3, damage_mult=3.0, required_level=3,
            parent_id="assassin_murder", branch_name="致命一击",
        ),
        SkillNode(
            id="assassin_murder_poison", name="剧毒暗杀",
            description="伤害×2.5并附加中毒(8×3回合)",
            mp_cost=13, cooldown=3, damage_mult=2.5, required_level=3,
            parent_id="assassin_murder", branch_name="淬毒大师",
            debuff_effect={"type": "poison", "damage": 8, "duration": 3},
        ),

        # ── 基础 ──
        SkillNode(
            id="assassin_stealth", name="潜行",
            description="隐匿身形，下次攻击必定暴击",
            mp_cost=10, cooldown=2, required_level=2,
            buff_effect={"stat": "guaranteed_crit", "value": 1, "duration": 1},
        ),
        SkillNode(
            id="assassin_stealth_double", name="双重暗杀",
            description="潜行后下次攻击可连击两次",
            mp_cost=12, cooldown=3, required_level=4,
            parent_id="assassin_stealth", branch_name="连击流",
            buff_effect={"stat": "double_attack", "value": 1, "duration": 1},
        ),
        SkillNode(
            id="assassin_stealth_vanish", name="完全隐匿",
            description="潜行同时完全回避下次攻击",
            mp_cost=10, cooldown=2, required_level=4,
            parent_id="assassin_stealth", branch_name="闪避流",
            buff_effect={"stat": "dodge_next", "value": 1, "duration": 1},
        ),

        # ── Lv4基础 ──
        SkillNode(
            id="assassin_dagger", name="淬毒飞刃",
            description="投掷毒刃，伤害×1.2并中毒(5×3)",
            mp_cost=15, cooldown=2, damage_mult=1.2, required_level=4,
            debuff_effect={"type": "poison", "damage": 5, "duration": 3},
        ),
        SkillNode(
            id="assassin_shuriken", name="影之手里剑",
            description="投掷三枚手里剑，伤害×0.8×3次",
            mp_cost=20, cooldown=4, damage_mult=2.4, required_level=4,
            parent_id=None, branch_name="忍术大师",
        ),

        # ── 基础 ──
        SkillNode(
            id="assassin_shadow", name="影遁",
            description="闪入暗影，完全回避下次攻击",
            mp_cost=20, cooldown=4, required_level=6,
            buff_effect={"stat": "dodge_next", "value": 1, "duration": 1},
        ),
        SkillNode(
            id="assassin_shadow_regen", name="暗影再生",
            description="影遁时回复15%HP",
            mp_cost=20, cooldown=4, heal_amount=15, required_level=8,
            parent_id="assassin_shadow", branch_name="暗影治疗",
            buff_effect={"stat": "dodge_next", "value": 1, "duration": 1},
        ),
        SkillNode(
            id="assassin_shadow_strike", name="影袭反杀",
            description="回避后自动反击100%伤害",
            mp_cost=22, cooldown=4, required_level=8,
            parent_id="assassin_shadow", branch_name="反杀专家",
            buff_effect={"stat": "counter_strike", "value": 100, "duration": 1},
        ),

        # ── 终极 ──
        SkillNode(
            id="assassin_ultimate", name="影杀阵",
            description="在敌人身边布下暗影杀阵，造成×4.0伤害",
            mp_cost=45, cooldown=8, damage_mult=4.0, required_level=8,
            is_ultimate=True, skill_point_cost=3,
        ),
    ],

    "KNIGHT": [
        # 基础
        SkillNode(
            id="knight_bash", name="盾击",
            description="盾牌猛击，伤害×1.0并眩晕1回合",
            mp_cost=10, cooldown=2, damage_mult=1.0, required_level=1,
            debuff_effect={"type": "stun", "duration": 1},
        ),
        SkillNode(
            id="knight_bash_power", name="重盾猛击",
            description="更重的盾击，伤害×1.5并眩晕2回合",
            mp_cost=14, cooldown=3, damage_mult=1.5, required_level=3,
            parent_id="knight_bash", branch_name="重盾流",
            debuff_effect={"type": "stun", "duration": 2},
        ),
        SkillNode(
            id="knight_bash_heal", name="圣盾守护",
            description="盾击造成伤害同时回复自身8HP",
            mp_cost=12, cooldown=2, damage_mult=1.0, heal_amount=8, required_level=3,
            parent_id="knight_bash", branch_name="圣盾流",
            debuff_effect={"type": "stun", "duration": 1},
        ),

        # 基础
        SkillNode(
            id="knight_vow", name="守护誓言",
            description="展开防护结界，减免50%伤害2回合",
            mp_cost=20, cooldown=3, required_level=2,
            buff_effect={"stat": "damage_reduction", "value": 50, "duration": 2},
        ),
        SkillNode(
            id="knight_vow_all", name="神圣庇护",
            description="全队伤害减免40%持续2回合",
            mp_cost=25, cooldown=4, required_level=4,
            parent_id="knight_vow", branch_name="团队守护",
            buff_effect={"stat": "damage_reduction", "value": 40, "duration": 2, "target": "all"},
        ),
        SkillNode(
            id="knight_vow_thorns", name="荆棘誓言",
            description="减免50%伤害同时反弹10伤害",
            mp_cost=22, cooldown=3, required_level=4,
            parent_id="knight_vow", branch_name="荆棘守护",
            buff_effect={"stat": "damage_reduction", "value": 50, "duration": 2},
        ),

        # Lv4基础
        SkillNode(
            id="knight_judgment", name="圣光审判",
            description="神圣之力审判敌人，伤害×1.5",
            mp_cost=15, cooldown=2, damage_mult=1.5, required_level=4,
        ),
        SkillNode(
            id="knight_heal", name="圣愈之光",
            description="放弃攻击，治疗全队25HP",
            mp_cost=18, cooldown=2, heal_amount=25, required_level=4,
            parent_id=None, branch_name="治愈骑士",
        ),

        # 基础
        SkillNode(
            id="knight_sacrifice", name="牺牲守护",
            description="为全队承受伤害并回复20%HP",
            mp_cost=25, cooldown=4, heal_amount=20, required_level=6,
            buff_effect={"stat": "taunt", "value": 1, "duration": 1},
        ),
        SkillNode(
            id="knight_sacrifice_immune", name="圣盾牺牲",
            description="承受全队伤害且自身减免30%",
            mp_cost=28, cooldown=4, heal_amount=20, required_level=8,
            parent_id="knight_sacrifice", branch_name="不屈守护",
            buff_effect={"stat": "taunt", "value": 1, "duration": 1},
        ),
        SkillNode(
            id="knight_sacrifice_thorns", name="反伤牺牲",
            description="承受伤害并反弹所受伤害的50%",
            mp_cost=25, cooldown=4, heal_amount=15, required_level=8,
            parent_id="knight_sacrifice", branch_name="复仇守护",
            buff_effect={"stat": "taunt", "value": 1, "duration": 1},
        ),

        # 终极
        SkillNode(
            id="knight_ultimate", name="圣殿守护",
            description="召唤圣殿之光，全队无敌1回合并回复40%HP",
            mp_cost=50, cooldown=10, heal_amount=40, required_level=8,
            is_ultimate=True, skill_point_cost=3,
            buff_effect={"stat": "invincible", "value": 1, "duration": 1, "target": "all"},
        ),
    ],

    "PRIEST": [
        # 基础
        SkillNode(
            id="priest_heal", name="治愈之光",
            description="神圣之光治愈伤口，回复大量HP",
            mp_cost=15, cooldown=1, heal_amount=40, required_level=1,
        ),
        SkillNode(
            id="priest_heal_greater", name="圣疗术",
            description="更强的治愈，回复60HP",
            mp_cost=20, cooldown=1, heal_amount=60, required_level=3,
            parent_id="priest_heal", branch_name="大治疗",
        ),
        SkillNode(
            id="priest_heal_regen", name="治愈之泉",
            description="回复30HP并在3回合内每回合回复10HP",
            mp_cost=18, cooldown=2, heal_amount=30, required_level=3,
            parent_id="priest_heal", branch_name="持续治疗",
            buff_effect={"stat": "regen", "value": 10, "duration": 3},
        ),

        # 基础
        SkillNode(
            id="priest_exorcism", name="驱魔",
            description="圣光驱散邪恶，对恶魔伤害×2",
            mp_cost=12, cooldown=2, damage_mult=2.0, required_level=2,
        ),
        SkillNode(
            id="priest_exorcism_holy", name="圣光裁决",
            description="对恶魔伤害×3，其他敌人×1.5",
            mp_cost=15, cooldown=2, damage_mult=3.0, required_level=4,
            parent_id="priest_exorcism", branch_name="审判者",
        ),
        SkillNode(
            id="priest_exorcism_cleanse", name="净化驱魔",
            description="伤害×1.8并驱散敌人增益",
            mp_cost=14, cooldown=2, damage_mult=1.8, required_level=4,
            parent_id="priest_exorcism", branch_name="净化者",
        ),

        # Lv4基础
        SkillNode(
            id="priest_blessing", name="神圣祝福",
            description="祝福队友，全属性+2持续3回合",
            mp_cost=18, cooldown=3, required_level=4,
            buff_effect={"stat": "all_stats", "value": 2, "duration": 3},
        ),
        SkillNode(
            id="priest_smite", name="神圣惩击",
            description="以圣光惩戒敌人，伤害×2.0",
            mp_cost=16, cooldown=2, damage_mult=2.0, required_level=4,
            parent_id=None, branch_name="战斗牧师",
        ),

        # 基础
        SkillNode(
            id="priest_purify", name="净化圣言",
            description="群体治疗+解除所有负面状态",
            mp_cost=30, cooldown=4, heal_amount=25, required_level=6,
        ),
        SkillNode(
            id="priest_purify_shield", name="圣言护盾",
            description="群体治疗25HP并附加30护盾2回合",
            mp_cost=32, cooldown=4, heal_amount=25, required_level=8,
            parent_id="priest_purify", branch_name="护盾圣言",
        ),
        SkillNode(
            id="priest_purify_revive", name="复活圣言",
            description="群体治疗15HP并可复活一名队友(50%HP)",
            mp_cost=40, cooldown=6, heal_amount=15, required_level=8,
            parent_id="priest_purify", branch_name="复活圣言",
            buff_effect={"stat": "revive", "value": 50, "duration": 1},
        ),

        # 终极
        SkillNode(
            id="priest_ultimate", name="神之恩典",
            description="召唤神之恩典，全队满血并全属性永久+1",
            mp_cost=60, cooldown=12, heal_amount=100, required_level=8,
            is_ultimate=True, skill_point_cost=3,
        ),
    ],

    "MAGE": [
        # 基础
        SkillNode(
            id="mage_fireball", name="火球术",
            description="凝聚火焰投掷，伤害×2",
            mp_cost=12, cooldown=1, damage_mult=2.0, required_level=1,
        ),
        SkillNode(
            id="mage_fireball_big", name="炎爆术",
            description="巨大的火球，伤害×3.0",
            mp_cost=18, cooldown=2, damage_mult=3.0, required_level=3,
            parent_id="mage_fireball", branch_name="火焰大师",
        ),
        SkillNode(
            id="mage_fireball_chain", name="连锁火球",
            description="火球在敌人间弹射，伤害×1.5(对Boss×2.5)",
            mp_cost=14, cooldown=1, damage_mult=1.5, required_level=3,
            parent_id="mage_fireball", branch_name="元素连锁",
        ),

        # 基础
        SkillNode(
            id="mage_barrier", name="奥术屏障",
            description="展开魔法屏障，吸收30伤害",
            mp_cost=15, cooldown=3, required_level=2,
            buff_effect={"stat": "shield", "value": 30, "duration": 2},
        ),
        SkillNode(
            id="mage_barrier_reflect", name="反射屏障",
            description="吸收20伤害并反弹50%给敌人",
            mp_cost=18, cooldown=3, required_level=4,
            parent_id="mage_barrier", branch_name="反射大师",
            buff_effect={"stat": "shield", "value": 20, "duration": 2},
        ),
        SkillNode(
            id="mage_barrier_mana", name="法力屏障",
            description="吸收的伤害由MP承担（每MP抵2伤害）",
            mp_cost=8, cooldown=3, required_level=4,
            parent_id="mage_barrier", branch_name="法力护盾",
            buff_effect={"stat": "mana_shield", "value": 1, "duration": 2},
        ),

        # Lv4基础
        SkillNode(
            id="mage_blizzard", name="冰霜风暴",
            description="召唤暴风雪，伤害×1.5+减速",
            mp_cost=20, cooldown=3, damage_mult=1.5, required_level=4,
            debuff_effect={"type": "slow", "duration": 2},
        ),
        SkillNode(
            id="mage_thunder", name="雷暴术",
            description="召唤雷电，伤害×2.0并可能麻痹",
            mp_cost=22, cooldown=3, damage_mult=2.0, required_level=4,
            parent_id=None, branch_name="雷电使者",
            debuff_effect={"type": "stun", "duration": 1},
        ),

        # 基础
        SkillNode(
            id="mage_meteor", name="陨石召唤",
            description="召唤天外陨石，伤害×3.0",
            mp_cost=35, cooldown=5, damage_mult=3.0, required_level=6,
        ),
        SkillNode(
            id="mage_meteor_shower", name="流星雨",
            description="召唤流星雨，伤害×1.8覆盖全场",
            mp_cost=40, cooldown=6, damage_mult=3.6, required_level=8,
            parent_id="mage_meteor", branch_name="天灾召唤",
        ),
        SkillNode(
            id="mage_meteor_void", name="虚空陨石",
            description="虚空陨石无视50%防御，伤害×2.5",
            mp_cost=38, cooldown=5, damage_mult=2.5, required_level=8,
            parent_id="mage_meteor", branch_name="虚空行者",
        ),

        # 终极
        SkillNode(
            id="mage_ultimate", name="元素湮灭",
            description="释放元素之力湮灭一切，伤害×5.0",
            mp_cost=55, cooldown=10, damage_mult=5.0, required_level=8,
            is_ultimate=True, skill_point_cost=3,
        ),
    ],
}


def get_skill_tree(char_class) -> List[SkillNode]:
    """获取指定职业的完整技能树。"""
    if isinstance(char_class, CharClass):
        key = char_class.name
    else:
        key = char_class
    return SKILL_TREES.get(key, [])


def get_base_skills(char_class) -> List[int]:
    """获取基础技能（Lv1-2自动解锁）的索引列表。"""
    tree = get_skill_tree(char_class)
    base_indices = []
    for i, node in enumerate(tree):
        if node.required_level <= 2 and not node.parent_id:
            base_indices.append(i)
    return base_indices


def get_available_branches(tree: List[SkillNode], unlocked_indices: set, level: int) -> List[int]:
    """获取当前可解锁的分支技能索引列表。"""
    available = []
    for i, node in enumerate(tree):
        if i in unlocked_indices:
            continue
        if node.required_level > level:
            continue
        # 有前置的，检查前置是否已解锁
        if node.parent_id and node.parent_id not in {tree[j].id for j in unlocked_indices}:
            continue
        available.append(i)
    return available


def get_branch_children(tree: List[SkillNode], parent_idx: int) -> List[int]:
    """获取某个技能的所有分支子节点索引。"""
    parent = tree[parent_idx]
    children = []
    for i, node in enumerate(tree):
        if node.parent_id == parent.id:
            children.append(i)
    return children
