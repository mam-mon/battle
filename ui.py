# 文件: ui.py (最终正确版本)

import pygame
import textwrap
import inspect
import os
from collections import deque
from settings import *
from settings import DAMAGE_TYPE_NAMES_CN, DAMAGE_TYPE_COLORS, TEXT_COLOR, CRIT_COLOR

def init_fonts():
    fonts = {}
    try:
        fonts['normal'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_NORMAL)
        fonts['small'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_SMALL)
        fonts['large'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_LARGE)
        fonts['minimap'] = pygame.font.SysFont(FONT_NAME_CN, 16) 
    except pygame.error:
        print("警告: 未找到指定中文字体，将使用默认字体。")
        fonts['normal'] = pygame.font.Font(None, FONT_SIZE_NORMAL + 4)
        fonts['small'] = pygame.font.Font(None, FONT_SIZE_SMALL + 4)
        fonts['large'] = pygame.font.Font(None, FONT_SIZE_LARGE + 4)
        fonts['minimap'] = pygame.font.Font(None, 18)
    return fonts

class Button:
    def __init__(self, rect, text, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.is_hovered = False
        self.is_clicked = False
    def handle_event(self, event):
        action_triggered = False
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.is_hovered:
            self.is_clicked = True
            action_triggered = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.is_clicked = False
        return action_triggered
    def draw(self, surface):
        button_color = PANEL_BG_COLOR
        if self.is_clicked: button_color = BUTTON_CLICK_COLOR
        elif self.is_hovered: button_color = PANEL_BORDER_COLOR
        pygame.draw.rect(surface, button_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER_COLOR, self.rect, 2, border_radius=10)
        text_surf = self.font.render(self.text, True, TEXT_COLOR)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

def draw_text(surface, text, font, color, rect, aa=True):
    y = rect.top
    line_spacing = -2
    font_height = font.size("Tg")[1]
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

def get_display_name(obj):
    return getattr(obj, 'display_name', obj.__class__.__name__)

def draw_character_panel(surface, char, rect, fonts):
    ui_elements = {'talents': [], 'buffs': []}
    pygame.draw.rect(surface, PANEL_BG_COLOR, rect, border_radius=15)
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect, 3, border_radius=15)
    
    name_surf = fonts['large'].render(char.name, True, TEXT_COLOR)
    level_surf = fonts['normal'].render(f"Lv. {char.level}", True, TEXT_COLOR)
    surface.blit(name_surf, (rect.left + 20, rect.top + 15))
    surface.blit(level_surf, (rect.left + name_surf.get_width() + 30, rect.top + 28))

    hp_bar_rect = pygame.Rect(rect.left + 20, rect.top + 80, rect.width - 40, 30)
    hp_percent = char.hp / char.max_hp if char.max_hp > 0 else 0
    hp_width = (hp_bar_rect.width - 4) * hp_percent
    pygame.draw.rect(surface, (50,50,50), hp_bar_rect, border_radius=5)
    pygame.draw.rect(surface, HP_BAR_GREEN, (hp_bar_rect.left + 2, hp_bar_rect.top + 2, hp_width, hp_bar_rect.height - 4), border_radius=5)
    if char.shield > 0:
        shield_percent = min(char.shield / char.max_hp, 1.0)
        shield_width = (hp_bar_rect.width - 4) * shield_percent
        shield_rect_pos = hp_bar_rect.left + 2 + hp_width
        pygame.draw.rect(surface, SHIELD_BAR_GREY, (shield_rect_pos, hp_bar_rect.top + 2, shield_width, hp_bar_rect.height - 4), border_radius=5)
    hp_text = f"{int(char.hp)}/{int(char.max_hp)}" + (f" (+{int(char.shield)})" if char.shield > 0 else "")
    hp_text_surf = fonts['small'].render(hp_text, True, TEXT_COLOR)
    surface.blit(hp_text_surf, hp_text_surf.get_rect(center=hp_bar_rect.center))

    stats_text = f"攻击: {int(char.attack)} | 防御: {int(char.defense)} | 攻速: {char.attack_speed:.2f}"
    stats_surf = fonts['small'].render(stats_text, True, TEXT_COLOR)
    surface.blit(stats_surf, (rect.left + 20, rect.top + 140))

    equipped_talents_to_draw = [t for t in char.equipped_talents if t is not None]
    if equipped_talents_to_draw:
        current_x = rect.left + 20
        talent_label_surf = fonts['small'].render("天赋: ", True, (255, 215, 0))
        surface.blit(talent_label_surf, (current_x, rect.top + 170))
        current_x += talent_label_surf.get_width()
        for i, talent in enumerate(equipped_talents_to_draw):
            name_surf = fonts['small'].render(talent.display_name, True, (255, 215, 0))
            name_rect = name_surf.get_rect(left=current_x, top=rect.top + 170)
            surface.blit(name_surf, name_rect)
            ui_elements['talents'].append((name_rect, talent))
            current_x += name_rect.width
            if i < len(equipped_talents_to_draw) - 1:
                separator_surf = fonts['small'].render(" | ", True, (255, 215, 0))
                surface.blit(separator_surf, (current_x, rect.top + 170))
                current_x += separator_surf.get_width()

    visible_buffs = [b for b in char.buffs if not b.hidden]
    if visible_buffs:
        current_x = rect.left + 20
        status_label_surf = fonts['small'].render("状态: ", True, TEXT_COLOR)
        surface.blit(status_label_surf, (current_x, rect.top + 200))
        current_x += status_label_surf.get_width()
        for i, buff in enumerate(visible_buffs):
            buff_text = buff.display_name
            if buff.max_stacks > 1 and buff.stacks > 1: buff_text += f"({buff.stacks})"
            color = (255, 80, 80) if buff.is_debuff else (80, 255, 80)
            text_surf = fonts['small'].render(buff_text, True, color)
            text_rect = text_surf.get_rect(left=current_x, top=rect.top + 200)
            surface.blit(text_surf, text_rect)
            ui_elements['buffs'].append((text_rect, buff))
            current_x += text_rect.width
            if i < len(visible_buffs) - 1:
                separator_surf = fonts['small'].render(" | ", True, TEXT_COLOR)
                surface.blit(separator_surf, (current_x, rect.top + 200))
                current_x += separator_surf.get_width()
    
    return ui_elements

