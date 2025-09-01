# states/shop_screen.py
import pygame
import random
from .base import BaseState
from ui import Button, draw_panel, draw_text
from settings import *
import Equips

# 根据品质定价
RARITY_PRICES = {"common": 50, "uncommon": 100, "rare": 250, "epic": 500, "legendary": 1000}

class ShopScreen(BaseState):
    def __init__(self, game, origin_room):
        super().__init__(game)
        self.is_overlay = True
        self.origin_room = origin_room
        self.shop_items = [] # (按钮, 物品实例, 价格)
        self.feedback_message = ""
        
        self._generate_inventory()
        self._setup_ui()

    def _generate_inventory(self):
        """随机生成3件商品"""
        all_item_classes = [getattr(Equips, name) for name in dir(Equips) if isinstance(getattr(Equips, name), type) and issubclass(getattr(Equips, name), Equips.Equipment) and getattr(Equips, name) is not Equips.Equipment]
        
        num_items = 3
        if len(all_item_classes) < num_items:
            # 如果物品总数少于3，就全放上来
            choices = all_item_classes
        else:
            choices = random.sample(all_item_classes, num_items)
            
        for item_class in choices:
            item = item_class()
            rarity = getattr(item, 'rarity', 'common')
            price = RARITY_PRICES.get(rarity, 9999)
            self.shop_items.append([None, item, price]) # 按钮先留空

    def _setup_ui(self):
        panel_w, panel_h = 900, 600
        self.panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) / 2, (SCREEN_HEIGHT - panel_h) / 2, panel_w, panel_h)
        
        card_w, card_h, spacing = 250, 400, 25
        start_x = self.panel_rect.centerx - (card_w * len(self.shop_items) + spacing * (len(self.shop_items) - 1)) / 2
        
        for i, item_tuple in enumerate(self.shop_items):
            card_x = start_x + i * (card_w + spacing)
            card_rect = pygame.Rect(card_x, self.panel_rect.y + 120, card_w, card_h)
            
            # 用物品名称和价格作为按钮文本
            name = getattr(item_tuple[1], 'display_name', "物品")
            price = item_tuple[2]
            button_text = f"购买 ({price}G)"
            
            button = Button(card_rect, button_text, self.game.fonts['normal'])
            item_tuple[0] = button # 把创建好的按钮放回元组
            
        # 离开按钮
        leave_rect = pygame.Rect(self.panel_rect.centerx - 150, self.panel_rect.bottom - 80, 300, 60)
        self.leave_button = Button(leave_rect, "离开商店", self.game.fonts['normal'])

    def handle_event(self, event):
        if self.leave_button.handle_event(event):
            self.origin_room.is_cleared = True
            from .dungeon_screen import DungeonScreen
            if len(self.game.state_stack) > 1 and isinstance(self.game.state_stack[-2], DungeonScreen):
                self.game.state_stack[-2].door_rects = self.game.state_stack[-2]._generate_doors()
            self.game.state_stack.pop()
            return

        for button, item, price in self.shop_items:
            if button.handle_event(event):
                if self.game.player.gold >= price:
                    self.game.player.gold -= price
                    self.game.player.pickup_item(item)
                    self.feedback_message = f"成功购买 {getattr(item, 'display_name', '物品')}！"
                    # 从商店移除已购买的物品
                    self.shop_items.remove([button, item, price])
                else:
                    self.feedback_message = "金币不足！"
                # 重新设置UI以反映物品的移除
                self._setup_ui()
                return

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
        draw_panel(surface, self.panel_rect, "神秘商店", self.game.fonts['large'])
        
        # 显示玩家金币
        gold_text = f"你的金币: {self.game.player.gold} G"
        gold_surf = self.game.fonts['normal'].render(gold_text, True, (255, 215, 0))
        gold_rect = gold_surf.get_rect(right=self.panel_rect.right - 30, top=self.panel_rect.top + 20)
        surface.blit(gold_surf, gold_rect)

        # 绘制商品
        for button, item, price in self.shop_items:
            rarity = getattr(item, 'rarity', 'common')
            color = RARITY_COLORS.get(rarity, (255,255,255))
            
            # 卡片背景
            bg_color = PANEL_BORDER_COLOR if button.is_hovered else PANEL_BG_COLOR
            pygame.draw.rect(surface, bg_color, button.rect, border_radius=10)
            pygame.draw.rect(surface, color, button.rect, 2, border_radius=10)
            
            # 物品名称
            name = getattr(item, 'display_name', '物品')
            name_surf = self.game.fonts['normal'].render(name, True, color)
            name_rect = name_surf.get_rect(centerx=button.rect.centerx, top=button.rect.top + 20)
            surface.blit(name_surf, name_rect)
            
            # ... (可以添加更多物品描述) ...
            
            # 价格按钮 (位于卡片底部)
            price_rect = pygame.Rect(button.rect.x, button.rect.bottom - 70, button.rect.width, 70)
            pygame.draw.rect(surface, (50,60,70), price_rect, border_bottom_left_radius=10, border_bottom_right_radius=10)
            draw_text(surface, f"购买 ({price} G)", self.game.fonts['normal'], TEXT_COLOR, price_rect)

        self.leave_button.draw(surface)
        if self.feedback_message:
             draw_text(surface, self.feedback_message, self.game.fonts['small'], TEXT_COLOR, self.panel_rect)