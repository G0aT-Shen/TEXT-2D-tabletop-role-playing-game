"""核心游戏引擎 — 状态机驱动的完整游戏循环（支持单人/双人）。"""

import random
import re
from enum import Enum, auto
from typing import List

import pygame

from .character import Character, CharClass
from .event import EventType, EventManager
from .combat import CombatEngine, CombatAction, create_enemy
from .chapter import ChapterManager
from .save import save_game, load_game, list_saves, delete_save
from .ui import GameUI, WIDTH, SIDEBAR_X
from .dice import Dice


class GameState(Enum):
    MENU = auto()
    DIFFICULTY_SELECT = auto()
    CREATE_CLASS = auto()
    CREATE_NAME = auto()
    CREATE_CONFIRM = auto()
    CREATE_CLASS_2 = auto()
    CREATE_NAME_2 = auto()
    CREATE_CONFIRM_2 = auto()
    CHAPTER_INTRO = auto()
    PLAY = auto()
    EVENT_RESULT = auto()
    COMBAT = auto()
    COMBAT_RESULT = auto()
    SHOP = auto()
    SKILL_TREE = auto()
    SAVE = auto()
    LOAD = auto()
    CHARACTER_SHEET = auto()
    GAME_OVER = auto()
    GAME_WIN = auto()
    PAUSE = auto()
    ENDING = auto()