# 文件: ui.py (完整替换 ScrollableTextRenderer 类)

class ScrollableTextRenderer:
    def __init__(self, rect, font, line_height, text_color=(200, 200, 200), bg_color=(30, 30, 30, 180)):
        self.rect = rect
        self.font = font
        self.line_height = line_height
        self.default_text_color = text_color # <-- 重命名，以示区分
        self.bg_color = bg_color
        self.messages = []
        self.offset = 0
        self.visible_lines = int(self.rect.height / self.line_height)
        self.scroll_bar_width = 10
        self.padding = 5

    def add_message(self, parts, color=None):
        """
        ### 核心升级 ###
        现在可以接收一个 parts 列表，格式为: [(text1, color1), (text2, color2), ...]
        为了向后兼容，如果传入的是普通字符串，则自动包装。
        """
        if isinstance(parts, str):
            # 如果只传入一个普通字符串，就用提供的颜色或默认颜色包装它
            self.messages.append([(parts, color if color else self.default_text_color)])
        else:
            # 否则，假定传入的是一个列表
            self.messages.append(parts)

        if len(self.messages) > self.visible_lines:
            self.offset = len(self.messages) - self.visible_lines

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                if event.button == 4: self.scroll(-1)
                elif event.button == 5: self.scroll(1)

    def scroll(self, delta_lines):
        max_offset = max(0, len(self.messages) - self.visible_lines)
        self.offset = max(0, min(self.offset + delta_lines, max_offset))

    def draw(self, surface):
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=5)
        pygame.draw.rect(surface, PANEL_BORDER_COLOR, self.rect, 2, border_radius=5)
        
        content_rect = pygame.Rect(
            self.rect.left + self.padding, self.rect.top + self.padding,
            self.rect.width - 2 * self.padding - (self.scroll_bar_width if len(self.messages) > self.visible_lines else 0),
            self.rect.height - 2 * self.padding
        )
        display_surface = surface.subsurface(content_rect)

        for i in range(self.visible_lines):
            msg_idx = self.offset + i
            if msg_idx < len(self.messages):
                message_parts = self.messages[msg_idx]
                current_x = 0
                
                # ### 核心升级 ###
                # 遍历一行中的所有片段，并挨个绘制
                for text, color in message_parts:
                    text_surf = self.font.render(text, True, color)
                    display_surface.blit(text_surf, (current_x, i * self.line_height))
                    current_x += text_surf.get_width() # 移动下一个片段的起始x坐标

        if len(self.messages) > self.visible_lines:
            bar_height = max(10, (self.visible_lines / len(self.messages)) * content_rect.height)
            bar_y_ratio = self.offset / max(1, len(self.messages) - self.visible_lines)
            bar_y = content_rect.top + bar_y_ratio * (content_rect.height - bar_height)
            
            scroll_bg_rect = pygame.Rect(self.rect.right - self.scroll_bar_width - self.padding, self.rect.top + self.padding, self.scroll_bar_width, content_rect.height)
            pygame.draw.rect(surface, (50, 50, 50), scroll_bg_rect, border_radius=3)
            slider_rect = pygame.Rect(scroll_bg_rect.left, bar_y, self.scroll_bar_width, bar_height)
            pygame.draw.rect(surface, (150, 150, 150), slider_rect, border_radius=3)


