# states/combat.py
import pygame
import time
from states.base import BaseState
from ui import draw_health_bar, draw_text
from settings import *
from Character import Character

class CombatScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self._initialize_combat()

    def _initialize_combat(self):
        stage_data = self.game.story_data[self.game.current_stage]
        enemy_id = stage_data["enemy_id"]
        enemy_preset = self.game.enemy_data[enemy_id]
        self.enemy = Character(name=enemy_preset["name"], **enemy_preset["stats"])
        
        for eq in self.game.player.all_equipment: eq.on_battle_start(self.game.player)
        for eq in self.enemy.all_equipment: eq.on_battle_start(self.enemy)
        self.game.player.update(0)
        self.enemy.update(0)
        
        self.last_update_time = time.time()
        self.latest_action = "战斗开始！"

    def update(self):
        from states.combat_victory import CombatVictoryScreen # <-- Import 移至此处
        from states.title import TitleScreen # <-- Import 移至此处

        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now

        self.game.player.update(dt)
        self.enemy.update(dt)

        player_res = self.game.player.try_attack(self.enemy, dt)
        if player_res: self.latest_action = player_res[0]
        
        enemy_res = self.enemy.try_attack(self.game.player, dt)
        if enemy_res: self.latest_action = enemy_res[0]

        if self.game.player.hp <= 0 or self.enemy.hp <= 0:
            winner = self.game.player if self.game.player.hp > 0 else self.enemy
            
            self.game.state_stack.pop()
            if winner is self.game.player:
                self.game.state_stack.append(CombatVictoryScreen(self.game, self.enemy))
            else:
                self.game.state_stack = [TitleScreen(self.game)]

    def draw(self, surface):
        surface.fill(BG_COLOR)
        player_hp_rect = pygame.Rect(50, 50, 500, 40)
        draw_health_bar(surface, player_hp_rect, self.game.player)
        enemy_hp_rect = pygame.Rect(SCREEN_WIDTH - 550, 50, 500, 40)
        draw_health_bar(surface, enemy_hp_rect, self.enemy)
        action_log_rect = pygame.Rect(0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 50)
        draw_text(surface, f"最新行动: {self.latest_action}", self.game.fonts['normal'], TEXT_COLOR, action_log_rect)