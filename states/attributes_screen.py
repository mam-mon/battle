# states/attributes_screen.py (新文件)

import pygame
import math
from .base import BaseState
from ui import Button, draw_text, get_display_name
from settings import *

class AttributesScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.player = self.game.player
        self.is_overlay = True
        
        # 存储待分配的点数
        self.pending_points = {
            'strength': 0, 'vitality': 0,
            'dexterity': 0, 'toughness': 0
        }
        
        self.font_title = self.game.fonts['large']
        self.font_main = self.game.fonts['normal']
        self.font_small = self.game.fonts['small']
        
        self._setup_layout()

    def _setup_layout(self):
        panel_w, panel_h = 700, 550
        self.panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) / 2, (SCREEN_HEIGHT - panel_h) / 2, panel_w, panel_h)
        
        self.attribute_buttons = {}
        attributes = ['strength', 'vitality', 'dexterity', 'toughness']
        y_start, y_gap = self.panel_rect.y + 120, 60
        
        for i, attr in enumerate(attributes):
            y = y_start + i * y_gap
            btn_rect = pygame.Rect(self.panel_rect.right - 100, y, 40, 40)
            self.attribute_buttons[attr] = Button(btn_rect, "+", self.font_main)
            
        self.confirm_button = Button((self.panel_rect.centerx - 160, self.panel_rect.bottom - 80, 150, 50), "确认", self.font_main)
        self.reset_button = Button((self.panel_rect.centerx + 10, self.panel_rect.bottom - 80, 150, 50), "重置", self.font_main)
        self.close_button = Button((self.panel_rect.right - 50, self.panel_rect.top + 10, 40, 40), "×", self.font_main)

    def get_pending_total(self):
        return sum(self.pending_points.values())
        
    def handle_event(self, event):
        if self.close_button.handle_event(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            self.game.state_stack.pop()
            return

        # 点击 "+" 按钮
        if self.player.attribute_points > self.get_pending_total():
            for attr, button in self.attribute_buttons.items():
                if button.handle_event(event):
                    self.pending_points[attr] += 1
                    
        # 点击 "重置" 按钮
        if self.reset_button.handle_event(event):
            for attr in self.pending_points:
                self.pending_points[attr] = 0
                
        # 点击 "确认" 按钮
        if self.confirm_button.handle_event(event) and self.get_pending_total() > 0:
            self.player.strength += self.pending_points['strength']
            self.player.vitality += self.pending_points['vitality']
            self.player.dexterity += self.pending_points['dexterity']
            self.player.toughness += self.pending_points['toughness']
            self.player.attribute_points -= self.get_pending_total()
            self.player.recalculate_stats() # 应用属性点
            for attr in self.pending_points: # 清空待定点数
                self.pending_points[attr] = 0

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # 绘制主面板
        pygame.draw.rect(surface, PANEL_BG_COLOR, self.panel_rect, border_radius=15)
        pygame.draw.rect(surface, PANEL_BORDER_COLOR, self.panel_rect, 3, border_radius=15)
        
        # 标题
        title_surf = self.font_title.render("角色属性", True, TEXT_COLOR)
        title_rect = title_surf.get_rect(centerx=self.panel_rect.centerx, top=self.panel_rect.top + 20)
        surface.blit(title_surf, title_rect)
        
        # 可用点数
        points_text = f"可用属性点: {self.player.attribute_points - self.get_pending_total()}"
        points_surf = self.font_main.render(points_text, True, (255, 215, 0))
        points_rect = points_surf.get_rect(centerx=self.panel_rect.centerx, top=title_rect.bottom + 15)
        surface.blit(points_surf, points_rect)
        
        # 绘制各个属性行
        attr_names_cn = {'strength': '力量', 'vitality': '体质', 'dexterity': '技巧', 'toughness': '韧性'}
        y_start, y_gap = self.panel_rect.y + 120, 60
        
        for i, attr in enumerate(attr_names_cn.keys()):
            y = y_start + i * y_gap
            
            # 属性名
            name_surf = self.font_main.render(f"{attr_names_cn[attr]}:", True, TEXT_COLOR)
            surface.blit(name_surf, (self.panel_rect.x + 50, y))
            
            # 属性值
            base_value = getattr(self.player, attr)
            pending_value = self.pending_points[attr]
            value_text = f"{base_value}"
            if pending_value > 0:
                value_text += f" + {pending_value}"
                
            value_surf = self.font_main.render(value_text, True, (100, 255, 100) if pending_value > 0 else TEXT_COLOR)
            surface.blit(value_surf, (self.panel_rect.x + 200, y))
            
            # 绘制 "+" 按钮
            if self.player.attribute_points > self.get_pending_total():
                self.attribute_buttons[attr].draw(surface)

        self.confirm_button.draw(surface)
        self.reset_button.draw(surface)
        self.close_button.draw(surface)