class TooltipManager:
    def __init__(self, font, delay=500):
        self.font, self.delay = font, delay
        self.active_item, self.hover_start_time, self.tooltip_surface = None, 0, None
    def _get_description(self, item):
        if not item: return None
        doc = inspect.getdoc(item)
        if not doc: return get_display_name(item)
        display_name = getattr(item, 'display_name', item.__class__.__name__)
        return f"[ {display_name} ]\n" + "-"*20 + f"\n{doc}"
    def update(self, hovered_item):
        now = pygame.time.get_ticks()
        if hovered_item:
            if self.active_item != hovered_item:
                self.active_item, self.hover_start_time, self.tooltip_surface = hovered_item, now, None
            elif now - self.hover_start_time > self.delay and not self.tooltip_surface:
                self._create_tooltip_surface(self._get_description(self.active_item))
        else:
            self.active_item, self.tooltip_surface = None, None
    def _create_tooltip_surface(self, text):
        if not text: return
        lines, wrapped_lines, max_width = text.splitlines(), [], 0
        for line in lines:
            wrapped = textwrap.wrap(line, width=40, replace_whitespace=False)
            if not wrapped: wrapped_lines.append("")
            for wrapped_line in wrapped:
                wrapped_lines.append(wrapped_line)
                line_width = self.font.size(wrapped_line)[0]
                if line_width > max_width: max_width = line_width
        padding, line_height = 15, self.font.get_height()
        total_width, total_height = max_width + padding * 2, len(wrapped_lines) * line_height + padding * 2
        self.tooltip_surface = pygame.Surface((total_width, total_height), pygame.SRCALPHA)
        self.tooltip_surface.fill((20, 35, 50, 230))
        pygame.draw.rect(self.tooltip_surface, PANEL_BORDER_COLOR, self.tooltip_surface.get_rect(), 2, border_radius=8)
        current_y = padding
        for line in wrapped_lines:
            text_surf = self.font.render(line, True, TEXT_COLOR)
            self.tooltip_surface.blit(text_surf, (padding, current_y))
            current_y += line_height
    def draw(self, surface):
        if self.tooltip_surface:
            mouse_pos = pygame.mouse.get_pos()
            tooltip_rect = self.tooltip_surface.get_rect(topleft=(mouse_pos[0] + 15, mouse_pos[1] + 15))
            if tooltip_rect.right > SCREEN_WIDTH: tooltip_rect.right = mouse_pos[0] - 15
            if tooltip_rect.bottom > SCREEN_HEIGHT: tooltip_rect.bottom = mouse_pos[1] - 15
            surface.blit(self.tooltip_surface, tooltip_rect)

def format_damage_log(damage_details, action_name="效果"):
    """
    一个标准化的伤害日志格式化工具。
    接收 take_damage 返回的“伤害报告”字典和一个动作名称，
    返回一个可供 log_renderer 使用的富文本列表。
    """
    if not damage_details:
        return []

    source_name = "环境"
    if damage_details["source"]:
        source_name = damage_details["source"].name

    target_name = damage_details["target"].name
    dmg_amount = damage_details["final_amount"]
    dmg_type_enum = damage_details["damage_type"]
    
    dmg_type_name = DAMAGE_TYPE_NAMES_CN.get(dmg_type_enum.name, "未知伤害")
    dmg_color = DAMAGE_TYPE_COLORS.get(dmg_type_enum.name, (255, 255, 255))

    # 使用金色来突出显示动作名称
    action_color = (255, 215, 0) 

    log_parts = [
        (f"[{source_name}]", TEXT_COLOR),
        (f" 的 ", TEXT_COLOR),
        (f"[{action_name}]", action_color),
        (f" 对 ", TEXT_COLOR),
        (f"[{target_name}]", TEXT_COLOR),
        (f" 造成了 ", TEXT_COLOR),
        (f"{dmg_amount} 点 [{dmg_type_name}]", dmg_color),
    ]

    if damage_details["is_critical"]:
        log_parts.append((" (暴击!)", CRIT_COLOR))
        
    return log_parts