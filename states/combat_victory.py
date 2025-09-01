# states/combat_victory.py
import pygame
from .base import BaseState
# <-- 导入新的UI工具
from ui import draw_character_panel, draw_panel, Button
from settings import *

class CombatVictoryScreen(BaseState):
    def __init__(self, game, final_enemy):
        super().__init__(game)
        self.final_enemy = final_enemy
        # <-- 新增：创建一个继续按钮
        self.continue_button = Button(
            (SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT - 100, 300, 60),
            "进入结算",
            self.game.fonts['normal']
        )

    def handle_event(self, event):
        from states.loot import LootScreen
        # <-- 使用按钮的 handle_event 方法
        if self.continue_button.handle_event(event) or \
           (event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]):
            self.game.state_stack.pop()
            self.game.state_stack.append(LootScreen(self.game))

    def draw(self, surface):
        surface.fill(BG_COLOR)
        # <-- 保持风格统一，继续使用角色面板显示最终状态
        draw_character_panel(surface, self.game.player, PLAYER_PANEL_RECT, self.game.fonts)
        draw_character_panel(surface, self.final_enemy, ENEMY_PANEL_RECT, self.game.fonts)

        # <-- 使用一个面板来显示胜利信息，更有仪式感
        victory_panel_rect = pygame.Rect(SCREEN_WIDTH * 0.25, SCREEN_HEIGHT / 2 - 100, SCREEN_WIDTH * 0.5, 200)
        draw_panel(surface, victory_panel_rect, "战斗胜利！", self.game.fonts['large'])
        
        # <-- 绘制按钮
        self.continue_button.draw(surface)