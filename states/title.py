# states/title.py
import pygame
from .base import BaseState
from .loading import LoadScreen
from ui import Button
from settings import *

class TitleScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.buttons = {
            "new_game": Button((SCREEN_WIDTH / 2 - 150, 300, 300, 60), "新游戏", self.game.fonts['normal']),
            "continue_game": Button((SCREEN_WIDTH / 2 - 150, 400, 300, 60), "继续游戏", self.game.fonts['normal']),
            "load_game": Button((SCREEN_WIDTH / 2 - 150, 500, 300, 60), "加载游戏", self.game.fonts['normal']),
        }
    
    def handle_event(self, event):
        from states.story import StoryScreen # <-- Import 移至此处
        if self.buttons['new_game'].handle_event(event):
            self.game.start_new_game()
            self.game.state_stack.append(StoryScreen(self.game))
        
        elif self.buttons['continue_game'].handle_event(event):
            if self.game.load_from_slot(0):
                self.game.state_stack.append(StoryScreen(self.game))
            else:
                self.game.start_new_game()
                self.game.state_stack.append(StoryScreen(self.game))

        elif self.buttons['load_game'].handle_event(event):
            self.game.state_stack.append(LoadScreen(self.game))

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.running = False # 在主菜单按ESC则退出

    def draw(self, surface):
        surface.fill(BG_COLOR)
        title_surf = self.game.fonts['large'].render("我的战斗游戏", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH / 2, 150))
        surface.blit(title_surf, title_rect)
        for button in self.buttons.values():
            button.draw(surface)