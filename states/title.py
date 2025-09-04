# 文件: states/title.py (完整替换)

import pygame
from .base import BaseState
from .loading import LoadScreen
from .story import StoryScreen
from .sandbox_screen import SandboxScreen # <-- 1. 导入新场景
from ui import Button
from settings import *

class TitleScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        # --- 2. 重新布局，加入新按钮 ---
        self.buttons = {
            "new_game": Button((SCREEN_WIDTH / 2 - 150, 300, 300, 60), "新游戏", self.game.fonts['normal']),
            "continue_game": Button((SCREEN_WIDTH / 2 - 150, 380, 300, 60), "继续游戏", self.game.fonts['normal']),
            "load_game": Button((SCREEN_WIDTH / 2 - 150, 460, 300, 60), "加载游戏", self.game.fonts['normal']),
            "sandbox": Button((SCREEN_WIDTH / 2 - 150, 540, 300, 60), "沙盒模式(测试)", self.game.fonts['normal']),
        }

    def handle_event(self, event):
        # --- 3. 添加对新按钮的事件处理 ---
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

        elif self.buttons['sandbox'].handle_event(event):
            self.game.state_stack.append(SandboxScreen(self.game))

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.running = False

    def draw(self, surface):
        surface.fill(BG_COLOR)
        title_surf = self.game.fonts['large'].render("我的战斗游戏", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH / 2, 150))
        surface.blit(title_surf, title_rect)
        for button in self.buttons.values():
            button.draw(surface)