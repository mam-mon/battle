# states/shop_screen.py (现代化重写版本)
import pygame
import random
import math
import inspect
from .base import BaseState
from ui import Button, TooltipManager
from settings import *
import Equips

RARITY_PRICES = {"common": 50, "uncommon": 100, "rare": 250, "epic": 500, "legendary": 1000}

class ShopScreen(BaseState):
    def __init__(self, game, origin_room):
        super().__init__(game)
        self.is_overlay = True
        self.origin_room = origin_room
        self.shop_items = []
        self.feedback_message = ""
        self.feedback_timer = 0
        
        # 动画系统
        self.hover_animations = {}
        self.glow_animation = 0
        self.entrance_animation = 0
        self.coin_particles = []
        self.card_bounce_offsets = []
        
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        
        self._generate_inventory()
        self._setup_ui()

    def _get_font(self, font_name, default_size=20):
        """安全获取字体"""
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)

    def _generate_inventory(self):
        """生成商店物品"""
        all_item_classes = [getattr(Equips, name) for name in dir(Equips) 
                           if isinstance(getattr(Equips, name), type) 
                           and issubclass(getattr(Equips, name), Equips.Equipment) 
                           and getattr(Equips, name) is not Equips.Equipment]
        
        choices = random.sample(all_item_classes, min(4, len(all_item_classes)))  # 增加到4个商品
        
        for item_class in choices:
            item = item_class()
            rarity = getattr(item, 'rarity', 'common')
            base_price = RARITY_PRICES.get(rarity, 9999)
            # 添加价格波动
            price_variation = random.uniform(0.8, 1.2)
            price = int(base_price * price_variation)
            self.shop_items.append([None, item, price, False])

    def _setup_ui(self):
        """设置UI布局"""
        # 动态调整面板大小
        num_items = len(self.shop_items)
        card_width, card_height = 280, 380
        spacing = 25
        
        # 计算布局
        cards_per_row = min(4, num_items)
        rows = (num_items + cards_per_row - 1) // cards_per_row
        
        total_width = cards_per_row * card_width + (cards_per_row - 1) * spacing + 80
        total_height = rows * card_height + (rows - 1) * spacing + 200
        
        self.panel_rect = pygame.Rect(0, 0, total_width, total_height)
        self.panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # 创建商品卡片
        cards_start_x = self.panel_rect.x + 40
        cards_start_y = self.panel_rect.y + 120
        
        for i, item_tuple in enumerate(self.shop_items):
            row = i // cards_per_row
            col = i % cards_per_row
            
            # 如果最后一行商品数量不足，居中显示
            if row == rows - 1:
                items_in_last_row = num_items - row * cards_per_row
                if items_in_last_row < cards_per_row:
                    # 计算居中偏移
                    empty_slots = cards_per_row - items_in_last_row
                    center_offset = (empty_slots * (card_width + spacing)) // 2
                    card_x = cards_start_x + center_offset + col * (card_width + spacing)
                else:
                    card_x = cards_start_x + col * (card_width + spacing)
            else:
                card_x = cards_start_x + col * (card_width + spacing)
            
            card_y = cards_start_y + row * (card_height + spacing)
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            
            button = Button(card_rect, "", self._get_font('normal'))
            item_tuple[0] = button
            
            # 初始化动画
            self.hover_animations[i] = 0
            self.card_bounce_offsets.append(random.uniform(0, math.pi * 2))  # 随机相位
        
        # 离开按钮
        leave_rect = pygame.Rect(self.panel_rect.centerx - 100, 
                                self.panel_rect.bottom - 60, 200, 45)
        self.leave_button = Button(leave_rect, "离开商店", self._get_font('normal'))
        self.hover_animations['leave'] = 0

    def handle_event(self, event):
        """处理事件"""
        if self.entrance_animation < 1.0:
            return
        
        if self.leave_button.handle_event(event):
            self.origin_room.is_cleared = True
            from .dungeon_screen import DungeonScreen
            if len(self.game.state_stack) > 1 and isinstance(self.game.state_stack[-2], DungeonScreen):
                self.game.state_stack[-2].door_rects = self.game.state_stack[-2]._generate_doors()
            self.game.state_stack.pop()
            return
        
        for i, (button, item, price, is_sold) in enumerate(self.shop_items):
            if not is_sold and button.handle_event(event):
                if self.game.player.gold >= price:
                    # 购买成功
                    self.game.player.gold -= price
                    feedback = self.game.player.pickup_item(item)
                    
                    # 创建金币粒子效果
                    self._create_coin_particles(button.rect.center)
                    
                    if feedback:
                        from .notification_screen import NotificationScreen
                        self.game.state_stack.append(NotificationScreen(self.game, feedback))
                    
                    self.feedback_message = f"成功购买 {getattr(item, 'display_name', '物品')}！"
                    self.shop_items[self.shop_items.index([button, item, price, is_sold])][3] = True
                else:
                    self.feedback_message = "金币不足！"
                    
                self.feedback_timer = pygame.time.get_ticks()
                return

    def _create_coin_particles(self, center):
        """创建金币粒子效果"""
        for _ in range(15):
            particle = {
                'x': center[0] + random.uniform(-20, 20),
                'y': center[1] + random.uniform(-20, 20),
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-5, -1),
                'life': 60,
                'max_life': 60,
                'size': random.uniform(3, 8)
            }
            self.coin_particles.append(particle)

    def update(self):
        """更新动画和状态"""
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): 
            self._last_time = current_time
            
        dt_ms = current_time - self._last_time
        self._last_time = current_time
        dt_sec = dt_ms / 1000.0
        
        # 入场动画
        self.entrance_animation = min(1.0, self.entrance_animation + dt_sec * 2.5)
        
        # 发光动画
        self.glow_animation = (self.glow_animation + dt_sec * 2) % (2 * math.pi)
        
        # 更新粒子
        for particle in self.coin_particles[:]:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.2  # 重力
            particle['life'] -= 1
            if particle['life'] <= 0:
                self.coin_particles.remove(particle)
        
        # 悬停检测和动画
        mouse_pos = pygame.mouse.get_pos()
        hovered_item = None
        
        # 检查商品卡片悬停
        for i, (button, item, price, is_sold) in enumerate(self.shop_items):
            if button.rect.collidepoint(mouse_pos) and not is_sold:
                self.hover_animations[i] = min(1.0, self.hover_animations[i] + dt_sec * 4)
                hovered_item = item
            else:
                self.hover_animations[i] = max(0, self.hover_animations[i] - dt_sec * 3)
        
        # 检查离开按钮悬停
        if self.leave_button.rect.collidepoint(mouse_pos):
            self.hover_animations['leave'] = min(1.0, self.hover_animations['leave'] + dt_sec * 4)
        else:
            self.hover_animations['leave'] = max(0, self.hover_animations['leave'] - dt_sec * 3)
        
        # 更新tooltip
        self.tooltip_manager.update(hovered_item)
        
        # 清除过期反馈消息
        if self.feedback_message and current_time - self.feedback_timer > 2000:
            self.feedback_message = ""

    def draw(self, surface):
        """绘制界面"""
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(200 * self.entrance_animation)))
        surface.blit(overlay, (0, 0))
        
        # 主面板（入场动画）
        panel_rect = self.panel_rect.copy()
        if self.entrance_animation < 1.0:
            scale = 0.7 + 0.3 * self.entrance_animation
            panel_rect = pygame.Rect(0, 0, 
                                   int(self.panel_rect.width * scale),
                                   int(self.panel_rect.height * scale))
            panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        self._draw_modern_panel(surface, panel_rect, (25, 30, 50, 240))
        
        # 绘制各部分
        self._draw_header(surface, panel_rect)
        self._draw_shop_items(surface)
        self._draw_leave_button(surface)
        self._draw_feedback(surface, panel_rect)
        self._draw_particles(surface)
        
        # 绘制tooltip
        self.tooltip_manager.draw(surface)

    def _draw_modern_panel(self, surface, rect, color, border_color=None):
        """绘制现代化面板"""
        pygame.draw.rect(surface, color, rect, border_radius=15)
        if border_color is None: 
            border_color = (70, 80, 100, 200)
        pygame.draw.rect(surface, border_color, rect, width=3, border_radius=15)
        
        # 内发光效果
        glow_rect = rect.inflate(-6, -6)
        pygame.draw.rect(surface, (255, 255, 255, 25), glow_rect, width=2, border_radius=12)

    def _draw_header(self, surface, panel_rect):
        """绘制商店标题和金币显示"""
        header_rect = pygame.Rect(panel_rect.x + 30, panel_rect.y + 20, 
                                 panel_rect.width - 60, 80)
        
        # 标题背景
        self._draw_modern_panel(surface, header_rect, (35, 40, 65, 180), (100, 120, 150))
        
        # 商店标题
        title_font = self._get_font('large', 32)
        title_text = "✨ 神秘商店 ✨"
        title_surface = title_font.render(title_text, True, (255, 215, 0))
        title_rect = title_surface.get_rect(x=header_rect.x + 25, centery=header_rect.centery - 10)
        surface.blit(title_surface, title_rect)
        
        # 金币显示
        gold_font = self._get_font('normal', 24)
        gold_text = f"💰 {self.game.player.gold} G"
        gold_surface = gold_font.render(gold_text, True, (255, 215, 0))
        gold_rect = gold_surface.get_rect(right=header_rect.right - 25, centery=header_rect.centery - 10)
        
        # 金币背景
        gold_bg = gold_rect.inflate(20, 10)
        pygame.draw.rect(surface, (50, 40, 20, 150), gold_bg, border_radius=8)
        pygame.draw.rect(surface, (255, 215, 0, 100), gold_bg, width=2, border_radius=8)
        surface.blit(gold_surface, gold_rect)
        
        # 副标题
        subtitle_font = self._get_font('small', 16)
        subtitle_text = "精选装备，物超所值！"
        subtitle_surface = subtitle_font.render(subtitle_text, True, (180, 180, 180))
        subtitle_rect = subtitle_surface.get_rect(x=header_rect.x + 25, top=title_rect.bottom + 5)
        surface.blit(subtitle_surface, subtitle_rect)

    def _draw_shop_items(self, surface):
        """绘制商店物品"""
        current_time = pygame.time.get_ticks()
        
        for i, (button, item, price, is_sold) in enumerate(self.shop_items):
            # 计算入场动画偏移
            entrance_delay = i * 0.1
            entrance_progress = max(0, min(1, (self.entrance_animation - entrance_delay) / 0.8))
            entrance_offset = (1 - entrance_progress) * 50
            
            # 计算浮动偏移
            bounce_phase = self.card_bounce_offsets[i] + current_time * 0.001
            bounce_offset = math.sin(bounce_phase) * 2 if not is_sold else 0
            
            # 调整卡片位置
            card_rect = button.rect.copy()
            card_rect.y += entrance_offset + bounce_offset
            
            # 绘制商品卡片
            hover_alpha = self.hover_animations[i]
            self._draw_item_card(surface, card_rect, item, price, is_sold, hover_alpha)

    def _draw_item_card(self, surface, rect, item, price, is_sold, hover_alpha):
        """绘制单个商品卡片"""
        # 获取物品信息
        name = getattr(item, 'display_name', '未知物品')
        rarity = getattr(item, 'rarity', 'common')
        rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['common'])
        
        # 卡片状态
        if is_sold:
            bg_alpha = 60
            border_alpha = 80
            text_color = (120, 120, 120)
            scale = 0.95
        else:
            bg_alpha = int(140 + hover_alpha * 40)
            border_alpha = int(180 + hover_alpha * 75)
            text_color = (255, 255, 255)
            scale = 1.0 + hover_alpha * 0.03
        
        # 缩放效果
        if scale != 1.0:
            scaled_size = (int(rect.width * scale), int(rect.height * scale))
            scaled_rect = pygame.Rect(0, 0, *scaled_size)
            scaled_rect.center = rect.center
            rect = scaled_rect
        
        # 卡片背景
        card_color = (*rarity_color, bg_alpha) if not is_sold else (60, 60, 60, bg_alpha)
        border_color = (*rarity_color, border_alpha) if not is_sold else (80, 80, 80, border_alpha)
        
        pygame.draw.rect(surface, card_color, rect, border_radius=12)
        pygame.draw.rect(surface, border_color, rect, width=3, border_radius=12)
        
        # 稀有度装饰
        decoration_rect = pygame.Rect(rect.x, rect.y, rect.width, 8)
        decoration_color = rarity_color if not is_sold else (80, 80, 80)
        pygame.draw.rect(surface, decoration_color, decoration_rect, 
                        border_top_left_radius=12, border_top_right_radius=12)
        
        # 发光效果（悬停且未售出）
        if hover_alpha > 0 and not is_sold:
            glow_intensity = int((math.sin(self.glow_animation) + 1) * hover_alpha * 25 + 15)
            glow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*rarity_color, glow_intensity), 
                           (0, 0, rect.width, rect.height), border_radius=12)
            surface.blit(glow_surface, rect.topleft)
        
        # 已售出标记
        if is_sold:
            sold_font = self._get_font('large', 28)
            sold_text = sold_font.render("已售罄", True, (255, 100, 100))
            sold_rect = sold_text.get_rect(center=rect.center)
            
            # 半透明背景
            sold_bg = sold_rect.inflate(30, 15)
            pygame.draw.rect(surface, (0, 0, 0, 150), sold_bg, border_radius=8)
            pygame.draw.rect(surface, (255, 100, 100), sold_bg, width=2, border_radius=8)
            surface.blit(sold_text, sold_rect)
            return
        
        # 物品名称
        name_font = self._get_font('normal', 18)
        # 处理长名称
        display_name = name
        if name_font.size(display_name)[0] > rect.width - 20:
            while name_font.size(display_name + "...")[0] > rect.width - 20 and len(display_name) > 1:
                display_name = display_name[:-1]
            display_name += "..."
        
        name_surface = name_font.render(display_name, True, text_color)
        name_rect = name_surface.get_rect(centerx=rect.centerx, top=rect.top + 20)
        
        # 名称背景
        name_bg_rect = name_rect.inflate(16, 6)
        pygame.draw.rect(surface, (0, 0, 0, 100), name_bg_rect, border_radius=4)
        surface.blit(name_surface, name_rect)
        
        # 稀有度标签
        rarity_font = self._get_font('small', 14)
        rarity_text = rarity.upper()
        rarity_surface = rarity_font.render(rarity_text, True, rarity_color)
        rarity_rect = rarity_surface.get_rect(centerx=rect.centerx, top=name_rect.bottom + 8)
        surface.blit(rarity_surface, rarity_rect)
        
        # 分割线
        line_y = rarity_rect.bottom + 12
        pygame.draw.line(surface, (100, 100, 100), 
                        (rect.x + 15, line_y), (rect.right - 15, line_y), 1)
        
        # 物品描述（简化版）
        description = inspect.getdoc(item) or "神秘的装备"
        desc_words = description.split()[:12]  # 限制字数
        short_desc = " ".join(desc_words) + ("..." if len(description.split()) > 12 else "")
        
        desc_rect = pygame.Rect(rect.x + 15, line_y + 10, rect.width - 30, 80)
        self._draw_wrapped_text(surface, short_desc, self._get_font('small', 12), 
                               (180, 180, 180), desc_rect)
        
        # 价格区域
        price_rect = pygame.Rect(rect.x + 15, rect.bottom - 80, rect.width - 30, 60)
        price_bg = price_rect.inflate(-5, -5)
        
        # 价格背景
        price_bg_color = (50, 40, 20, 150) if self.game.player.gold >= price else (50, 20, 20, 150)
        pygame.draw.rect(surface, price_bg_color, price_bg, border_radius=8)
        pygame.draw.rect(surface, (255, 215, 0, 100) if self.game.player.gold >= price else (255, 100, 100, 100), 
                        price_bg, width=2, border_radius=8)
        
        # 价格文字
        price_font = self._get_font('normal', 20)
        price_text = f"{price} G"
        price_color = (255, 215, 0) if self.game.player.gold >= price else (255, 100, 100)
        price_surface = price_font.render(price_text, True, price_color)
        price_text_rect = price_surface.get_rect(center=price_bg.center)
        surface.blit(price_surface, price_text_rect)
        
        # 购买提示（悬停时）
        if hover_alpha > 0.5 and self.game.player.gold >= price:
            hint_font = self._get_font('small', 14)
            hint_text = "点击购买"
            hint_surface = hint_font.render(hint_text, True, (100, 255, 100))
            hint_rect = hint_surface.get_rect(centerx=rect.centerx, bottom=price_bg.top - 5)
            
            # 提示背景
            hint_bg = hint_rect.inflate(12, 4)
            pygame.draw.rect(surface, (20, 50, 20, 150), hint_bg, border_radius=4)
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
        line_height = font.get_height() + 2
        y_offset = rect.y
        
        for line in lines:
            if y_offset + line_height > rect.bottom:
                break
            line_surface = font.render(line, True, color)
            surface.blit(line_surface, (rect.x, y_offset))
            y_offset += line_height

    def _draw_leave_button(self, surface):
        """绘制离开按钮"""
        hover_alpha = self.hover_animations.get('leave', 0)
        button_rect = self.leave_button.rect
        
        # 按钮背景
        if hover_alpha > 0:
            scale = 1.0 + hover_alpha * 0.05
            scaled_size = (int(button_rect.width * scale), int(button_rect.height * scale))
            scaled_rect = pygame.Rect(0, 0, *scaled_size)
            scaled_rect.center = button_rect.center
            button_rect = scaled_rect
        
        bg_alpha = int(150 + hover_alpha * 50)
        border_alpha = int(180 + hover_alpha * 75)
        
        pygame.draw.rect(surface, (80, 60, 60, bg_alpha), button_rect, border_radius=8)
        pygame.draw.rect(surface, (150, 100, 100, border_alpha), button_rect, width=2, border_radius=8)
        
        # 按钮文字
        font = self._get_font('normal', 18)
        text_color = (255, 200, 200) if hover_alpha > 0 else (200, 200, 200)
        text_surface = font.render("离开商店", True, text_color)
        text_rect = text_surface.get_rect(center=button_rect.center)
        surface.blit(text_surface, text_rect)

    def _draw_feedback(self, surface, panel_rect):
        """绘制反馈消息"""
        if self.feedback_message:
            feedback_rect = pygame.Rect(panel_rect.x + 40, panel_rect.bottom - 120, 
                                       panel_rect.width - 80, 30)
            
            # 消息背景
            is_success = "成功" in self.feedback_message
            bg_color = (20, 50, 20, 180) if is_success else (50, 20, 20, 180)
            border_color = (100, 255, 100) if is_success else (255, 100, 100)
            
            pygame.draw.rect(surface, bg_color, feedback_rect, border_radius=6)
            pygame.draw.rect(surface, border_color, feedback_rect, width=2, border_radius=6)
            
            # 消息文字
            font = self._get_font('normal', 16)
            text_color = (150, 255, 150) if is_success else (255, 150, 150)
            text_surface = font.render(self.feedback_message, True, text_color)
            text_rect = text_surface.get_rect(center=feedback_rect.center)
            surface.blit(text_surface, text_rect)

    def _draw_particles(self, surface):
        """绘制粒子效果"""
        for particle in self.coin_particles:
            alpha = int(255 * (particle['life'] / particle['max_life']))
            color = (255, 215, 0, alpha)
            
            # 创建粒子表面
            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, 
                             (particle['size'], particle['size']), particle['size'])
            
            surface.blit(particle_surface, (particle['x'] - particle['size'], 
                                          particle['y'] - particle['size']))