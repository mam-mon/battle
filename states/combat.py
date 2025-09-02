# states/combat.py (已更新)
import pygame
import time
import random # 导入 random
from .base import BaseState
from ui import draw_character_panel, BattleLog, TooltipManager, Button, draw_panel
from settings import *
from Character import Character
import Talents

class CombatScreen(BaseState):
    def __init__(self, game, enemy_id, origin_identifier=None):
        super().__init__(game)
        self.enemy_id = enemy_id
        self.origin_id = origin_identifier
        
        self._initialize_combat()
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        self.player_ui_elements, self.enemy_ui_elements = {}, {}
        self.is_paused = False
        pause_button_rect = pygame.Rect(SCREEN_WIDTH - 60, 10, 50, 50)
        self.pause_button = Button(pause_button_rect, "||", self.game.fonts['normal'])

    def _initialize_combat(self):
        enemy_preset = self.game.enemy_data[self.enemy_id]
        
        # --- 核心改动：敌人的随机天赋生成逻辑 ---
        rolled_talents = []
        possible_talents = enemy_preset.get("possible_talents", [])
        for talent_info in possible_talents:
            if random.random() < talent_info["chance"]:
                talent_class_name = talent_info["talent_class_name"]
                if hasattr(Talents, talent_class_name):
                    print(f"敌人 {enemy_preset['name']} 获得了天赋: {talent_class_name}")
                    talent_class = getattr(Talents, talent_class_name)
                    rolled_talents.append(talent_class())
        
        # 使用随机生成的天赋来创建敌人实例
        self.enemy = Character(
            id=self.enemy_id, # <-- 增加这一行，把从json读到的id传给Character
            name=enemy_preset["name"], 
            talents=rolled_talents, 
            **enemy_preset["stats"]
        )
        
        # --- 后续逻辑不变 ---
        self.game.player.on_enter_combat(); self.enemy.on_enter_combat()
        for eq in self.game.player.all_equipment: eq.on_battle_start(self.game.player)
        for eq in self.enemy.all_equipment: eq.on_battle_start(self.enemy)
        self.last_update_time = time.time()
        self.battle_log = BattleLog(BATTLE_LOG_RECT, self.game.fonts['small'])
        self.battle_log.add_message(f"战斗开始！遭遇了 {self.enemy.name}！")

    # 在 states/combat.py 文件中，找到并替换这个函数

    def _on_victory(self):
        """战斗胜利后的处理逻辑"""
        from .dungeon_screen import DungeonScreen
        from .loot import LootScreen
        from .title import TitleScreen

        next_story_stage_id = None
        # 判断战斗来源
        if len(self.game.state_stack) > 1 and isinstance(self.game.state_stack[-2], DungeonScreen):
            # --- 地牢战斗 ---
            dungeon_screen = self.game.state_stack[-2]
            if self.origin_id:
                dungeon_screen.on_monster_defeated(self.origin_id)
        else:
            # --- 剧情战斗 ---
            print("主线剧情战斗胜利！")
            current_stage_data = self.game.story_data.get(self.game.current_stage, {})
            next_story_stage_id = current_stage_data.get("next_win")

        # 弹出自己 (CombatScreen)
        self.game.state_stack.pop()

        # --- 核心修改在这里 ---
        # 之前我们传递的是 self.enemy_id (一个字符串)
        # 现在我们传递整个 self.enemy 对象，它包含了敌人的所有实时信息！
        self.game.state_stack.append(LootScreen(self.game, self.enemy, next_story_stage=next_story_stage_id))
        
    def update(self):
        if self.is_paused: return
        from .title import TitleScreen
        now = time.time(); dt = now - self.last_update_time; self.last_update_time = now
        for msg in self.game.player.update(dt): self.battle_log.add_message(msg)
        for msg in self.enemy.update(dt): self.battle_log.add_message(msg)
        player_res = self.game.player.try_attack(self.enemy, dt)
        if player_res: main, extra = player_res; self.battle_log.add_message(main); [self.battle_log.add_message(f"  └ {e}") for e in extra]
        enemy_res = self.enemy.try_attack(self.game.player, dt)
        if enemy_res: main, extra = enemy_res; self.battle_log.add_message(main); [self.battle_log.add_message(f"  └ {e}") for e in extra]
        self._update_hovers()
        if self.enemy.hp <= 0: self._on_victory()
        elif self.game.player.hp <= 0: self.game.state_stack = [TitleScreen(self.game)]
    def _update_hovers(self):
        mouse_pos = pygame.mouse.get_pos(); hovered_object = None
        all_elements = self.player_ui_elements.get('talents', []) + self.player_ui_elements.get('buffs', []) + \
                       self.enemy_ui_elements.get('talents', []) + self.enemy_ui_elements.get('buffs', [])
        for rect, obj in all_elements:
            if rect.collidepoint(mouse_pos): hovered_object = obj; break
        self.tooltip_manager.update(hovered_object)
    def draw(self, surface):
        surface.fill(BG_COLOR)
        self.player_ui_elements = draw_character_panel(surface, self.game.player, PLAYER_PANEL_RECT, self.game.fonts)
        self.enemy_ui_elements = draw_character_panel(surface, self.enemy, ENEMY_PANEL_RECT, self.game.fonts)
        self.battle_log.draw(surface); self.pause_button.draw(surface)
        if self.is_paused:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
            paused_rect = pygame.Rect(0, 0, 400, 200); paused_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
            draw_panel(surface, paused_rect, "游戏已暂停", self.game.fonts['large'])
        self.tooltip_manager.draw(surface)
    def handle_event(self, event):
        if self.pause_button.handle_event(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_p):
            self.is_paused = not self.is_paused;
            if not self.is_paused: self.last_update_time = time.time()
            return
        if self.is_paused: return
        from .confirm_dialog import ConfirmDialog; from .title import TitleScreen
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            def on_confirm_action(): self.game.state_stack = [TitleScreen(self.game)]
            confirm_dialog = ConfirmDialog(self.game, "所有战斗进度都将丢失，确定要返回主菜单吗？", on_confirm_action)
            self.game.state_stack.append(confirm_dialog)