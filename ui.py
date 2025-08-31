# ui.py (已更新)
import pygame
import textwrap
import inspect
import os
from collections import deque
from settings import *

def init_fonts():
    fonts = {}
    try:
        fonts['normal'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_NORMAL)
        fonts['small'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_SMALL)
        fonts['large'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_LARGE)
        # <-- 核心修复：在这里创建 'minimap' 字体 -->
        fonts['minimap'] = pygame.font.SysFont(FONT_NAME_CN, 16) 
    except pygame.error:
        print("警告: 未找到指定中文字体，将使用默认字体。")
        fonts['normal'] = pygame.font.Font(None, FONT_SIZE_NORMAL + 4)
        fonts['small'] = pygame.font.Font(None, FONT_SIZE_SMALL + 4)
        fonts['large'] = pygame.font.Font(None, FONT_SIZE_LARGE + 4)
        # <-- 核心修复：确保在默认字体情况下也创建 'minimap' 字体 -->
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
    y = rect.top; line_spacing = -2; font_height = font.size("Tg")[1]
    max_chars_per_line = rect.width // font.size("一")[0] if font.size("一")[0] > 0 else 1
    wrapped_text = textwrap.wrap(text, width=max_chars_per_line)
    for line in wrapped_text:
        line_surface = font.render(line, aa, color)
        surface.blit(line_surface, (rect.left, y)); y += font_height + line_spacing
def draw_panel(surface, rect, title, font):
    pygame.draw.rect(surface, PANEL_BG_COLOR, rect, border_radius=10)
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect, 3, border_radius=10)
    title_surf = font.render(title, True, TEXT_COLOR)
    title_rect = title_surf.get_rect(center=(rect.centerx, rect.top + 50))
    surface.blit(title_surf, title_rect)
def draw_health_bar(surface, rect, char):
    pygame.draw.rect(surface, (50, 50, 50), rect, border_radius=5)
    hp_percent = char.hp / char.max_hp if char.max_hp > 0 else 0
    hp_width = (rect.width - 4) * hp_percent
    hp_rect = pygame.Rect(rect.left + 2, rect.top + 2, hp_width, rect.height - 4)
    pygame.draw.rect(surface, HP_BAR_GREEN, hp_rect, border_radius=5)
    if char.shield > 0:
        shield_percent = min(char.shield / char.max_hp, 1.0) if char.max_hp > 0 else 0
        shield_width = (rect.width - 4) * shield_percent
        shield_rect = pygame.Rect(rect.right - 2 - shield_width, rect.top + 2, shield_width, rect.height - 4)
        pygame.draw.rect(surface, SHIELD_BAR_GREY, shield_rect, border_radius=5)
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect, 2, border_radius=5)
    fonts = init_fonts()
    hp_text = f"{char.name} HP: {int(char.hp)}/{int(char.max_hp)} | 盾: {int(char.shield)}"
    text_surf = fonts['normal'].render(hp_text, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=rect.center)
    surface.blit(text_surf, text_rect)
def get_display_name(obj):
    return getattr(obj, 'display_name', obj.__class__.__name__)

# 在 ui.py 文件中，找到并修改这个函数

def init_fonts():
    fonts = {}
    try:
        fonts['normal'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_NORMAL)
        fonts['small'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_SMALL)
        fonts['large'] = pygame.font.SysFont(FONT_NAME_CN, FONT_SIZE_LARGE)
        # <-- 新增：为小地图创建一个更小的字体 -->
        fonts['minimap'] = pygame.font.SysFont(FONT_NAME_CN, 16) 
    except pygame.error:
        print("警告: 未找到指定中文字体，将使用默认字体。")
        fonts['normal'] = pygame.font.Font(None, FONT_SIZE_NORMAL + 4)
        fonts['small'] = pygame.font.Font(None, FONT_SIZE_SMALL + 4)
        fonts['large'] = pygame.font.Font(None, FONT_SIZE_LARGE + 4)
        # <-- 新增：默认字体版本 -->
        fonts['minimap'] = pygame.font.Font(None, 18)
    return fonts

