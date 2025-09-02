# states/notification_screen.py
import pygame
from .base import BaseState
from ui import draw_text
from settings import *

class NotificationScreen(BaseState):
    def __init__(self, game, message, duration=2.0):
        super().__init__(game)
        self.is_overlay = True
        self.message = message
        self.duration = duration # 秒
        self.start_time = pygame.time.get_ticks()

    def update(self):
        # 计时结束，自动关闭
        if pygame.time.get_ticks() - self.start_time > self.duration * 1000:
            self.game.state_stack.pop()

    def draw(self, surface):
        # 创建一个位于屏幕底部中央的对话框
        box_width = 600
        box_height = 80
        box_rect = pygame.Rect(
            (SCREEN_WIDTH - box_width) / 2,
            SCREEN_HEIGHT - box_height - 30, # 离底部30像素
            box_width,
            box_height
        )
        
        # 绘制半透明背景
        bg_surface = pygame.Surface(box_rect.size, pygame.SRCALPHA)
        bg_surface.fill((20, 35, 50, 200)) # 使用面板背景色，带透明度
        surface.blit(bg_surface, box_rect.topleft)
        pygame.draw.rect(surface, PANEL_BORDER_COLOR, box_rect, 2, border_radius=10)

        # 绘制消息文本
        draw_text(surface, self.message, self.game.fonts['normal'], TEXT_COLOR, box_rect)