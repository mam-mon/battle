# states/combat.py (已更新)
import pygame
import time
from .base import BaseState
from ui import draw_character_panel, BattleLog, TooltipManager, Button, draw_panel
from settings import *
from Character import Character
import Talents

class CombatScreen(BaseState):
    # __init__ 现在接收 enemy_id 和一个可选的 identifier (可以是node_id或monster_uid)
    def __init__(self, game, enemy_id, origin_identifier=None):
        super().__init__(game)
        self.enemy_id = enemy_id
        self.origin_id = origin_identifier # 记录来源ID
        
        
        self._initialize_combat()
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        self.player_ui_elements, self.enemy_ui_elements = {}, {}
        self.is_paused = False
        pause_button_rect = pygame.Rect(SCREEN_WIDTH - 60, 10, 50, 50)
        self.pause_button = Button(pause_button_rect, "||", self.game.fonts['normal'])

    def _initialize_combat(self):
        # ... (此方法保持不变) ...
        enemy_preset = self.game.enemy_data[self.enemy_id]; enemy_talents = []
        talent_names = enemy_preset.get("talents", []);
        for name in talent_names:
            if hasattr(Talents, name): enemy_talents.append(getattr(Talents, name)())
        self.enemy = Character(name=enemy_preset["name"], talents=enemy_talents, **enemy_preset["stats"])
        self.game.player.on_enter_combat(); self.enemy.on_enter_combat()
        for eq in self.game.player.all_equipment: eq.on_battle_start(self.game.player)
        for eq in self.enemy.all_equipment: eq.on_battle_start(self.enemy)
        self.last_update_time = time.time()
        self.battle_log = BattleLog(BATTLE_LOG_RECT, self.game.fonts['small'])
        self.battle_log.add_message(f"战斗开始！遭遇了 {self.enemy.name}！")

    def _on_victory(self):
        """战斗胜利后的处理逻辑"""
        from .dungeon_screen import DungeonScreen
        from .loot import LootScreen
        from .title import TitleScreen

        # --- 核心修复：统一所有战斗胜利后的出口都是 LootScreen ---

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
            next_story_stage_id = current_stage_data.get("next_win") # 获取下一个剧情ID

        # 弹出自己 (CombatScreen)
        self.game.state_stack.pop()
        # 统一进入 LootScreen, 并把下一个剧情ID作为“任务”传给它
        self.game.state_stack.append(LootScreen(self.game, self.enemy_id, next_story_stage=next_story_stage_id))

    # ... (update, draw, handle_event, _update_hovers 保持不变) ...
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