buff_icons = {}
def load_buff_icons():
    # <-- 核心改动 1: 确保这里包含了你项目中所有的Buff类名 -->
    icon_names = {
        'SteelHeartBuff': 'steel_heart.png',    # 刚毅
        'RegenerationBuff': 'regeneration.png', # 再生
        'PoisonDebuff': 'poison.png',           # 毒
        'AttackDisabledBuff': 'stun.png',       # 无法攻击 (用眩晕图标)
        'StunDebuff': 'stun.png',               # 眩晕
        'ThornsBuff': 'thorns.png',             # 荆棘
        'PhoenixCrownStage1Buff': 'phoenix.png', # 不灭1
        'PhoenixCrownStage2Buff': 'phoenix.png', # 不灭2
    }
    for buff_class_name, icon_filename in icon_names.items():
        try:
            path = os.path.join('assets', 'icons', icon_filename)
            image = pygame.image.load(path).convert_alpha()
            buff_icons[buff_class_name] = pygame.transform.scale(image, BUFF_ICON_SIZE)
        except pygame.error:
            print(f"警告: 无法加载图标 {path}")
    try: # 加载默认图标
        path = os.path.join('assets', 'icons', 'default.png')
        image = pygame.image.load(path).convert_alpha()
        buff_icons['default'] = pygame.transform.scale(image, BUFF_ICON_SIZE)
    except pygame.error:
        print("警告: 无法加载默认图标 default.png")

def draw_buff_icons(surface, char, x, y):
    # 这个函数现在只负责绘制，并返回它绘制的 (Rect, Buff对象) 列表
    drawn_elements = []
    for i, buff in enumerate(char.buffs):
        if buff.hidden: continue
        icon = buff_icons.get(buff.__class__.__name__, buff_icons.get('default'))
        if icon:
            icon_rect = pygame.Rect(x + i * (BUFF_ICON_SIZE[0] + 5), y, BUFF_ICON_SIZE[0], BUFF_ICON_SIZE[1])
            surface.blit(icon, icon_rect)
            drawn_elements.append((icon_rect, buff)) # 记录位置和对象

            if buff.max_stacks > 1 and buff.stacks > 1:
                fonts = init_fonts()
                stack_surf = fonts['small'].render(str(buff.stacks), True, TEXT_COLOR)
                stack_rect = stack_surf.get_rect(bottomright=(icon_rect.right, icon_rect.bottom))
                pygame.draw.rect(surface, (0,0,0), stack_rect.inflate(4,4))
                surface.blit(stack_surf, stack_rect)
    return drawn_elements


