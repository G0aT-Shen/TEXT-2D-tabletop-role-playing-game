"""骰子系统 — D20/D100 检定，大成功/大失败判定."""

import random
from enum import Enum
from typing import Tuple


class RollResult(Enum):
    CRITICAL_SUCCESS = "critical_success"  # D20=20: 大成功
    SUCCESS = "success"                     # >= DC
    FAILURE = "failure"                     # < DC
    CRITICAL_FAILURE = "critical_failure"   # D20=1: 大失败


class Dice:
    """骰子工具类。"""

    @staticmethod
    def roll(sides: int) -> int:
        """投掷一个 sides 面骰子，返回 1~sides。"""
        return random.randint(1, sides)

    @staticmethod
    def d20() -> int:
        return Dice.roll(20)

    @staticmethod
    def d100() -> int:
        return Dice.roll(100)

    @staticmethod
    def d6() -> int:
        return Dice.roll(6)

    @staticmethod
    def d8() -> int:
        return Dice.roll(8)

    @staticmethod
    def check(dc: int, modifier: int = 0) -> Tuple[RollResult, int, int]:
        """难度检定。

        Args:
            dc: 目标难度等级 (Difficulty Class)
            modifier: 属性/技能加值

        Returns:
            (RollResult, natural_roll, total): 判定结果、原始出目、总结果
        """
        natural = Dice.d20()

        if natural == 20:
            return RollResult.CRITICAL_SUCCESS, natural, natural + modifier
        if natural == 1:
            return RollResult.CRITICAL_FAILURE, natural, natural + modifier

        total = natural + modifier
        if total >= dc:
            return RollResult.SUCCESS, natural, total
        else:
            return RollResult.FAILURE, natural, total

    @staticmethod
    def contest(mod_a: int, mod_b: int) -> Tuple[RollResult, int, int, int]:
        """对抗检定：双方各投 D20 + 加值，比较大小。

        Returns:
            (result_for_a, roll_a, roll_b, diff): A的结果、A出目、B出目、差值
        """
        roll_a = Dice.d20()
        roll_b = Dice.d20()
        total_a = roll_a + mod_a
        total_b = roll_b + mod_b

        if roll_a == 20:
            return RollResult.CRITICAL_SUCCESS, roll_a, roll_b, total_a - total_b
        if roll_a == 1:
            return RollResult.CRITICAL_FAILURE, roll_a, roll_b, total_a - total_b
        if roll_b == 20:
            return RollResult.CRITICAL_FAILURE, roll_a, roll_b, total_a - total_b
        if roll_b == 1:
            return RollResult.CRITICAL_SUCCESS, roll_a, roll_b, total_a - total_b

        if total_a >= total_b:
            return RollResult.SUCCESS, roll_a, roll_b, total_a - total_b
        else:
            return RollResult.FAILURE, roll_a, roll_b, total_a - total_b

    @staticmethod
    def result_text(result: RollResult) -> str:
        """获取检定结果的中文描述。"""
        mapping = {
            RollResult.CRITICAL_SUCCESS: "✨ 大成功！",
            RollResult.SUCCESS: "✅ 成功",
            RollResult.FAILURE: "❌ 失败",
            RollResult.CRITICAL_FAILURE: "💀 大失败！",
        }
        return mapping[result]

    @staticmethod
    def luck_check(luck: int) -> Tuple[RollResult, int]:
        """幸运检定：投 D100，≤ 幸运值即成功。"""
        roll = Dice.d100()
        if roll <= 5:
            return RollResult.CRITICAL_SUCCESS, roll
        if roll >= 96:
            return RollResult.CRITICAL_FAILURE, roll
        if roll <= luck:
            return RollResult.SUCCESS, roll
        return RollResult.FAILURE, roll
