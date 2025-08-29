# states/confirm_dialog.py
import pygame
from .base import BaseState
from ui import Button, draw_text, draw_panel
from settings import *

class ConfirmDialog(BaseState):
    def __init__(self, game, text, on_confirm):
        super().__init__(game)
        self.text = text
        self.on_confirm = on_confirm # 接受一个“确认”后要执行的函数

        # 定义UI元素
        panel_w, panel_h = 600, 300
        self.panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) / 2, (SCREEN_HEIGHT - panel_h) / 2, panel_w, panel_h)
        
        btn_w, btn_h = 150, 60
        self.yes_button = Button((self.panel_rect.centerx - btn_w - 20, self.panel_rect.bottom - 100, btn_w, btn_h), "确认", self.game.fonts['normal'])
        self.no_button = Button((self.panel_rect.centerx + 20, self.panel_rect.bottom - 100, btn_w, btn_h), "取消", self.game.fonts['normal'])

    def handle_event(self, event):
        if self.yes_button.handle_event(event):
            self.on_confirm() # 执行确认操作
        
        if self.no_button.handle_event(event):
            self.game.state_stack.pop() # 点击“取消”，只弹出自己

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.state_stack.pop() # 按ESC也视为取消

    def draw(self, surface):
        # 1. 先绘制底层界面（使其变暗）
        if len(self.game.state_stack) > 1:
            self.game.state_stack[-2].draw(surface)
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 2. 绘制对话框面板
        draw_panel(surface, self.panel_rect, "请确认", self.game.fonts['large'])
        
        # 3. 绘制提示文字
        text_rect = self.panel_rect.inflate(-80, -80)
        text_rect.h = 100 # 限制文字区域高度
        draw_text(surface, self.text, self.game.fonts['normal'], TEXT_COLOR, text_rect)

        # 4. 绘制按钮
        self.yes_button.draw(surface)
        self.no_button.draw(surface)