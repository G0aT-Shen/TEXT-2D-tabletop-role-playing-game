import os
import re
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

from game.chapter import ChapterManager
from game.character import Character, CharClass
from game.combat import ENEMY_TEMPLATES
from game.engine import Game
from game.equipment import (
    AFFIX_MAP,
    Equipment,
    EquipmentSlot,
    Rarity,
    generate_equipment,
)
from game.event import Choice, Event, EventManager, EventType
from game.save import load_game, save_game


class EquipmentTests(unittest.TestCase):
    def test_equipment_bonuses_affect_character_once(self):
        player = Character("测试者", CharClass.WARRIOR)
        base_defense = player.defense
        base_strength_mod = player.str_mod
        base_mp = player.stats.max_mp
        equipment = Equipment(
            "测试甲",
            EquipmentSlot.ARMOR,
            Rarity.COMMON,
            base_defense=10,
            stat_bonuses={"str": 4},
            affixes=[AFFIX_MAP["魔力涌动"]],
        )

        player.equip(equipment)

        self.assertEqual(player.defense, base_defense + 10)
        self.assertEqual(player.str_mod, base_strength_mod + 2)
        self.assertEqual(player.stats.max_mp, base_mp + 20)

    def test_save_round_trip_keeps_corrected_equipment_limits(self):
        player = Character("测试者", CharClass.MAGE)
        player.equip(Equipment(
            "测试戒指",
            EquipmentSlot.ACCESSORY_1,
            Rarity.RARE,
            affixes=[AFFIX_MAP["魔力涌动"]],
        ))
        chapter = ChapterManager()

        with tempfile.TemporaryDirectory() as tmp:
            with patch("game.save.SAVE_DIR", tmp):
                self.assertTrue(save_game(1, player.to_dict(), chapter.to_dict()))
                restored = Character.from_dict(load_game(1)["player"])

        self.assertEqual(restored.stats.max_mp, 105)
        self.assertEqual(restored.stats.mp, 105)

    def test_unknown_saved_affix_is_ignored(self):
        equipment = Equipment.from_dict({
            "name": "旧装备",
            "slot": "weapon",
            "rarity": "COMMON",
            "affix_names": ["已删除词缀"],
        })

        self.assertEqual(equipment.affixes, [])

    def test_second_accessory_slot_can_be_generated(self):
        equipment = generate_equipment(
            "WARRIOR",
            preferred_slot=EquipmentSlot.ACCESSORY_2,
            rarity=Rarity.COMMON,
        )

        self.assertEqual(equipment.slot, EquipmentSlot.ACCESSORY_2)


class EventOutcomeTests(unittest.TestCase):
    def setUp(self):
        self.player = Character("测试者", CharClass.WARRIOR)
        self.player.hp = 100
        self.choice = Choice(
            text="检定",
            result_text="结果",
            check_type="str",
            success_text="成功",
            failure_text="失败",
            critical_success_text="大成功",
            critical_failure_text="大失败",
            hp_change=-10,
            xp_reward=20,
            item_reward="圣水",
        )
        self.event = Event("test", "测试", "", EventType.DICE_CHECK, [self.choice])

    def execute_with_roll(self, result, natural):
        with patch("game.event.Dice.check", return_value=(result, natural, natural + 3)):
            return EventManager(self.player).execute_choice(self.event, 0)

    def test_success_does_not_apply_critical_rewards_or_penalties(self):
        from game.dice import RollResult

        result = self.execute_with_roll(RollResult.SUCCESS, 12)

        self.assertEqual(self.player.hp, 100)
        self.assertEqual(self.player.xp, 20)
        self.assertEqual(self.player.items, [])
        self.assertIsNone(result["item_reward"])

    def test_critical_success_awards_item_and_double_xp(self):
        from game.dice import RollResult

        self.execute_with_roll(RollResult.CRITICAL_SUCCESS, 20)

        self.assertEqual(self.player.hp, 100)
        self.assertEqual(self.player.xp, 40)
        self.assertEqual(self.player.items[0]["name"], "圣水")

    def test_critical_failure_applies_declared_penalty_only(self):
        from game.dice import RollResult

        result = self.execute_with_roll(RollResult.CRITICAL_FAILURE, 1)

        self.assertEqual(self.player.hp, 90)
        self.assertEqual(self.player.xp, 0)
        self.assertEqual(self.player.items, [])
        self.assertEqual(result["hp_change"], -10)

    def test_normal_failure_has_no_critical_penalty(self):
        from game.dice import RollResult

        self.execute_with_roll(RollResult.FAILURE, 5)

        self.assertEqual(self.player.hp, 100)
        self.assertEqual(self.player.xp, 0)
        self.assertEqual(self.player.items, [])


class ContentAndProgressionTests(unittest.TestCase):
    def test_all_story_combat_references_exist(self):
        manager = ChapterManager()
        event_ids = []
        for chapter in manager.chapters:
            for event in chapter.events:
                event_ids.append(event.event_id)
                for choice in event.choices:
                    if choice.trigger_combat:
                        self.assertIn(choice.combat_enemy, ENEMY_TEMPLATES)
        self.assertEqual(len(event_ids), len(set(event_ids)))

    def test_displayed_dc_matches_check_data(self):
        manager = ChapterManager()
        for chapter in manager.chapters:
            for event in chapter.events:
                for choice in event.choices:
                    match = re.search(r"DC\s*[=：:]?\s*(\d+)", choice.text, re.IGNORECASE)
                    if match and choice.check_type:
                        self.assertEqual(
                            int(match.group(1)),
                            choice.dc,
                            f"{event.event_id}: {choice.text}",
                        )

    def test_chapter_reward_uses_completed_chapter(self):
        game = Game.__new__(Game)
        game.player = Character("测试者", CharClass.WARRIOR)
        game.player2 = None
        game.multiplayer = False
        game.event_log = []

        game._award_chapter_completion(1)

        self.assertEqual(game.player.faction_reputation["DAWN"], 20)
        self.assertEqual(game.player.faction_reputation["OBSERVER"], 0)

    def test_opening_shop_does_not_mutate_global_stock_templates(self):
        from game.shop import SHOP_CONSUMABLES

        game = Game.__new__(Game)
        game.player = Character("测试者", CharClass.WARRIOR)
        game.chapter_manager = ChapterManager()

        game._open_shop()
        game.shop_items[3].stock = 0
        game._open_shop()

        self.assertEqual(game.shop_items[3].stock, 3)
        self.assertEqual(SHOP_CONSUMABLES[3].stock, 3)


if __name__ == "__main__":
    unittest.main()
