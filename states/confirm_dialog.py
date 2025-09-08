# states/confirm_dialog.py (现代化重写版本)
import pygame
import math
from .base import BaseState
from ui import Button, draw_text
from settings import *

class ConfirmDialog(BaseState):
    # 这是我们之前讨论过的，非常重要的 __init__ 构造函数
    # 所有初始化的工作都在这里完成
    def __init__(self, game, text, on_confirm, title="请确认", confirm_text="确认", cancel_text="取消"):
        super().__init__(game)
        self.is_overlay = True
        self.text = text
        self.title = title
        self.on_confirm = on_confirm
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        
        # 动画系统
        self.entrance_animation = 0
        self.hover_animations = {'confirm': 0, 'cancel': 0}
        self.glow_animation = 0
        self.shake_animation = 0
        
        self._setup_ui()

    def _get_font(self, font_name, default_size=20):
        """安全获取字体"""
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)

    def _setup_ui(self):
        """设置UI布局"""
        # 动态调整对话框大小
        temp_font = self._get_font('normal', 18)
        text_lines = self._wrap_text(self.text, temp_font, 500)
        
        dialog_width = 600
        dialog_height = 150 + len(text_lines) * 25 + 100
        
        self.panel_rect = pygame.Rect(0, 0, dialog_width, dialog_height)
        self.panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # 按钮尺寸和位置
        btn_width, btn_height = 140, 50
        btn_spacing = 30
        total_btn_width = btn_width * 2 + btn_spacing
        
        confirm_x = self.panel_rect.centerx - total_btn_width // 2
        cancel_x = confirm_x + btn_width + btn_spacing
        btn_y = self.panel_rect.bottom - 80
        
        self.confirm_button = Button(
            (confirm_x, btn_y, btn_width, btn_height), 
            self.confirm_text, 
            self._get_font('normal')
        )
        
        self.cancel_button = Button(
            (cancel_x, btn_y, btn_width, btn_height), 
            self.cancel_text, 
            self._get_font('normal')
        )

    def _wrap_text(self, text, font, max_width):
        """文本自动换行"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines

    def handle_event(self, event):
        # 等待入场动画完成
        if self.entrance_animation < 1.0:
            return
            
        if self.confirm_button.handle_event(event):
            self.on_confirm()
        
        if self.cancel_button.handle_event(event):
            self.game.state_stack.pop()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.on_confirm()
            elif event.key == pygame.K_ESCAPE:
                self.game.state_stack.pop()

    def update(self, dt=0):
        """更新动画"""
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): 
            self._last_time = current_time
            
        dt_ms = current_time - self._last_time
        self._last_time = current_time
        dt_sec = dt_ms / 1000.0
        
        self.entrance_animation = min(1.0, self.entrance_animation + dt_sec * 3)
        self.glow_animation = (self.glow_animation + dt_sec * 2) % (2 * math.pi)
        
        mouse_pos = pygame.mouse.get_pos()
        if self.confirm_button.rect.collidepoint(mouse_pos):
            self.hover_animations['confirm'] = min(1.0, self.hover_animations['confirm'] + dt_sec * 4)
        else:
            self.hover_animations['confirm'] = max(0, self.hover_animations['confirm'] - dt_sec * 3)
            
        if self.cancel_button.rect.collidepoint(mouse_pos):
            self.hover_animations['cancel'] = min(1.0, self.hover_animations['cancel'] + dt_sec * 4)
        else:
            self.hover_animations['cancel'] = max(0, self.hover_animations['cancel'] - dt_sec * 3)

    # 这是我们修复的 draw 函数和它的辅助函数
    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(220 * self.entrance_animation)))
        surface.blit(overlay, (0, 0))
        
        panel_rect = self.panel_rect.copy()
        if self.entrance_animation < 1.0:
            scale = 0.6 + 0.4 * self.entrance_animation
            panel_rect = pygame.Rect(0, 0, 
                                    int(self.panel_rect.width * scale),
                                    int(self.panel_rect.height * scale))
            panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        self._draw_modern_panel(surface, panel_rect, (25, 30, 50, 240))
        self._draw_header(surface, panel_rect)
        self._draw_content(surface, panel_rect)
        self._draw_buttons(surface)
    
    def _draw_modern_panel(self, surface, rect, color, border_color=None):
        pygame.draw.rect(surface, color, rect, border_radius=15)
        if border_color is None: 
            border_color = (70, 80, 100, 200)
        pygame.draw.rect(surface, border_color, rect, width=3, border_radius=15)
        glow_rect = rect.inflate(-6, -6)
        pygame.draw.rect(surface, (255, 255, 255, 20), glow_rect, width=2, border_radius=12)

    def _draw_header(self, surface, panel_rect):
        title_font = self._get_font('large', 28)
        title_surface = title_font.render(self.title, True, (255, 215, 0))
        title_pos = title_surface.get_rect(centerx=panel_rect.centerx, top=panel_rect.top + 30)
        surface.blit(title_surface, title_pos)

    def _draw_content(self, surface, panel_rect):
        content_font = self._get_font('normal', 18)
        content_rect = pygame.Rect(panel_rect.x + 40, panel_rect.y + 80, panel_rect.width - 80, panel_rect.height - 180)
        draw_text(surface, self.text, content_font, (220, 220, 220), content_rect)
        
    def _draw_buttons(self, surface):
        self.confirm_button.draw(surface)
        self.cancel_button.draw(surface)