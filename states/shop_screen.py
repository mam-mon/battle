# states/shop_screen.py (已更新)
import pygame
import random
import inspect # <-- 1. 导入 inspect 模块 (Tooltip 需要)
from .base import BaseState
from ui import Button, draw_panel, draw_text, TooltipManager # <-- 2. 导入 TooltipManager
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
        
        # <-- 3. 在 __init__ 中，初始化 TooltipManager -->
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        
        self._generate_inventory()
        self._setup_ui()

    def _generate_inventory(self):
        all_item_classes = [getattr(Equips, name) for name in dir(Equips) if isinstance(getattr(Equips, name), type) and issubclass(getattr(Equips, name), Equips.Equipment) and getattr(Equips, name) is not Equips.Equipment]
        choices = random.sample(all_item_classes, min(3, len(all_item_classes)))
        for item_class in choices:
            item = item_class()
            rarity = getattr(item, 'rarity', 'common')
            price = RARITY_PRICES.get(rarity, 9999)
            self.shop_items.append([None, item, price, False])

    def _setup_ui(self):
        panel_w, panel_h = 900, 600
        self.panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) / 2, (SCREEN_HEIGHT - panel_h) / 2, panel_w, panel_h)
        card_w, card_h, spacing = 250, 400, 25
        start_x = self.panel_rect.centerx - (card_w * len(self.shop_items) + spacing * (len(self.shop_items) - 1)) / 2
        
        for i, item_tuple in enumerate(self.shop_items):
            card_x = start_x + i * (card_w + spacing)
            card_rect = pygame.Rect(card_x, self.panel_rect.y + 120, card_w, card_h)
            button = Button(card_rect, "", self.game.fonts['normal'])
            item_tuple[0] = button
            
        leave_rect = pygame.Rect(self.panel_rect.centerx - 150, self.panel_rect.bottom - 80, 300, 60)
        self.leave_button = Button(leave_rect, "离开商店", self.game.fonts['normal'])

    def handle_event(self, event):
        # ... (handle_event 逻辑保持不变) ...
        if self.leave_button.handle_event(event):
            self.origin_room.is_cleared = True
            from .dungeon_screen import DungeonScreen
            if len(self.game.state_stack) > 1 and isinstance(self.game.state_stack[-2], DungeonScreen):
                self.game.state_stack[-2].door_rects = self.game.state_stack[-2]._generate_doors()
            self.game.state_stack.pop()
            return
        for button, item, price, is_sold in self.shop_items:
            if not is_sold and button.handle_event(event):
                if self.game.player.gold >= price:
                    self.game.player.gold -= price
                    feedback = self.game.player.pickup_item(item)
                    if feedback:
                        from .notification_screen import NotificationScreen
                        self.game.state_stack.append(NotificationScreen(self.game, feedback))
                    self.feedback_message = f"成功购买 {getattr(item, 'display_name', '物品')}！"
                    self.shop_items[self.shop_items.index([button, item, price, is_sold])][3] = True
                else:
                    self.feedback_message = "金币不足！"
                self.feedback_timer = pygame.time.get_ticks()
                return

    def update(self):
        if self.feedback_message and pygame.time.get_ticks() - self.feedback_timer > 2000:
            self.feedback_message = ""

        # <-- 4. 在 update 中，添加悬停检测逻辑 -->
        hovered_item = None
        mouse_pos = pygame.mouse.get_pos()
        for button, item, price, is_sold in self.shop_items:
            if button.rect.collidepoint(mouse_pos):
                hovered_item = item
                break
        self.tooltip_manager.update(hovered_item)


    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
        draw_panel(surface, self.panel_rect, "神秘商店", self.game.fonts['large'])
        
        gold_text = f"你的金币: {self.game.player.gold} G"
        gold_surf = self.game.fonts['normal'].render(gold_text, True, (255, 215, 0))
        gold_rect = gold_surf.get_rect(right=self.panel_rect.right - 30, top=self.panel_rect.top + 20)
        surface.blit(gold_surf, gold_rect)

        for button, item, price, is_sold in self.shop_items:
            rarity = getattr(item, 'rarity', 'common')
            color = RARITY_COLORS.get(rarity, (255,255,255))
            
            bg_color = PANEL_BORDER_COLOR if button.is_hovered and not is_sold else PANEL_BG_COLOR
            pygame.draw.rect(surface, bg_color, button.rect, border_radius=10)
            pygame.draw.rect(surface, color if not is_sold else (80,80,80), button.rect, 2, border_radius=10)
            
            name = getattr(item, 'display_name', '物品')
            name_surf = self.game.fonts['normal'].render(name, True, color if not is_sold else (120,120,120))
            name_rect = name_surf.get_rect(centerx=button.rect.centerx, top=button.rect.top + 20)
            surface.blit(name_surf, name_rect)

            # 绘制物品描述（这里用 tooltip 代替，所以可以留空或画个图）
            
            price_text = "已售罄" if is_sold else f"购买 ({price} G)"
            price_color = (150,150,150) if is_sold else TEXT_COLOR
            price_rect_area = pygame.Rect(button.rect.x, button.rect.bottom - 70, button.rect.width, 70)
            draw_text(surface, price_text, self.game.fonts['normal'], price_color, price_rect_area)

        self.leave_button.draw(surface)
        if self.feedback_message:
             feedback_rect = pygame.Rect(0, self.panel_rect.top + 80, self.panel_rect.width, 30)
             feedback_rect.centerx = self.panel_rect.centerx
             draw_text(surface, self.feedback_message, self.game.fonts['small'], HOVER_COLOR, feedback_rect)

        # <-- 5. 在 draw 的末尾，绘制悬停提示 -->
        self.tooltip_manager.draw(surface)