def draw_character_panel(surface, char, rect, fonts):
    """绘制一个完整的角色信息面板, 并返回可交互UI元素的位置和对象"""
    ui_elements = {'talents': [], 'buffs': []}

    pygame.draw.rect(surface, PANEL_BG_COLOR, rect, border_radius=15)
    pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect, 3, border_radius=15)
    
    name_surf = fonts['large'].render(char.name, True, TEXT_COLOR)
    level_surf = fonts['normal'].render(f"Lv. {char.level}", True, TEXT_COLOR)
    surface.blit(name_surf, (rect.left + 20, rect.top + 15))
    surface.blit(level_surf, (rect.left + name_surf.get_width() + 30, rect.top + 28))

    hp_bar_rect = pygame.Rect(rect.left + 20, rect.top + 80, rect.width - 40, 30)
    # ... (血条绘制逻辑保持不变) ...
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
    
    if hasattr(char, 'exp'):
        # ... (经验条绘制逻辑保持不变) ...
        exp_bar_rect = pygame.Rect(rect.left + 20, rect.top + 120, rect.width - 40, 10)
        pygame.draw.rect(surface, (50,50,50), exp_bar_rect, border_radius=3)
        exp_percent = char.exp / char.exp_to_next_level if char.exp_to_next_level > 0 else 0
        exp_width = exp_bar_rect.width * exp_percent
        pygame.draw.rect(surface, XP_BAR_COLOR, (exp_bar_rect.left, exp_bar_rect.top, exp_width, exp_bar_rect.height), border_radius=3)

    stats_text = f"攻击: {int(char.attack)} | 防御: {int(char.defense)} | 攻速: {char.attack_speed:.2f}"
    stats_surf = fonts['small'].render(stats_text, True, TEXT_COLOR)
    surface.blit(stats_surf, (rect.left + 20, rect.top + 140))

    # --- 绘制天赋列表 (逻辑不变) ---
    current_x = rect.left + 20
    if char.talents:
        talent_label_surf = fonts['small'].render("天赋: ", True, (255, 215, 0))
        surface.blit(talent_label_surf, (current_x, rect.top + 170))
        current_x += talent_label_surf.get_width()

        for i, talent in enumerate(char.talents):
            if not talent.display_name: continue
            name_surf = fonts['small'].render(talent.display_name, True, (255, 215, 0))
            name_rect = name_surf.get_rect(left=current_x, top=rect.top + 170)
            surface.blit(name_surf, name_rect)
            ui_elements['talents'].append((name_rect, talent))
            current_x += name_rect.width
            if i < len(char.talents) - 1:
                separator_surf = fonts['small'].render(" | ", True, (255, 215, 0))
                surface.blit(separator_surf, (current_x, rect.top + 170))
                current_x += separator_surf.get_width()

    # <-- 核心改动：用新的文本绘制逻辑替换掉 draw_buff_icons -->
    current_x = rect.left + 20
    if char.buffs:
        status_label_surf = fonts['small'].render("状态: ", True, TEXT_COLOR)
        surface.blit(status_label_surf, (current_x, rect.top + 200))
        current_x += status_label_surf.get_width()
        
        visible_buffs = [b for b in char.buffs if not b.hidden]
        for i, buff in enumerate(visible_buffs):
            # 格式化文本，加入层数
            buff_text = buff.display_name
            if buff.max_stacks > 1 and buff.stacks > 1:
                buff_text += f"({buff.stacks})"
            
            # 根据是增益(Buff)还是减益(Debuff)选择不同颜色
            color = (255, 80, 80) if buff.is_debuff else (80, 255, 80)
            
            # 绘制文本并记录其位置和对象，用于悬停检测
            text_surf = fonts['small'].render(buff_text, True, color)
            text_rect = text_surf.get_rect(left=current_x, top=rect.top + 200)
            surface.blit(text_surf, text_rect)
            ui_elements['buffs'].append((text_rect, buff))
            current_x += text_rect.width

            # 绘制分隔符
            if i < len(visible_buffs) - 1:
                separator_surf = fonts['small'].render(" | ", True, TEXT_COLOR)
                surface.blit(separator_surf, (current_x, rect.top + 200))
                current_x += separator_surf.get_width()

    # 我们不再需要调用 draw_buff_icons 了
    # buff_elements = draw_buff_icons(surface, char, rect.left + 20, rect.top + 205)
    # ui_elements['buffs'].extend(buff_elements)

    return ui_elements

# ... (BattleLog 和 TooltipManager 保持不变) ...
class BattleLog:
    def __init__(self, rect, font, max_lines=8):
        self.rect, self.font, self.max_lines = rect, font, max_lines
        self.messages = deque(maxlen=max_lines)
        self.surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
    def add_message(self, message): self.messages.append(message)
    def draw(self, surface):
        self.surface.fill(LOG_BG_COLOR)
        for i, msg in enumerate(reversed(self.messages)):
            alpha = 255 - (i * 25)
            color = (LOG_TEXT_COLOR[0], LOG_TEXT_COLOR[1], LOG_TEXT_COLOR[2], alpha)
            msg_surf = self.font.render(msg, True, color)
            self.surface.blit(msg_surf, (10, self.rect.height - (len(self.messages) - i) * (self.font.get_height() + 2)))
        surface.blit(self.surface, self.rect.topleft)
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
            self.tooltip_surface.blit(text_surf, (padding, current_y)); current_y += line_height
    def draw(self, surface):
        if self.tooltip_surface:
            mouse_pos = pygame.mouse.get_pos()
            tooltip_rect = self.tooltip_surface.get_rect(topleft=(mouse_pos[0] + 15, mouse_pos[1] + 15))
            if tooltip_rect.right > SCREEN_WIDTH: tooltip_rect.right = mouse_pos[0] - 15
            if tooltip_rect.bottom > SCREEN_HEIGHT: tooltip_rect.bottom = mouse_pos[1] - 15
            surface.blit(self.tooltip_surface, tooltip_rect)