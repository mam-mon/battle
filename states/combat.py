# states/combat.py (已更新)
import pygame
import time
import random # 导入 random
from .base import BaseState
from ui import ScrollableTextRenderer, draw_character_panel, TooltipManager, Button, draw_panel, draw_text
from settings import *
from Character import Character
import Talents
from battle_logger import battle_logger

# 文件: states/combat.py (替换整个类)

class CombatScreen(BaseState):
    def __init__(self, game, enemy_id, origin_identifier=None):
        super().__init__(game)
        self.enemy_id = enemy_id
        self.origin_id = origin_identifier
        
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])

        # 这会创建 self.enemy
        self._initialize_combat()
        
        # ### 核心修复：在这里，正式为双方指定对手！###
        self.game.player.current_opponent = self.enemy
        self.enemy.current_opponent = self.game.player

        self.player_ui_elements, self.enemy_ui_elements = {}, {}
        self.is_paused = False
        pause_button_rect = pygame.Rect(SCREEN_WIDTH - 60, 10, 50, 50)
        self.pause_button = Button(pause_button_rect, "||", self.game.fonts['normal'])

        self.battle_ended = False
        self.end_timer = 0.0
        self.END_DELAY = 2.0
        
        self.log_renderer = ScrollableTextRenderer(
            BATTLE_LOG_RECT, 
            self.game.fonts['small'], 
            line_height=20,
            bg_color=(30, 30, 30, 180)
        )
        
        battle_logger.register_renderer(self.log_renderer)
        self.log_renderer.add_message(f"战斗开始！遭遇了 {self.enemy.name}！")


    def _initialize_combat(self):
        enemy_preset = self.game.enemy_data[self.enemy_id]
        rolled_talents = []
        
        possible_talents = enemy_preset.get("possible_talents", [])
        for talent_info in possible_talents:
            if random.random() < talent_info["chance"]:
                talent_class_name = talent_info["talent_class_name"]
                if hasattr(Talents, talent_class_name):
                    talent_class = getattr(Talents, talent_class_name)
                    rolled_talents.append(talent_class())

        guaranteed_talents = enemy_preset.get("talents", [])
        for talent_class_name in guaranteed_talents:
            if hasattr(Talents, talent_class_name):
                talent_class = getattr(Talents, talent_class_name)
                rolled_talents.append(talent_class())
        
        self.enemy = Character(
            id=self.enemy_id, name=enemy_preset["name"], 
            talents=rolled_talents, **enemy_preset["stats"]
        )
        
        self.game.player.on_enter_combat()
        self.enemy.on_enter_combat()
        self.last_update_time = time.time()
        
        for talent in self.game.player.equipped_talents:
            if talent and hasattr(talent, 'on_battle_start'):
                talent.on_battle_start(self.game.player, self.enemy)
        for talent in self.enemy.equipped_talents:
            if talent and hasattr(talent, 'on_battle_start'):
                talent.on_battle_start(self.enemy, self.game.player)

        for eq in self.game.player.all_equipment: eq.on_battle_start(self.game.player)
        for eq in self.enemy.all_equipment: eq.on_battle_start(self.enemy)

    def handle_event(self, event):
        if self.pause_button.handle_event(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_p):
            self.is_paused = not self.is_paused
            self.pause_button.text = "继续" if self.is_paused else "||"
            if not self.is_paused: self.last_update_time = time.time()
            return

        if self.is_paused: return
        self.log_renderer.handle_event(event)

        from .confirm_dialog import ConfirmDialog
        from .title import TitleScreen
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            def on_confirm_action(): self.game.state_stack = [TitleScreen(self.game)]
            confirm_dialog = ConfirmDialog(self.game, "所有战斗进度都将丢失，确定要返回主菜单吗？", on_confirm_action)
            self.game.state_stack.append(confirm_dialog)

    def _on_victory(self):
            # ### 核心修复：战斗胜利后，清除对手信息 ###
            self.game.player.current_opponent = None
            if hasattr(self, 'enemy'):
                self.enemy.current_opponent = None
            battle_logger.unregister_renderer()

            from .dungeon_screen import DungeonScreen
            from .loot import LootScreen
            # ... (后续的胜利逻辑不变) ...
            next_story_stage_id = None
            if len(self.game.state_stack) > 1 and isinstance(self.game.state_stack[-2], DungeonScreen):
                dungeon_screen = self.game.state_stack[-2]
                if self.origin_id:
                    dungeon_screen.on_monster_defeated(self.origin_id)
            else:
                current_stage_data = self.game.story_data.get(self.game.current_stage, {})
                next_story_stage_id = current_stage_data.get("next_win")

            self.game.state_stack.pop()
            self.game.state_stack.append(LootScreen(self.game, self.enemy, next_story_stage=next_story_stage_id))


    def update(self):
        from .title import TitleScreen

        self._update_hovers()

        if self.is_paused:
            return
            
        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now

        if self.battle_ended:
            self.end_timer += dt
            if self.end_timer >= self.END_DELAY:
                if self.enemy.hp <= 0:
                    self._on_victory()
                elif self.game.player.hp <= 0:
                    # ### 核心修复：战斗失败后，也要清除对手信息 ###
                    self.game.player.current_opponent = None
                    if hasattr(self, 'enemy'):
                        self.enemy.current_opponent = None
                    battle_logger.unregister_renderer()
                    self.game.state_stack = [TitleScreen(self.game)]
            return

        for msg in self.game.player.update(dt): self.log_renderer.add_message(msg)
        for msg in self.enemy.update(dt): self.log_renderer.add_message(msg)
        
        player_res = self.game.player.try_attack(self.enemy, dt)
        if player_res:
            log_parts, extra_logs = player_res
            self.log_renderer.add_message(log_parts)
            [self.log_renderer.add_message(f"  └ {e}") for e in extra_logs]
            
        enemy_res = self.enemy.try_attack(self.game.player, dt)
        if enemy_res:
            log_parts, extra_logs = enemy_res
            self.log_renderer.add_message(log_parts)
            [self.log_renderer.add_message(f"  └ {e}") for e in extra_logs]
        
        if self.enemy.hp <= 0 or self.game.player.hp <= 0:
            self.battle_ended = True


    def _update_hovers(self):
        mouse_pos = pygame.mouse.get_pos()
        hovered_object = None
        all_elements = self.player_ui_elements.get('talents', []) + self.player_ui_elements.get('buffs', []) + \
                       self.enemy_ui_elements.get('talents', []) + self.enemy_ui_elements.get('buffs', [])
        for rect, obj in all_elements:
            if rect.collidepoint(mouse_pos):
                hovered_object = obj
                break
        self.tooltip_manager.update(hovered_object)

    def draw(self, surface):
        surface.fill(BG_COLOR)
        
        self.player_ui_elements = draw_character_panel(surface, self.game.player, PLAYER_PANEL_RECT, self.game.fonts)
        self.enemy_ui_elements = draw_character_panel(surface, self.enemy, ENEMY_PANEL_RECT, self.game.fonts)
        
        self._draw_combat_actions(surface, self.game.player, PLAYER_ACTION_PANEL_RECT)
        
        # --- 核心修复：使用新的 log_renderer 属性来绘制日志 ---
        self.log_renderer.draw(surface)
        
        self.pause_button.draw(surface)
        self.tooltip_manager.draw(surface)
        
    def _draw_combat_actions(self, surface, char, rect):
        """(占位符) 绘制角色的战斗行动选项，如技能、道具"""
        draw_panel(surface, rect, "行动", self.game.fonts['normal'])
        text_rect = rect.inflate(-20, -80)
        draw_text(surface, "技能/道具系统\n即将推出!", self.game.fonts['small'], TEXT_COLOR, text_rect)
        