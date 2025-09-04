# 文件: states/choice_screen.py (现代化重写版本)

import pygame
import math
import inspect
from .base import BaseState
from ui import Button, draw_text
from settings import *

class ChoiceScreen(BaseState):
    def __init__(self, game, item_choices, origin_room):
        super().__init__(game)
        self.is_overlay = True
        self.item_choices = item_choices
        self.origin_room = origin_room
        self.choice_buttons = []
        self.choice_made = False
        
        # 动画系统
        self.hover_animations = {}
        self.glow_animation = 0
        self.entrance_animation = 0
        self.card_offsets = []
        
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
        num_choices = len(self.item_choices)
        
        # 动态调整面板大小
        base_card_width, base_card_height = 320, 450
        spacing = 30
        total_width = base_card_width * num_choices + spacing * (num_choices - 1) + 100
        
        # 如果太宽，调整卡片大小
        if total_width > SCREEN_WIDTH - 100:
            available_width = SCREEN_WIDTH - 200
            card_width = (available_width - spacing * (num_choices - 1)) // num_choices
            card_width = max(280, card_width)  # 最小宽度
        else:
            card_width = base_card_width
        
        card_height = base_card_height
        panel_width = min(total_width, SCREEN_WIDTH - 100)
        panel_height = card_height + 180
        
        self.panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        self.panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # 创建卡片按钮
        actual_spacing = 30 if num_choices <= 3 else 20
        total_cards_width = card_width * num_choices + actual_spacing * (num_choices - 1)
        start_x = self.panel_rect.centerx - total_cards_width // 2
        
        self.choice_buttons = []
        self.card_offsets = []
        
        for i, item in enumerate(self.item_choices):
            card_x = start_x + i * (card_width + actual_spacing)
            card_rect = pygame.Rect(card_x, self.panel_rect.y + 90, card_width, card_height)
            button = Button(card_rect, "", self._get_font('normal'))
            self.choice_buttons.append((button, item))
            self.card_offsets.append(0)  # 初始化动画偏移
            self.hover_animations[i] = 0

    def handle_event(self, event):
        if self.choice_made or self.entrance_animation < 1.0:
            return

        for i, (button, item) in enumerate(self.choice_buttons):
            if button.handle_event(event):
                self.choice_made = True 
                
                # 添加选择动画效果
                self._animate_selection(i)
                
                # 处理选择逻辑
                feedback = self.game.player.pickup_item(item)
                print(f"玩家选择了: {getattr(item, 'display_name', item.__class__.__name__)}")
                
                self.origin_room.is_cleared = True
                
                # 更新地牢界面
                from .dungeon_screen import DungeonScreen
                if len(self.game.state_stack) > 1:
                    prev_state = self.game.state_stack[-2]
                    if isinstance(prev_state, DungeonScreen):
                        prev_state.door_rects = prev_state._generate_doors()
                
                # 退出当前界面
                self.game.state_stack.pop() 

                # 显示通知
                if feedback:
                    from .notification_screen import NotificationScreen
                    self.game.state_stack.append(NotificationScreen(self.game, feedback))
                
                return

    def _animate_selection(self, selected_index):
        """选择动画效果"""
        for i in range(len(self.choice_buttons)):
            if i != selected_index:
                self.hover_animations[i] = -1  # 标记为未选中

    def update(self, dt=0):
        """更新动画"""
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): 
            self._last_time = current_time
            
        dt_ms = current_time - self._last_time
        self._last_time = current_time
        dt_sec = dt_ms / 1000.0
        
        # 入场动画
        self.entrance_animation = min(1.0, self.entrance_animation + dt_sec * 3)
        
        # 发光动画
        self.glow_animation = (self.glow_animation + dt_sec * 2) % (2 * math.pi)
        
        # 悬停检测和动画
        mouse_pos = pygame.mouse.get_pos()
        for i, (button, item) in enumerate(self.choice_buttons):
            if button.rect.collidepoint(mouse_pos) and not self.choice_made:
                self.hover_animations[i] = min(1.0, self.hover_animations[i] + dt_sec * 4)
                # 轻微浮动效果
                self.card_offsets[i] = math.sin(current_time * 0.003 + i) * 3
            else:
                if self.hover_animations[i] >= 0:  # 只有非选择状态才衰减
                    self.hover_animations[i] = max(0, self.hover_animations[i] - dt_sec * 3)
                    self.card_offsets[i] = 0

    def draw(self, surface):
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(200 * self.entrance_animation)))
        surface.blit(overlay, (0, 0))
        
        # 主面板（入场动画）
        panel_rect = self.panel_rect.copy()
        if self.entrance_animation < 1.0:
            scale = 0.8 + 0.2 * self.entrance_animation
            panel_rect = pygame.Rect(0, 0, 
                                   int(self.panel_rect.width * scale),
                                   int(self.panel_rect.height * scale))
            panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self._draw_modern_panel(surface, panel_rect, (25, 30, 50, 240))
        
        # 绘制标题
        self._draw_header(surface, panel_rect)
        
        # 绘制选择卡片
        self._draw_choice_cards(surface)

    def _draw_modern_panel(self, surface, rect, color, border_color=None):
        """绘制现代化面板"""
        pygame.draw.rect(surface, color, rect, border_radius=15)
        if border_color is None: 
            border_color = (70, 80, 100, 200)
        pygame.draw.rect(surface, border_color, rect, width=3, border_radius=15)
        
        # 内发光效果
        glow_rect = rect.inflate(-6, -6)
        pygame.draw.rect(surface, (255, 255, 255, 20), glow_rect, width=2, border_radius=12)

    def _draw_header(self, surface, panel_rect):
        """绘制标题区域"""
        title_rect = pygame.Rect(panel_rect.x + 30, panel_rect.y + 20, 
                                panel_rect.width - 60, 60)
        
        # 标题背景
        title_bg = title_rect.inflate(20, 10)
        self._draw_modern_panel(surface, title_bg, (35, 40, 65, 180), (100, 120, 150))
        
        # 主标题
        title_font = self._get_font('large', 28)
        title_text = "选择奖励"
        title_surface = title_font.render(title_text, True, (255, 215, 0))
        title_pos = title_surface.get_rect(center=title_bg.center)
        surface.blit(title_surface, title_pos)
        
        # 副标题
        subtitle_font = self._get_font('small', 16)
        subtitle_text = "从以下选项中选择一个奖励"
        subtitle_surface = subtitle_font.render(subtitle_text, True, (180, 180, 180))
        subtitle_pos = subtitle_surface.get_rect(centerx=title_bg.centerx, 
                                                top=title_pos.bottom + 5)
        surface.blit(subtitle_surface, subtitle_pos)

    def _draw_choice_cards(self, surface):
        """绘制选择卡片"""
        for i, (button, item) in enumerate(self.choice_buttons):
            # 计算动画偏移
            hover_alpha = max(0, self.hover_animations[i])
            entrance_offset = (1 - self.entrance_animation) * 100
            card_rect = button.rect.copy()
            card_rect.y += entrance_offset + self.card_offsets[i]
            
            # 绘制卡片
            self._draw_item_card(surface, card_rect, item, hover_alpha, i)

    def _draw_item_card(self, surface, rect, item, hover_alpha, card_index):
        """绘制单个物品卡片"""
        # 获取物品信息
        name = getattr(item, 'display_name', item.__class__.__name__)
        rarity = getattr(item, 'rarity', 'common')
        rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['common'])
        
        # 卡片背景色（根据悬停状态调整）
        if self.hover_animations[card_index] == -1:  # 未选中状态
            bg_alpha = 100
            border_alpha = 120
            scale = 0.95
        else:
            bg_alpha = int(120 + hover_alpha * 40)
            border_alpha = int(160 + hover_alpha * 95)
            scale = 1.0 + hover_alpha * 0.05
        
        # 缩放卡片
        if scale != 1.0:
            scaled_size = (int(rect.width * scale), int(rect.height * scale))
            scaled_rect = pygame.Rect(0, 0, *scaled_size)
            scaled_rect.center = rect.center
            rect = scaled_rect
        
        # 卡片主体
        card_bg_color = (*rarity_color, bg_alpha)
        border_color = (*rarity_color, border_alpha)
        
        pygame.draw.rect(surface, card_bg_color, rect, border_radius=12)
        pygame.draw.rect(surface, border_color, rect, width=3, border_radius=12)
        
        # 稀有度装饰条
        decoration_rect = pygame.Rect(rect.x, rect.y, rect.width, 8)
        pygame.draw.rect(surface, rarity_color, decoration_rect, 
                        border_top_left_radius=12, border_top_right_radius=12)
        
        # 发光效果（悬停时）
        if hover_alpha > 0:
            glow_intensity = int((math.sin(self.glow_animation) + 1) * hover_alpha * 30 + 10)
            glow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*rarity_color, glow_intensity), 
                           (0, 0, rect.width, rect.height), border_radius=12)
            surface.blit(glow_surface, rect.topleft)
        
        # 物品名称
        name_font = self._get_font('normal', 20)
        name_surface = name_font.render(name, True, (255, 255, 255))
        name_rect = name_surface.get_rect(centerx=rect.centerx, top=rect.top + 25)
        
        # 名称背景
        name_bg_rect = name_rect.inflate(20, 8)
        pygame.draw.rect(surface, (0, 0, 0, 120), name_bg_rect, border_radius=6)
        surface.blit(name_surface, name_rect)
        
        # 稀有度标签
        rarity_font = self._get_font('small', 14)
        rarity_text = rarity.upper()
        rarity_surface = rarity_font.render(rarity_text, True, rarity_color)
        rarity_rect = rarity_surface.get_rect(centerx=rect.centerx, 
                                             top=name_rect.bottom + 10)
        surface.blit(rarity_surface, rarity_rect)
        
        # 分割线
        line_y = rarity_rect.bottom + 15
        pygame.draw.line(surface, (100, 100, 100), 
                        (rect.x + 20, line_y), (rect.right - 20, line_y), 2)
        
        # 物品描述
        description = inspect.getdoc(item) or "这是一个神秘的物品。"
        desc_rect = pygame.Rect(rect.x + 15, line_y + 15, 
                               rect.width - 30, rect.height - (line_y - rect.y) - 30)
        self._draw_wrapped_text(surface, description, self._get_font('small', 14), 
                               (200, 200, 200), desc_rect)
        
        # 选择提示（悬停时）
        if hover_alpha > 0.5:
            hint_font = self._get_font('small', 16)
            hint_text = "点击选择"
            hint_surface = hint_font.render(hint_text, True, (255, 255, 100))
            hint_rect = hint_surface.get_rect(centerx=rect.centerx, 
                                             bottom=rect.bottom - 15)
            
            # 提示背景
            hint_bg = hint_rect.inflate(16, 6)
            pygame.draw.rect(surface, (50, 50, 0, 150), hint_bg, border_radius=4)
            surface.blit(hint_surface, hint_rect)

    def _draw_wrapped_text(self, surface, text, font, color, rect):
        """绘制自动换行文本"""
        words = text.split(' ')
        lines = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= rect.width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        # 绘制行
        line_height = font.get_height() + 3
        y_offset = rect.y
        
        for line in lines:
            if y_offset + line_height > rect.bottom:
                break
            line_surface = font.render(line, True, color)
            surface.blit(line_surface, (rect.x, y_offset))
            y_offset += line_height