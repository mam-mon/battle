# states/combat_victory.py
import pygame
from states.base import BaseState
from states.loot import LootScreen
from ui import draw_health_bar, draw_text
from settings import *

class CombatVictoryScreen(BaseState):
    def __init__(self, game, final_enemy):
        super().__init__(game)
        self.final_enemy = final_enemy

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
           (event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]):
            self.game.state_stack.pop()
            self.game.state_stack.append(LootScreen(self.game))

    def draw(self, surface):
        surface.fill(BG_COLOR)
        player_hp_rect = pygame.Rect(50, 50, 500, 40)
        draw_health_bar(surface, player_hp_rect, self.game.player)
        enemy_hp_rect = pygame.Rect(SCREEN_WIDTH - 550, 50, 500, 40)
        draw_health_bar(surface, enemy_hp_rect, self.final_enemy)

        victory_text = f"👑 {self.game.player.name} 获胜！"
        action_log_rect = pygame.Rect(0, SCREEN_HEIGHT - 120, SCREEN_WIDTH, 50)
        draw_text(surface, victory_text, self.game.fonts['large'], TEXT_COLOR, action_log_rect)
        
        prompt_surf = self.game.fonts['small'].render("点击 / 空格 / 回车 进入结算...", True, TEXT_COLOR)
        prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT - 40))
        surface.blit(prompt_surf, prompt_rect)