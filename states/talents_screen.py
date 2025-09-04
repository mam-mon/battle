# 文件: states/talents_screen.py (完全重写的现代化版本)

import pygame
import math
import inspect
from .base import BaseState
from ui import draw_text, Button, get_display_name, TooltipManager
from settings import *

# 天赋稀有度颜色配置
TALENT_RARITY_COLORS = {
    "common": (156, 163, 175),
    "uncommon": (16, 185, 129), 
    "rare": (59, 130, 246),
    "epic": (139, 92, 246),
    "legendary": (245, 158, 11)
}

class TalentsScreen(BaseState):
    def __init__(self, game, player_override=None):
        super().__init__(game)
        self.player = player_override or self.game.player
        self.is_overlay = True
        self.dragging_talent = None
        self.dragging_from_info = None
        
        # 动画系统
        self.hover_animation = {}
        self.glow_animation = 0
        self.pulse_animation = 0
        
        self._setup_layout()
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        
    def _get_font(self, font_name, default_size=20):
        """安全获取字体"""
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)

    def _setup_layout(self):
        margin, header_height = 40, 80
        self.container_rect = pygame.Rect(margin, margin, SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin)
        self.header_rect = pygame.Rect(self.container_rect.x, self.container_rect.y, 
                                     self.container_rect.width, header_height)
        
        content_y = self.header_rect.bottom + 15
        content_height = self.container_rect.height - header_height - 15
        
        # 左侧：已装备天赋面板
        panel_width = 380
        self.equipped_panel_rect = pygame.Rect(self.container_rect.x, content_y, 
                                             panel_width, content_height)
        
        # 右侧：天赋库面板  
        self.learned_panel_rect = pygame.Rect(self.equipped_panel_rect.right + 20, content_y,
                                            self.container_rect.right - self.equipped_panel_rect.right - 20, 
                                            content_height)
        
        # 关闭按钮
        self.close_button = Button(
            pygame.Rect(self.container_rect.right - 50, self.container_rect.top + 15, 40, 40), 
            "×", self._get_font('large', 24)
        )

    def handle_event(self, event):
        if self.close_button.handle_event(event) or (event.type == pygame.KEYDOWN and event.key in [pygame.K_ESCAPE, pygame.K_t]):
            if self.dragging_talent:
                self._return_dragging_talent()
            self.game.state_stack.pop()
            return
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_down(event.pos)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_mouse_up(event.pos)
        if event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)

    def _handle_mouse_down(self, pos):
        if self.dragging_talent: 
            return
        
        # 从已装备槽拾起
        for i, talent in enumerate(self.player.equipped_talents):
            if talent is not None:
                rect = self._get_talent_rect(i, 'equipped')
                if rect.collidepoint(pos):
                    self.dragging_talent = talent
                    self.dragging_from_info = {'type': 'equipped', 'index': i}
                    self.player.unequip_talent(talent)
                    return
        
        # 从天赋库拾起
        unequipped = [t for t in self.player.learned_talents if t not in self.all_equipped_talents]
        for i, talent in enumerate(unequipped):
            rect = self._get_talent_rect(i, 'learned')
            if rect.collidepoint(pos):
                self.dragging_talent = talent
                self.dragging_from_info = {'type': 'learned'}
                return

    def _handle_mouse_up(self, pos):
        if not self.dragging_talent: 
            return

        talent_to_place = self.dragging_talent
        source_info = self.dragging_from_info
        
        # 重置拖拽状态
        self.dragging_talent = None
        self.dragging_from_info = None

        # 检查是否放置在装备槽
        for i in range(self.player.max_talent_slots):
            rect = self._get_talent_rect(i, 'equipped')
            if rect.collidepoint(pos):
                target_talent = self.player.equipped_talents[i]
                
                if target_talent:
                    self.player.unequip_talent(target_talent)
                
                self.player.equip_talent(talent_to_place, specific_index=i)
                
                if target_talent and source_info['type'] == 'equipped':
                    self.player.equip_talent(target_talent, specific_index=source_info['index'])
                
                self.player.recalculate_stats()
                return

        # 检查是否放置在天赋库
        if self.learned_panel_rect.collidepoint(pos):
            self.player.recalculate_stats()
            return

        # 无效操作，返回原处
        self._return_dragging_talent(talent_to_place, source_info)
        self.player.recalculate_stats()

    def _handle_mouse_motion(self, pos):
        """处理鼠标悬停动画"""
        # 重置所有悬停状态
        for key in list(self.hover_animation.keys()):
            if key not in ['mouse_pos']:
                self.hover_animation[key] = max(0, self.hover_animation[key] - 0.1)
        
        # 检查装备槽悬停
        for i in range(self.player.max_talent_slots):
            rect = self._get_talent_rect(i, 'equipped')
            if rect.collidepoint(pos):
                self.hover_animation[f'equipped_{i}'] = min(1.0, self.hover_animation.get(f'equipped_{i}', 0) + 0.15)
        
        # 检查天赋库悬停
        unequipped = [t for t in self.player.learned_talents if t not in self.all_equipped_talents]
        for i, talent in enumerate(unequipped):
            rect = self._get_talent_rect(i, 'learned')
            if rect.collidepoint(pos):
                self.hover_animation[f'learned_{i}'] = min(1.0, self.hover_animation.get(f'learned_{i}', 0) + 0.15)

    def _return_dragging_talent(self, talent_to_return, source_info):
        """将天赋返回原处"""
        if source_info and source_info['type'] == 'equipped':
            self.player.equip_talent(talent_to_return, specific_index=source_info['index'])

    def update(self, dt=0):
        """更新动画"""
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): 
            self._last_time = current_time
            
        dt_ms = current_time - self._last_time
        self._last_time = current_time
        dt_sec = dt_ms / 1000.0
        
        self.glow_animation = (self.glow_animation + dt_sec * 2) % (2 * math.pi)
        self.pulse_animation = (self.pulse_animation + dt_sec * 1.5) % (2 * math.pi)
        
        # 更新悬停检测
        if self.dragging_talent:
            self.tooltip_manager.update(None)
            return
        
        hovered_talent = None
        mouse_pos = pygame.mouse.get_pos()
        
        all_panels = [('equipped', self.all_equipped_talents), 
                      ('learned', [t for t in self.player.learned_talents if t not in self.all_equipped_talents])]

        for panel_type, talent_list in all_panels:
            for i, talent in enumerate(talent_list):
                if talent is None: 
                    continue
                rect = self._get_talent_rect(i, panel_type)
                if rect.collidepoint(mouse_pos):
                    hovered_talent = talent
                    break
            if hovered_talent: 
                break
        
        self.tooltip_manager.update(hovered_talent)

    def _get_talent_rect(self, index, panel_type):
        """获取天赋卡片矩形"""
        panel_rect = self.equipped_panel_rect if panel_type == 'equipped' else self.learned_panel_rect
        
        if panel_type == 'equipped':
            # 装备槽使用特殊布局
            padding, slot_size, spacing = 25, 80, 15
            cols = 3
            col, row = index % cols, index // cols
            x = panel_rect.left + padding + col * (slot_size + spacing)
            y = panel_rect.top + 120 + row * (slot_size + spacing)
            return pygame.Rect(x, y, slot_size, slot_size)
        else:
            # 天赋库使用网格布局
            padding, item_size, spacing = 20, 70, 12
            cols = max(1, (panel_rect.width - 2 * padding + spacing) // (item_size + spacing))
            col, row = index % cols, index // cols
            x = panel_rect.left + padding + col * (item_size + spacing)
            y = panel_rect.top + 120 + row * (item_size + spacing)
            return pygame.Rect(x, y, item_size, item_size)

    def draw(self, surface):
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # 主容器
        self._draw_modern_panel(surface, self.container_rect, (25, 30, 50, 240))
        
        # 绘制各部分
        self._draw_header(surface)
        self._draw_equipped_panel(surface)
        self._draw_learned_panel(surface)
        self._draw_dragging_talent(surface)
        
        self.close_button.draw(surface)
        self.tooltip_manager.draw(surface)
        
        # 更新动画
        if hasattr(self, 'update'): 
            self.update()

    def _draw_modern_panel(self, surface, rect, color, border_color=None):
        """绘制现代化面板"""
        pygame.draw.rect(surface, color, rect, border_radius=12)
        if border_color is None: 
            border_color = (70, 80, 100, 180)
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=12)
        
        # 内发光效果
        glow_rect = rect.inflate(-4, -4)
        pygame.draw.rect(surface, (255, 255, 255, 15), glow_rect, width=1, border_radius=10)

    def _draw_header(self, surface):
        """绘制标题区域"""
        header_bg = self.header_rect.inflate(-10, -10)
        self._draw_modern_panel(surface, header_bg, (35, 40, 65, 200))
        
        title_font = self._get_font('large', 32)
        title_text = title_font.render("天赋管理系统", True, (255, 215, 0))
        title_rect = title_text.get_rect(x=header_bg.x + 25, centery=header_bg.centery)
        surface.blit(title_text, title_rect)
        
        # 天赋点数显示
        if hasattr(self.player, 'talent_points'):
            points_text = f"天赋点: {self.player.talent_points}"
            points_font = self._get_font('normal', 20)
            points_surface = points_font.render(points_text, True, (100, 255, 100))
            points_rect = points_surface.get_rect(right=header_bg.right - 25, centery=header_bg.centery)
            surface.blit(points_surface, points_rect)

    def _draw_equipped_panel(self, surface):
        """绘制已装备天赋面板"""
        panel_bg = self.equipped_panel_rect.inflate(-8, -8)
        self._draw_modern_panel(surface, panel_bg, (30, 35, 55, 200))
        
        # 标题
        title = f"已装备天赋 ({len(self.all_equipped_talents)}/{self.player.max_talent_slots})"
        title_rect = pygame.Rect(panel_bg.x + 20, panel_bg.y + 20, panel_bg.width - 40, 50)
        title_font = self._get_font('normal', 22)
        title_surface = title_font.render(title, True, (255, 215, 0))
        surface.blit(title_surface, title_rect)
        
        # 分割线
        line_y = title_rect.bottom + 15
        pygame.draw.line(surface, (70, 80, 100), 
                        (panel_bg.x + 20, line_y), (panel_bg.right - 20, line_y), 2)
        
        # 装备槽
        for i in range(self.player.max_talent_slots):
            rect = self._get_talent_rect(i, 'equipped')
            hover_alpha = self.hover_animation.get(f'equipped_{i}', 0)
            
            # 槽位背景
            slot_color = (40, 50, 70, 120 + int(hover_alpha * 60))
            border_color = (70, 80, 100, 180 + int(hover_alpha * 75))
            
            # 添加悬停动画偏移
            if hover_alpha > 0:
                offset = int(math.sin(self.pulse_animation) * hover_alpha * 3)
                rect = rect.move(0, offset)
            
            pygame.draw.rect(surface, slot_color, rect, border_radius=10)
            pygame.draw.rect(surface, border_color, rect, width=2, border_radius=10)
            
            # 装备的天赋
            if i < len(self.player.equipped_talents):
                talent = self.player.equipped_talents[i]
                if talent and talent != self.dragging_talent:
                    self._draw_talent_card(surface, rect, talent, hover_alpha > 0.5)
                elif not talent:
                    # 空槽提示
                    plus_font = self._get_font('large', 36)
                    plus_text = plus_font.render("+", True, (100, 100, 100, 150))
                    plus_rect = plus_text.get_rect(center=rect.center)
                    surface.blit(plus_text, plus_rect)

    def _draw_learned_panel(self, surface):
        """绘制天赋库面板"""
        panel_bg = self.learned_panel_rect.inflate(-8, -8)
        self._draw_modern_panel(surface, panel_bg, (30, 35, 55, 200))
        
        # 标题
        unequipped_count = len([t for t in self.player.learned_talents if t not in self.all_equipped_talents])
        title = f"天赋库 ({unequipped_count} 个可用)"
        title_rect = pygame.Rect(panel_bg.x + 20, panel_bg.y + 20, panel_bg.width - 40, 50)
        title_font = self._get_font('normal', 22)
        title_surface = title_font.render(title, True, (255, 215, 0))
        surface.blit(title_surface, title_rect)
        
        # 分割线
        line_y = title_rect.bottom + 15
        pygame.draw.line(surface, (70, 80, 100), 
                        (panel_bg.x + 20, line_y), (panel_bg.right - 20, line_y), 2)
        
        # 天赋卡片
        unequipped = [t for t in self.player.learned_talents if t not in self.all_equipped_talents]
        
        for i, talent in enumerate(unequipped):
            if talent != self.dragging_talent:
                rect = self._get_talent_rect(i, 'learned')
                hover_alpha = self.hover_animation.get(f'learned_{i}', 0)
                
                # 添加悬停动画效果
                if hover_alpha > 0:
                    offset = int(math.sin(self.pulse_animation) * hover_alpha * 2)
                    rect = rect.move(0, offset)
                
                self._draw_talent_card(surface, rect, talent, hover_alpha > 0.3)

    def _draw_talent_card(self, surface, rect, talent, is_highlighted=False):
        """绘制天赋卡片"""
        # 获取稀有度
        rarity = getattr(talent, 'rarity', 'common')
        rarity_color = TALENT_RARITY_COLORS.get(rarity, TALENT_RARITY_COLORS['common'])
        
        # 背景颜色
        if is_highlighted:
            bg_color = (*rarity_color, 80)
            border_color = rarity_color
        else:
            bg_color = (*rarity_color, 40)
            border_color = (*rarity_color, 120)
        
        pygame.draw.rect(surface, bg_color, rect, border_radius=8)
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=8)
        
        # 稀有度指示条
        indicator_rect = pygame.Rect(rect.x, rect.y, rect.width, 4)
        pygame.draw.rect(surface, rarity_color, indicator_rect, 
                        border_top_left_radius=8, border_top_right_radius=8)
        
        # 天赋名称
        name = get_display_name(talent)
        font = self._get_font('small', 14)
        
        # 如果名称太长，截断并添加省略号
        if font.size(name)[0] > rect.width - 8:
            while font.size(name + "...")[0] > rect.width - 8 and len(name) > 1:
                name = name[:-1]
            name += "..."
        
        text_surface = font.render(name, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(rect.centerx, rect.centery))
        surface.blit(text_surface, text_rect)
        
        # 发光效果（如果高亮）
        if is_highlighted:
            glow_alpha = int((math.sin(self.glow_animation) + 1) * 30 + 20)
            glow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(glow_surface, (*rarity_color, glow_alpha), 
                           (0, 0, rect.width, rect.height), border_radius=8)
            surface.blit(glow_surface, rect.topleft)

    def _draw_dragging_talent(self, surface):
        """绘制拖拽中的天赋"""
        if self.dragging_talent:
            mouse_pos = pygame.mouse.get_pos()
            name = get_display_name(self.dragging_talent)
            
            # 创建拖拽卡片
            card_size = (120, 40)
            card_rect = pygame.Rect(0, 0, *card_size)
            card_rect.center = mouse_pos
            
            # 半透明背景
            drag_surface = pygame.Surface(card_size, pygame.SRCALPHA)
            rarity = getattr(self.dragging_talent, 'rarity', 'common')
            rarity_color = TALENT_RARITY_COLORS.get(rarity, TALENT_RARITY_COLORS['common'])
            
            pygame.draw.rect(drag_surface, (*rarity_color, 150), 
                           (0, 0, *card_size), border_radius=8)
            pygame.draw.rect(drag_surface, rarity_color, 
                           (0, 0, *card_size), width=2, border_radius=8)
            
            # 文字
            font = self._get_font('normal', 16)
            text = font.render(name, True, (255, 255, 255))
            text_rect = text.get_rect(center=(card_size[0]//2, card_size[1]//2))
            drag_surface.blit(text, text_rect)
            
            surface.blit(drag_surface, card_rect.topleft)

    @property
    def all_equipped_talents(self):
        """获取所有已装备的非空天赋"""
        return [t for t in self.player.equipped_talents if t is not None]