class Game:
    """绝夜之旅 — 主游戏类。"""

    def __init__(self):
        self.ui = GameUI()
        self.state = GameState.MENU
        self.running = True

        # 游戏数据
        self.player: Character = None
        self.player2: Character = None
        self.multiplayer: bool = False
        self.chapter_manager = ChapterManager()
        self.event_manager = None
        self.combat: CombatEngine = None

        # 菜单
        self.menu_options = ["新游戏", "双人冒险", "继续游戏", "读取存档", "退出"]
        self.menu_selected = 0
        self.has_saves = len(list_saves()) > 0

        # 角色创建
        self.create_selected_class = 0
        self.create_name = ""
        self.creating_player_label = 1  # "玩家1" or "玩家2"

        # 事件
        self.event_result_data = None
        self.event_log = []
        self.selected_choice = 0

        # 战斗
        self.combat_action_phase = "action"
        self.combat_selected_action = 0
        self.combat_selected_skill = 0
        self.combat_result = None

        # 存档
        self.save_mode = "save"
        self.save_selected = 0
        self.save_message = ""

        # 结局
        self.ending_choice = 0

        # ── Phase 2 新系统 ──
        # 难度选择
        self.selected_difficulty = 0
        self.difficulty_options = ["简单", "标准", "硬核"]
        # 商店
        self.shop_items = []
        self.shop_selected = 0
        self.shop_message = ""
        # 技能树
        self.skill_tree_selected = 0
        self.skill_tree_message = ""

    def _all_players(self) -> List[Character]:
        """返回所有玩家列表。"""
        players = [self.player]
        if self.multiplayer and self.player2:
            players.append(self.player2)
        return players

    def _all_alive(self) -> bool:
        return all(p.is_alive for p in self._all_players())

    # ═══════════════════════════════════════════
    # 主循环
    # ═══════════════════════════════════════════

    def run(self):
        while self.running:
            self._handle_events()
            self._update()
            self._render()
            self.ui.update_display()

        self.ui.cleanup()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            if event.type == pygame.TEXTINPUT:
                self._handle_textinput(event)

    def _handle_textinput(self, event):
        if self.state in (GameState.CREATE_NAME, GameState.CREATE_NAME_2):
            self.create_name += event.text

    def _handle_keydown(self, event):
        key = event.key
        if key == pygame.K_ESCAPE:
            self._handle_escape()
            return

        handlers = {
            GameState.MENU: self._handle_menu_input,
            GameState.DIFFICULTY_SELECT: self._handle_difficulty_input,
            GameState.CREATE_CLASS: self._handle_create_class_input,
            GameState.CREATE_NAME: self._handle_create_name_input,
            GameState.CREATE_CONFIRM: self._handle_create_confirm_input,
            GameState.CREATE_CLASS_2: self._handle_create_class_input,
            GameState.CREATE_NAME_2: self._handle_create_name_input,
            GameState.CREATE_CONFIRM_2: self._handle_create_confirm_input,
            GameState.CHAPTER_INTRO: self._handle_chapter_intro_input,
            GameState.PLAY: self._handle_play_input,
            GameState.EVENT_RESULT: self._handle_event_result_input,
            GameState.COMBAT: self._handle_combat_input,
            GameState.COMBAT_RESULT: self._handle_combat_result_input,
            GameState.SHOP: self._handle_shop_input,
            GameState.SKILL_TREE: self._handle_skill_tree_input,
            GameState.SAVE: self._handle_save_input,
            GameState.LOAD: self._handle_load_input,
            GameState.CHARACTER_SHEET: self._handle_character_sheet_input,
            GameState.GAME_OVER: self._handle_game_over_input,
            GameState.GAME_WIN: self._handle_game_win_input,
            GameState.ENDING: self._handle_ending_input,
        }
        handler = handlers.get(self.state)
        if handler:
            handler(key)

    def _handle_escape(self):
        if self.state == GameState.MENU:
            self.running = False
        elif self.state == GameState.PLAY:
            self.state = GameState.PAUSE
        elif self.state == GameState.PAUSE:
            self.state = GameState.PLAY
        elif self.state == GameState.SHOP:
            self._advance_event()
        elif self.state == GameState.SKILL_TREE:
            self.state = GameState.CHARACTER_SHEET
        elif self.state in (GameState.CREATE_NAME, GameState.CREATE_NAME_2):
            pygame.key.stop_text_input()
            prev = GameState.CREATE_CLASS_2 if self.state == GameState.CREATE_NAME_2 else GameState.CREATE_CLASS
            self.state = prev
        elif self.state in (GameState.CREATE_CONFIRM, GameState.CREATE_CONFIRM_2):
            prev = GameState.CREATE_NAME_2 if self.state == GameState.CREATE_CONFIRM_2 else GameState.CREATE_NAME
            self.state = prev
            self.ui.input_active = True
            pygame.key.start_text_input()
        elif self.state == GameState.COMBAT and self.combat_action_phase in ("skill", "item"):
            self.combat_action_phase = "action"
        elif self.state == GameState.SAVE:
            self.state = GameState.PLAY
        elif self.state == GameState.LOAD:
            self.state = GameState.MENU
            self.menu_selected = 0
        elif self.state == GameState.CHARACTER_SHEET:
            self.state = GameState.PLAY
        elif self.state == GameState.CHAPTER_INTRO:
            pass

    # ═══════════════════════════════════════════
    # 输入处理
    # ═══════════════════════════════════════════

    def _handle_menu_input(self, key):
        if key == pygame.K_UP:
            self.menu_selected = (self.menu_selected - 1) % len(self.menu_options)
        elif key == pygame.K_DOWN:
            self.menu_selected = (self.menu_selected + 1) % len(self.menu_options)
        elif key == pygame.K_RETURN:
            option = self.menu_options[self.menu_selected]
            if option == "新游戏":
                self.multiplayer = False
                self._start_new_game()
            elif option == "双人冒险":
                self.multiplayer = True
                self._start_new_game()
            elif option == "继续游戏":
                self._continue_game()
            elif option == "读取存档":
                self.state = GameState.LOAD
                self.save_selected = 0
            elif option == "退出":
                self.running = False

    def _handle_create_class_input(self, key):
        classes = list(CharClass)
        if key == pygame.K_LEFT:
            self.create_selected_class = (self.create_selected_class - 1) % len(classes)
        elif key == pygame.K_RIGHT:
            self.create_selected_class = (self.create_selected_class + 1) % len(classes)
        elif key == pygame.K_RETURN:
            next_name_state = GameState.CREATE_NAME_2 if self.state == GameState.CREATE_CLASS_2 else GameState.CREATE_NAME
            self.state = next_name_state
            self.ui.input_active = True
            self.create_name = ""
            pygame.key.start_text_input()

    def _handle_create_name_input(self, key):
        if key == pygame.K_BACKSPACE:
            self.create_name = self.create_name[:-1]
        elif key == pygame.K_RETURN:
            if self.create_name.strip():
                pygame.key.stop_text_input()
                next_confirm = GameState.CREATE_CONFIRM_2 if self.state == GameState.CREATE_NAME_2 else GameState.CREATE_CONFIRM
                self.state = next_confirm
                self.ui.input_active = False

    def _handle_create_confirm_input(self, key):
        if key == pygame.K_RETURN:
            char_class = list(CharClass)[self.create_selected_class]
            char = Character(self.create_name.strip(), char_class)

            if self.state == GameState.CREATE_CONFIRM_2:
                # 创建玩家2，然后选择难度
                self.player2 = char
                self.chapter_manager = ChapterManager()
                self.event_manager = EventManager(self.player)
                self.state = GameState.DIFFICULTY_SELECT
                self.selected_difficulty = 1
            else:
                # 创建玩家1
                self.player = char
                if self.multiplayer:
                    # 继续创建玩家2
                    self.creating_player_label = 2
                    self.create_selected_class = 0
                    self.create_name = ""
                    self.state = GameState.CREATE_CLASS_2
                else:
                    self.chapter_manager = ChapterManager()
                    self.event_manager = EventManager(self.player)
                    self.state = GameState.DIFFICULTY_SELECT
                    self.selected_difficulty = 1
        elif key == pygame.K_BACKSPACE:
            prev = GameState.CREATE_NAME_2 if self.state == GameState.CREATE_CONFIRM_2 else GameState.CREATE_NAME
            self.state = prev
            self.ui.input_active = True
            pygame.key.start_text_input()

    def _handle_chapter_intro_input(self, key):
        if key == pygame.K_RETURN:
            self.state = GameState.PLAY
            self.event_log = []
            self.selected_choice = 0

    def _handle_difficulty_input(self, key):
        if key == pygame.K_UP:
            self.selected_difficulty = (self.selected_difficulty - 1) % 3
        elif key == pygame.K_DOWN:
            self.selected_difficulty = (self.selected_difficulty + 1) % 3
        elif key == pygame.K_RETURN:
            diff_key = ["easy", "normal", "hard"][self.selected_difficulty]
            from .combat import set_difficulty
            set_difficulty(diff_key)
            self._start_chapter_intro()

    def _handle_play_input(self, key):
        event_obj = self.chapter_manager.current_event
        if not event_obj or not event_obj.choices:
            return

        num_choices = len(event_obj.choices)
        if key == pygame.K_UP:
            self.selected_choice = (self.selected_choice - 1) % num_choices
        elif key == pygame.K_DOWN:
            self.selected_choice = (self.selected_choice + 1) % num_choices
        elif key == pygame.K_RETURN:
            self._execute_event_choice()
        elif key == pygame.K_s:
            self.save_mode = "save"
            self.save_selected = 1
            self.state = GameState.SAVE
        elif key == pygame.K_c:
            self.state = GameState.CHARACTER_SHEET

    def _handle_event_result_input(self, key):
        if key == pygame.K_RETURN or key == pygame.K_SPACE:
            if self.event_result_data and self.event_result_data.get("combat"):
                self._start_combat(self.event_result_data["combat"])
                return
            self._advance_event()

    def _handle_combat_input(self, key):
        if not self.combat:
            return

        player_idx = self.combat.current_player_index
        current_p = self.combat.current_player

        if self.combat_action_phase == "action":
            if key == pygame.K_UP:
                self.combat_selected_action = (self.combat_selected_action - 1) % 5
            elif key == pygame.K_DOWN:
                self.combat_selected_action = (self.combat_selected_action + 1) % 5
            elif key == pygame.K_RETURN:
                if self.combat_selected_action == 0:  # 攻击
                    self.combat.player_action(player_idx, CombatAction.ATTACK)
                    self._after_combat_action()
                elif self.combat_selected_action == 1:  # 技能
                    self.combat_action_phase = "skill"
                    self.combat_selected_skill = 0
                elif self.combat_selected_action == 2:  # 防御
                    self.combat.player_action(player_idx, CombatAction.DEFEND)
                    self._after_combat_action()
                elif self.combat_selected_action == 3:  # 道具
                    if current_p.items:
                        self.combat_action_phase = "item"
                        self.combat_selected_skill = 0
                    else:
                        self.combat.log.append(f"🎒 [{current_p.name}] 背包为空！")
                elif self.combat_selected_action == 4:  # 逃跑
                    luck_result, _ = Dice.luck_check(current_p.stats.luck)
                    if luck_result.value in ("critical_success", "success"):
                        self.combat.escaped = True
                        self.combat.combat_over = True
                        self.combat.log.append(f"🏃 [{current_p.name}] 成功逃离了战斗！")
                        self.combat_result = None
                        self.state = GameState.COMBAT_RESULT
                    else:
                        self.combat.log.append(f"❌ [{current_p.name}] 逃跑失败！")
                        self._after_combat_action()

        elif self.combat_action_phase == "skill":
            # 只显示已解锁的技能
            unlocked_indices = [i for i, s in enumerate(current_p.skills) if not s.is_locked]
            if not unlocked_indices:
                self.combat.log.append(f"📜 [{current_p.name}] 没有可用技能！")
                self.combat_action_phase = "action"
                return
            if key == pygame.K_UP:
                self.combat_selected_skill = (self.combat_selected_skill - 1) % len(unlocked_indices)
            elif key == pygame.K_DOWN:
                self.combat_selected_skill = (self.combat_selected_skill + 1) % len(unlocked_indices)
            elif key == pygame.K_RETURN:
                real_idx = unlocked_indices[self.combat_selected_skill]
                self.combat.player_action(player_idx, CombatAction.SKILL, real_idx)
                self.combat_action_phase = "action"
                self._after_combat_action()

        elif self.combat_action_phase == "item":
            items = current_p.items
            if key == pygame.K_UP:
                self.combat_selected_skill = (self.combat_selected_skill - 1) % len(items)
            elif key == pygame.K_DOWN:
                self.combat_selected_skill = (self.combat_selected_skill + 1) % len(items)
            elif key == pygame.K_RETURN:
                item = current_p.use_item(self.combat_selected_skill)
                if item:
                    from .items import use_item
                    result_text = use_item(item, current_p, self.combat.log, self.combat.enemy)
                    self.combat.log.append(result_text)
                self.combat.player_action(player_idx, CombatAction.ITEM)
                self.combat_action_phase = "action"
                self._after_combat_action()

    def _after_combat_action(self):
        """战斗行动后：触发视觉特效并检查是否结束。"""
        self._trigger_combat_effects()
        self._check_combat_end()

    def _trigger_combat_effects(self):
        """根据最新战斗日志触发视觉特效。"""
        if not self.combat or not hasattr(self.ui, 'combat_hit_effect'):
            return

        for line in self.combat.log[-5:]:
            # 暴击伤害
            if "暴击" in line:
                if "造成" in line:
                    # 提取伤害值
                    match = re.search(r'造成\s*(\d+)\s*点伤害', line)
                    dmg = int(match.group(1)) if match else 30
                    self.ui.combat_hit_effect(
                        WIDTH // 3, 200, dmg, is_critical=True
                    )
            # 普通伤害
            elif "造成" in line and "点伤害" in line:
                match = re.search(r'造成\s*(\d+)\s*点伤害', line)
                if match:
                    dmg = int(match.group(1))
                    self.ui.combat_hit_effect(
                        WIDTH // 3 + random.randint(-40, 40),
                        200 + random.randint(-20, 20),
                        dmg, is_critical=False
                    )
            # 受到伤害（玩家受伤）
            elif "受到" in line and "点伤害" in line:
                match = re.search(r'受到\s*(\d+)\s*点伤害', line)
                if match:
                    dmg = int(match.group(1))
                    # 在角色栏附近
                    self.ui.combat_hit_effect(
                        SIDEBAR_X + 80, 200 + random.randint(-20, 20),
                        dmg, is_critical=False
                    )
            # 治疗
            elif "回复" in line:
                match = re.search(r'回复\s*(\d+)', line)
                if match:
                    amt = int(match.group(1))
                    self.ui.combat_heal_effect(
                        SIDEBAR_X + 80, 180, amt
                    )
            # 未命中（敌方失误）
            elif "失误" in line:
                self.ui.combat_miss_effect(
                    WIDTH // 3 + random.randint(-40, 40),
                    200
                )
            # 攻击未命中
            elif "未命中" in line:
                self.ui.combat_miss_effect(
                    WIDTH // 3, 220
                )

    def _handle_combat_result_input(self, key):
        if key == pygame.K_RETURN:
            if self.combat_result:  # 胜利
                rewards = self.combat.get_rewards()
                xp = rewards["xp"]
                gold = rewards.get("gold", 0)
                for p in self._all_players():
                    p.add_xp(xp)
                    p.gold += gold
                names = ", ".join(p.name for p in self._all_players())
                self.event_log.append(f"⭐ 战斗胜利！{names} 获得 {xp} 经验值")
                if gold > 0:
                    self.event_log.append(f"💰 获得 {gold} 金币")
                # Boss战掉落装备 + 暗影精华
                if rewards.get("loot") == "boss":
                    for p in self._all_players():
                        from .equipment import generate_boss_loot
                        eq = generate_boss_loot(p.char_class.name)
                        old = p.equip(eq)
                        self.event_log.append(f"🎁 [{p.name}] 获得装备: {eq.full_name} (攻+{eq.attack} 防+{eq.defense})")
                        for a in eq.affixes:
                            self.event_log.append(f"   ⚜ {a['name']}: {a['desc']}")
                        if old:
                            self.event_log.append(f"   (卸下: {old.full_name})")
                    se = rewards.get("shadow_essence", 0)
                    if se > 0:
                        for p in self._all_players():
                            p.shadow_essence += se
                        self.event_log.append(f"💎 获得 {se} 暗影精华")
                # 检查是否有列车事件，如果有则打开商店
                self._advance_event()
            elif self.combat_result is False:  # 失败
                self.state = GameState.GAME_OVER
            else:  # 逃跑
                self._advance_event()

    def _handle_save_input(self, key):
        if key == pygame.K_UP:
            self.save_selected = (self.save_selected - 1) % 3
        elif key == pygame.K_DOWN:
            self.save_selected = (self.save_selected + 1) % 3
        elif key == pygame.K_RETURN:
            slot = self.save_selected + 1
            if self.save_mode == "save":
                p2_dict = self.player2.to_dict() if self.player2 else None
                success = save_game(slot, self.player.to_dict(), self.chapter_manager.to_dict(), p2_dict)
                self.save_message = f"✅ 存档成功！槽位 {slot}" if success else "❌ 存档失败"
            elif self.save_mode == "load":
                data = load_game(slot)
                if data:
                    self._load_game_data(data)
                    self.state = GameState.CHAPTER_INTRO
                else:
                    self.save_message = "❌ 该槽位无存档"
        elif key == pygame.K_DELETE:
            slot = self.save_selected + 1
            delete_save(slot)
            self.save_message = f"🗑 存档 {slot} 已删除"

    def _handle_load_input(self, key):
        if key == pygame.K_UP:
            self.save_selected = (self.save_selected - 1) % 3
        elif key == pygame.K_DOWN:
            self.save_selected = (self.save_selected + 1) % 3
        elif key == pygame.K_RETURN:
            slot = self.save_selected + 1
            data = load_game(slot)
            if data:
                self._load_game_data(data)
                self.state = GameState.CHAPTER_INTRO
            else:
                self.save_message = "❌ 该槽位无存档"

    def _handle_character_sheet_input(self, key):
        # 角色详情页中按 T 进入技能树
        if key == pygame.K_t:
            self.state = GameState.SKILL_TREE
            self.skill_tree_selected = 0
            self.skill_tree_message = ""
            return
        # 角色详情页中按 A 进入属性分配
        if key == pygame.K_a:
            self.state = GameState.SKILL_TREE
            self.skill_tree_selected = 0
            self.skill_tree_message = ""
            return
        if key:
            self.state = GameState.PLAY

    def _handle_shop_input(self, key):
        if key == pygame.K_UP:
            self.shop_selected = (self.shop_selected - 1) % len(self.shop_items)
        elif key == pygame.K_DOWN:
            self.shop_selected = (self.shop_selected + 1) % len(self.shop_items)
        elif key == pygame.K_RETURN:
            item = self.shop_items[self.shop_selected]
            from .shop import can_afford
            if item.currency == "gold":
                if self.player.gold >= item.price and item.stock != 0:
                    self.player.gold -= item.price
                    if item.stock > 0:
                        item.stock -= 1
                    self._apply_shop_purchase(item)
                    self.shop_message = f"✅ 购买了 {item.name}！"
                else:
                    self.shop_message = "❌ 金币不足或已售罄"
            elif item.currency == "shadow_essence":
                if self.player.shadow_essence >= item.price and item.stock != 0:
                    self.player.shadow_essence -= item.price
                    if item.stock > 0:
                        item.stock -= 1
                    self._apply_shop_purchase(item)
                    self.shop_message = f"✅ 购买了 {item.name}！"
                else:
                    self.shop_message = "❌ 暗影精华不足或已售罄"
        elif key == pygame.K_ESCAPE:
            self._advance_event()

    def _apply_shop_purchase(self, item):
        """应用商店购买效果。"""
        if item.item_type == "consumable":
            item_name = item.data.get("item_name", "")
            if item_name:
                self.player.add_item(item_name)
        elif item.item_type == "equipment":
            eq = item.data.get("equipment")
            if eq:
                old = self.player.equip(eq)
        elif item.item_type == "info":
            reward = item.data.get("reward", "")
            if reward == "skill_point":
                self.player.skill_points += 1
            elif reward == "attr_points":
                self.player.pending_attr_points += item.data.get("amount", 2)
            elif reward == "legendary_item":
                from .equipment import generate_legendary
                eq = generate_legendary(self.player.char_class.name)
                old = self.player.equip(eq)
                if old:
                    self.player.add_item({"name": old.full_name, "desc": "被替换的装备", "effect": {}})
            elif reward == "full_heal":
                for p in self._all_players():
                    p.hp = p.stats.max_hp
                    p.mp = p.stats.max_mp

    def _handle_skill_tree_input(self, key):
        if key == pygame.K_LEFT:
            self.skill_tree_selected = max(0, self.skill_tree_selected - 1)
        elif key == pygame.K_RIGHT:
            unlocked = self.player.get_unlocked_skills()
            available = self.player.get_available_branches()
            all_display = unlocked + [self.player.skills[i] for i in available]
            if all_display:
                self.skill_tree_selected = min(len(all_display) - 1, self.skill_tree_selected + 1)
        elif key == pygame.K_RETURN:
            available = self.player.get_available_branches()
            if available:
                real_idx = available[self.skill_tree_selected] if self.skill_tree_selected < len(available) else -1
                if real_idx >= 0:
                    if self.player.unlock_skill(real_idx):
                        skill = self.player.skills[real_idx]
                        self.skill_tree_message = f"✅ 解锁了 {skill.name}！"
                    else:
                        self.skill_tree_message = "❌ 无法解锁此技能"
                else:
                    self.skill_tree_message = ""
            else:
                self.skill_tree_message = "没有可解锁的技能"
        # 属性分配（数字键分配）
        attr_keys = {
            pygame.K_1: "strength", pygame.K_2: "dexterity",
            pygame.K_3: "intelligence", pygame.K_4: "wisdom",
            pygame.K_5: "charisma", pygame.K_6: "luck",
        }
        if key in attr_keys:
            if self.player.pending_attr_points > 0:
                attr = attr_keys[key]
                if self.player.allocate_attr(attr):
                    names = {"strength": "力量", "dexterity": "敏捷", "intelligence": "智力",
                             "wisdom": "感知", "charisma": "魅力", "luck": "幸运"}
                    self.skill_tree_message = f"✅ {names[attr]}+1 (剩余{self.player.pending_attr_points}点)"
            else:
                self.skill_tree_message = "没有待分配属性点"
        elif key == pygame.K_ESCAPE or key == pygame.K_q:
            self.state = GameState.CHARACTER_SHEET

    def _handle_game_over_input(self, key):
        if key == pygame.K_RETURN:
            self._return_to_menu()

    def _handle_game_win_input(self, key):
        if key == pygame.K_RETURN:
            self._return_to_menu()
        elif key == pygame.K_n:
            # New Game+!
            self._start_new_game_plus()

    def _handle_ending_input(self, key):
        if key == pygame.K_UP or key == pygame.K_DOWN:
            self.ending_choice = 1 - self.ending_choice
        elif key == pygame.K_RETURN:
            self.state = GameState.GAME_WIN

    # ═══════════════════════════════════════════
    # 游戏逻辑
    # ═══════════════════════════════════════════

    def _start_new_game(self):
        self.create_selected_class = 0
        self.create_name = ""
        self.creating_player_label = 1
        self.state = GameState.CREATE_CLASS

    def _continue_game(self):
        data = load_game(1)
        if data:
            self._load_game_data(data)
            self.state = GameState.CHAPTER_INTRO
        else:
            self._start_new_game()

    def _load_game_data(self, data):
        self.player = Character.from_dict(data["player"])
        self.multiplayer = data.get("multiplayer", False)
        if "player2" in data and data["player2"]:
            self.player2 = Character.from_dict(data["player2"])
        else:
            self.player2 = None
            self.multiplayer = False
        self.chapter_manager = ChapterManager()
        self.chapter_manager.from_dict(data["chapter"])
        self.event_manager = EventManager(self.player)
        self.event_log = []

    def _start_chapter_intro(self):
        self.state = GameState.CHAPTER_INTRO
        ch = self.chapter_manager.current_chapter
        if ch:
            from .scene_renderer import SceneRenderer
            self.ui.set_current_scene(SceneRenderer.scene_for_chapter(ch.chapter_id))
        if ch is None:
            self.state = GameState.GAME_WIN
        self.event_log = []
        self.selected_choice = 0
        if self.player:
            p2_dict = self.player2.to_dict() if self.player2 else None
            save_game(1, self.player.to_dict(), self.chapter_manager.to_dict(), p2_dict)

    def _execute_event_choice(self):
        event_obj = self.chapter_manager.current_event
        if not event_obj:
            return
        if not event_obj.choices:
            self._advance_event()
            return
        if event_obj.event_type == EventType.BOSS:
            choice = event_obj.choices[0]
            if choice.trigger_combat:
                self._start_combat(choice.combat_enemy)
                return

        choice_index = self.selected_choice
        result = self.event_manager.execute_choice(event_obj, choice_index)
        self.event_result_data = result
        self.event_log = self.event_manager.get_event_log()

        # 多人模式：将HP变化分摊到两个玩家
        # 注意：event_manager.execute_choice() 已对主玩家应用了全额 hp_change，
        # 这里需要先撤销再分摊，避免主玩家受到双倍伤害
        if self.multiplayer and self.player2:
            hp_delta = result.get("hp_change", 0)
            if hp_delta < 0:
                # 撤销事件管理器对玩家1施加的全额伤害
                self.player.hp -= hp_delta  # hp_delta 为负，-= 即加回
                # 伤害分摊：各受一半伤害（至少1点）
                per_player = max(1, abs(hp_delta) // 2)
                self.player.hp -= per_player
                self.player2.hp -= per_player
                self.event_log.append(f"💔 [{self.player2.name}] 也受到 {per_player} 点伤害")

        self.state = GameState.EVENT_RESULT

        for k, v in result.get("flags_set", {}).items():
            self.chapter_manager.set_flag(k, v)

    def _advance_event(self):
        self.state = GameState.PLAY
        self.event_log = []
        self.selected_choice = 0
        self.event_result_data = None

        self.chapter_manager.advance_event()

        if self.chapter_manager.is_chapter_complete:
            ch = self.chapter_manager.current_chapter
            if ch and ch.is_final:
                self.state = GameState.ENDING
                return
            self.chapter_manager.advance_chapter()
            # 章节完成奖励：晨曦碎片 + 阵营声望 + 全队回复
            self._award_chapter_completion()
            if self.chapter_manager.is_game_complete:
                self.state = GameState.GAME_WIN
                return
            # 章节切换 → 打开商店
            self._open_shop()
            return

        current = self.chapter_manager.current_event
        # 列车事件 → 打开商店
        if current and current.event_type == EventType.TRAIN:
            self._open_shop()
            return
        if current:
            ch = self.chapter_manager.current_chapter
            chapter_id = ch.chapter_id if ch else 1
            self.ui.set_scene_from_event(current.event_type.value, chapter_id)
        if current and current.event_type == EventType.BOSS and current.choices:
            choice = current.choices[0]
            if choice.trigger_combat:
                self._start_combat(choice.combat_enemy)

    def _open_shop(self):
        """打开神秘商人商店。"""
        from .shop import SHOP_CONSUMABLES, get_equipment_shop_items, SHADOW_ESSENCE_ITEMS
        ch = self.chapter_manager.current_chapter
        chapter_id = ch.chapter_id if ch else 1
        items = list(SHOP_CONSUMABLES)
        # 添加装备
        items.extend(get_equipment_shop_items(chapter_id, self.player.char_class.name))
        # 添加暗影精华商店
        items.extend(SHADOW_ESSENCE_ITEMS)
        self.shop_items = items
        self.shop_selected = 0
        self.shop_message = ""
        self.state = GameState.SHOP

    def _award_chapter_completion(self):
        """章节完成奖励。"""
        # 晨曦碎片：每章1个
        for p in self._all_players():
            p.dawn_shards += 1
        self.event_log.append(f"✨ 获得晨曦碎片！(共{self.player.dawn_shards}块)")
        # 阵营声望：根据章节给予额外声望
        ch = self.chapter_manager.current_chapter
        chapter_id = ch.chapter_id if ch else 1
        if chapter_id == 1:
            faction_bonus = {"DAWN": 20}
        elif chapter_id == 2:
            faction_bonus = {"OBSERVER": 20}
        elif chapter_id == 3:
            faction_bonus = {"SHADOW": 20, "DAWN": 10}
        else:
            faction_bonus = {}
        for fac, amt in faction_bonus.items():
            for p in self._all_players():
                p.add_faction_reputation(fac, amt)
            from .faction import Faction
            try:
                fac_name = Faction[fac].display_name
            except KeyError:
                fac_name = fac
            self.event_log.append(f"🏛 {fac_name} 声望 +{amt}")
        # 全队回复
        for p in self._all_players():
            p.hp = p.stats.max_hp
            p.mp = p.stats.max_mp

    def _start_combat(self, enemy_id: str):
        enemy = create_enemy(enemy_id)
        if enemy is None:
            self._advance_event()
            return

        players = self._all_players()
        self.combat = CombatEngine(players, enemy)
        self.combat.start()
        self.combat_action_phase = "action"
        self.combat_selected_action = 0
        self.combat_selected_skill = 0
        self.combat_result = None
        self.state = GameState.COMBAT

    def _check_combat_end(self):
        if self.combat.combat_over:
            self.combat_result = self.combat.player_won
            self.state = GameState.COMBAT_RESULT

    def _return_to_menu(self):
        self.state = GameState.MENU
        self.player = None
        self.player2 = None
        self.multiplayer = False
        self.chapter_manager = ChapterManager()
        self.event_manager = None
        self.combat = None
        self.event_log = []
        self.has_saves = len(list_saves()) > 0
        self.menu_selected = 0

    def _start_new_game_plus(self):
        """开始 New Game+：继承装备，重置等级和技能。"""
        if not self.player:
            return
        # 保存装备
        saved_eq = dict(self.player.equipment)
        saved_gold = self.player.gold
        prev_level = self.player.ng_plus_level + 1

        # 重新创建角色（保留职业和名字）
        self.player = Character(self.player.name, self.player.char_class, level=1)
        self.player.ng_plus_level = prev_level
        self.player.is_ng_plus = True
        self.player.gold = saved_gold
        # 继承装备（NG+奖励：首次进入时装备上）
        for slot_key, eq in saved_eq.items():
            try:
                self.player.equip(eq)
            except Exception as e:
                self.event_log.append(f"⚠ 装备继承失败 [{slot_key}]: {e}")

        self.player2 = None
        self.multiplayer = False
        self.chapter_manager = ChapterManager()
        self.event_manager = EventManager(self.player)
        self.state = GameState.DIFFICULTY_SELECT
        self.selected_difficulty = 1
        self.event_log = [f"🔥 第{prev_level}周目开始！继承装备和金币（{saved_gold} GP）"]

    # ═══════════════════════════════════════════
    # 更新
    # ═══════════════════════════════════════════

    def _update(self):
        if self.state == GameState.PLAY and self.player:
            if not self._all_alive():
                self.state = GameState.GAME_OVER

    # ═══════════════════════════════════════════
    # 渲染
    # ═══════════════════════════════════════════

    def _render(self):
        if self.state == GameState.MENU:
            self.ui.draw_title_screen(self.menu_options, self.menu_selected, self.has_saves)

        elif self.state in (GameState.CREATE_CLASS, GameState.CREATE_CLASS_2):
            self.ui.draw_create_screen("class", list(CharClass), self.create_selected_class,
                                       player_label=self.creating_player_label)

        elif self.state in (GameState.CREATE_NAME, GameState.CREATE_NAME_2):
            self.ui.draw_create_screen("name", list(CharClass), self.create_selected_class,
                                       self.create_name, player_label=self.creating_player_label)

        elif self.state in (GameState.CREATE_CONFIRM, GameState.CREATE_CONFIRM_2):
            self.ui.draw_create_screen("confirm", list(CharClass), self.create_selected_class,
                                       self.create_name, player_label=self.creating_player_label)

        elif self.state == GameState.CHAPTER_INTRO:
            ch = self.chapter_manager.current_chapter
            if ch:
                self.ui.draw_chapter_intro(ch)
            else:
                self.state = GameState.GAME_WIN

        elif self.state == GameState.PLAY:
            self._render_play()

        elif self.state == GameState.EVENT_RESULT:
            self._render_play()
            self.ui._draw_text("按 Enter 继续...", 0, 680, (255, 255, 255),
                               self.ui.font_small, max_width=self.ui.screen.get_width(), center=True)

        elif self.state == GameState.COMBAT:
            if self.combat:
                self.ui.draw_combat_screen(
                    self.combat, self.combat_selected_action,
                    self.combat_selected_skill, self.combat_action_phase,
                )

        elif self.state == GameState.COMBAT_RESULT:
            if self.combat:
                self.ui.draw_combat_screen(
                    self.combat, self.combat_selected_action,
                    self.combat_selected_skill, "action",
                )

        elif self.state == GameState.SAVE:
            saves = list_saves()
            self.ui.draw_save_screen(saves, self.save_selected, self.save_message)

        elif self.state == GameState.LOAD:
            saves = list_saves()
            self.ui.draw_save_screen(saves, self.save_selected, self.save_message)

        elif self.state == GameState.CHARACTER_SHEET:
            if self.player:
                self.ui.draw_character_sheet(self.player, self.player2)

        elif self.state == GameState.PAUSE:
            self._render_pause()

        elif self.state == GameState.GAME_OVER:
            self.ui.draw_game_over()

        elif self.state == GameState.GAME_WIN:
            self.ui.draw_game_win()

        elif self.state == GameState.ENDING:
            self._render_ending()

        elif self.state == GameState.DIFFICULTY_SELECT:
            self.ui.draw_difficulty_select(self.difficulty_options, self.selected_difficulty)

        elif self.state == GameState.SHOP:
            self.ui.draw_shop_screen(self.player, self.player2, self.shop_items,
                                     self.shop_selected, self.chapter_manager,
                                     self.shop_message)

        elif self.state == GameState.SKILL_TREE:
            self.ui.draw_skill_tree_screen(self.player, self.skill_tree_selected,
                                           self.skill_tree_message)

    def _render_play(self):
        event_obj = self.chapter_manager.current_event
        if event_obj and self.player:
            ch = self.chapter_manager.current_chapter
            ch_title = f"第{ch.chapter_id}章 {ch.subtitle}" if ch else ""
            total = len(ch.events) if ch else 0
            self.ui.draw_game_screen(
                event_obj, self.player, self.event_log,
                self.selected_choice, ch_title,
                self.chapter_manager.current_event_index, total,
                player2=self.player2,
            )

    def _render_pause(self):
        self.ui.screen.fill((15, 10, 30))
        self.ui._draw_text("⏸ 游戏暂停", 0, 200, (255, 200, 60), self.ui.font_title,
                           max_width=self.ui.screen.get_width(), center=True)
        self.ui._draw_text("Esc 继续  |  S 存档  |  Q 返回标题", 0, 300, (200, 200, 200),
                           self.ui.font, max_width=self.ui.screen.get_width(), center=True)

    def _render_ending(self):
        self.ui.screen.fill((15, 10, 30))
        self.ui._draw_text("最终的抉择", 0, 100, (255, 200, 60), self.ui.font_title,
                           max_width=self.ui.screen.get_width(), center=True)
        self.ui._draw_text(
            "绝夜之神·诺克斯的身躯在晨曦碎片的光芒中逐渐消散。\n\n"
            "他的真实身份——曾经的晨曦之神——在你面前显现。\n"
            "「谢谢你让我想起了……黎明的感觉。」\n"
            "「现在，你可以选择：用四块碎片的力量彻底消灭我，终结绝夜；」\n"
            "「或者……用它们唤醒我心中的晨曦之神，让我重归光明。」\n\n"
            "消灭我，黑暗将永远消失，世界回到原本的轨道。\n"
            "唤醒我，我将重新成为光明的守护者——但代价是，你必须代替我留在这里，抵御虚空的侵蚀。",
            0, 170, (220, 215, 230), self.ui.font, max_width=self.ui.screen.get_width() - 100, center=True)

        choices = [
            "☀️ 唤醒晨曦之神，牺牲自己守护世界",
            "⚔️ 彻底消灭绝夜之神，终结黑暗诅咒",
        ]
        for i, choice_text in enumerate(choices):
            y = 440 + i * 50
            prefix = "▶ " if i == self.ending_choice else "  "
            color = (255, 200, 60) if i == self.ending_choice else (220, 215, 230)
            self.ui._draw_text(f"{prefix}{choice_text}", 0, y, color, self.ui.font,
                               max_width=self.ui.screen.get_width(), center=True)

        self.ui._draw_text("↑↓ 选择  Enter 确认", 0, 580, (140, 135, 155),
                           self.ui.font_small, max_width=self.ui.screen.get_width(), center=True)

    def quit(self):
        self.running = False
