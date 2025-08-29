# ui.py
import pygame
import textwrap
from settings import *

# --- 字体初始化 ---
def init_fonts():
    fonts = {}
    try:
        fonts['normal'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_NORMAL)
        fonts['small'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_SMALL)
        fonts['large'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_LARGE)
    except pygame.error:
        print("警告: 未找到指定中文字体，将使用默认字体。")
        fonts['normal'] = pygame.font.Font(None, FONT_SIZE_NORMAL + 4)
        fonts['small'] = pygame.font.Font(None, FONT_SIZE_SMALL + 4)
        fonts['large'] = pygame.font.Font(None, FONT_SIZE_LARGE + 4)
    return fonts

# --- 可复用UI组件 ---
class Button:
    def __init__(self, rect, text, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            return True
        return False

    def draw(self, surface):
        button_color = PANEL_BORDER_COLOR if self.is_hovered else PANEL_BG_COLOR
        pygame.draw.rect(surface, button_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER_COLOR, self.rect, 2, border_radius=10)
        
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

def draw_text(surface, text, font, color, rect, aa=True):
    y = rect.top
    line_spacing = -2
    font_height = font.size("Tg")[1]
    
    # 简单的文本换行，避免中文宽度计算问题
    max_chars_per_line = rect.width // font.size("一")[0] if font.size("一")[0] > 0 else 1
    wrapped_text = textwrap.wrap(text, width=max_chars_per_line)

    for line in wrapped_text:
        line_surface = font.render(line, aa, color)
        surface.blit(line_surface, (rect.left, y))
        y += font_height + line_spacing
        
def draw_panel(surface, rect, title, font):
    pygame.draw.rect(surface, PANEL_BG_COLOR, rect, border_radius=10)
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect, 3, border_radius=10)
    
    title_surf = font.render(title, True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(rect.centerx, rect.top + 50))
    surface.blit(title_surf, title_rect)

def draw_health_bar(surface, rect, char):
    """在指定矩形内绘制一个角色的血条、护盾和数值"""
    # 背景
    pygame.draw.rect(surface, (50, 50, 50), rect, border_radius=5)

    # 血量
    hp_percent = char.hp / char.max_hp if char.max_hp > 0 else 0
    hp_width = (rect.width - 4) * hp_percent
    hp_rect = pygame.Rect(rect.left + 2, rect.top + 2, hp_width, rect.height - 4)
    pygame.draw.rect(surface, HP_BAR_GREEN, hp_rect, border_radius=5)

    # 护盾 (从右侧覆盖)
    if char.shield > 0:
        shield_percent = min(char.shield / char.max_hp, 1.0) if char.max_hp > 0 else 0
        shield_width = (rect.width - 4) * shield_percent
        shield_rect = pygame.Rect(rect.right - 2 - shield_width, rect.top + 2, shield_width, rect.height - 4)
        pygame.draw.rect(surface, SHIELD_BAR_GREY, shield_rect, border_radius=5)

    # 边框
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect, 2, border_radius=5)

    # 文字
    fonts = init_fonts() # 获取字体
    hp_text = f"{char.name} HP: {int(char.hp)}/{int(char.max_hp)} | 盾: {int(char.shield)}"
    text_surf = fonts['normal'].render(hp_text, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)

def get_display_name(obj):
    """获取一个对象的显示名称，如果不存在则返回其类名"""
    return getattr(obj, 'display_name', obj.__class__.__name__)