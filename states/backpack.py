# states/backpack.py
import pygame
from states.base import BaseState
from ui import draw_text, draw_panel
from settings import *

class BackpackScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.dragging_item = None
        self.dragging_from = None # 'slots' or 'backpack'
        self.dragging_from_idx = None

        # 定义UI布局
        self.slot_panel_rect = pygame.Rect(50, 50, 400, SCREEN_HEIGHT - 100)
        self.backpack_panel_rect = pygame.Rect(470, 50, SCREEN_WIDTH - 520, SCREEN_HEIGHT - 100)
        
        self.equipment_slots_rects = self._generate_slot_rects()
        self.backpack_grid_rects = self._generate_backpack_rects()

    def _generate_slot_rects(self):
        rects = {}
        y_offset = self.slot_panel_rect.top + 80
        for slot_name in self.game.player.SLOT_CAPACITY.keys():
            rects[slot_name] = pygame.Rect(self.slot_panel_rect.left + 20, y_offset, self.slot_panel_rect.width - 40, 50)
            y_offset += 60
        return rects

    def _generate_backpack_rects(self):
        rects = []
        rows, cols = 8, 5
        cell_w = (self.backpack_panel_rect.width - 40) / cols
        cell_h = (self.backpack_panel_rect.height - 80) / rows
        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(
                    self.backpack_panel_rect.left + 20 + col * cell_w,
                    self.backpack_panel_rect.top + 70 + row * cell_h,
                    cell_w - 10, cell_h - 10
                )
                rects.append(rect)
        return rects


    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and (event.key == pygame.K_b or event.key == pygame.K_ESCAPE):
            # 如果正在拖拽物品时按键退出，需要将物品安全放回
            if self.dragging_item:
                if self.dragging_from == 'backpack':
                    self.game.player.backpack.insert(self.dragging_from_idx, self.dragging_item)
                self.dragging_item = None
            self.game.state_stack.pop()
            return

        # --- 鼠标按下：拿起物品 ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.dragging_item:
            # 1. 尝试从装备槽拿起
            for slot_name, item_list in self.game.player.slots.items():
                if item_list:
                    rect = self.equipment_slots_rects[slot_name]
                    if rect.collidepoint(event.pos):
                        self.dragging_item = self.game.player.unequip(item_list[0]) # 从身上卸下
                        self.dragging_from = 'slots'
                        return
            
            # 2. 尝试从背包拿起
            # 我们需要倒序遍历，这样pop才不会影响后续的索引
            for i in range(len(self.game.player.backpack) - 1, -1, -1):
                item = self.game.player.backpack[i]
                rect = self.backpack_grid_rects[i]
                if rect.collidepoint(event.pos):
                    self.dragging_item = item
                    self.dragging_from = 'backpack'
                    self.dragging_from_idx = i
                    self.game.player.backpack.pop(i) # 从背包中移除
                    return

        # --- 鼠标松开：放下物品 ---
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging_item:
            mouse_pos = event.pos
            item_was_placed = False

            # 1. 尝试放置在装备槽
            for slot_name, rect in self.equipment_slots_rects.items():
                if rect.collidepoint(mouse_pos) and self.dragging_item.slot == slot_name:
                    replaced_item = self.game.player.equip(self.dragging_item)
                    if replaced_item:
                        self.game.player.backpack.append(replaced_item)
                    self.game.player.recalculate_stats()
                    item_was_placed = True
                    break
            
            # 2. 如果没有成功放置在装备槽，则一律放回背包
            if not item_was_placed:
                # 如果是从背包拿起的，尝试放回原位
                if self.dragging_from == 'backpack':
                    self.game.player.backpack.insert(self.dragging_from_idx, self.dragging_item)
                else: # 如果是从装备槽拿起的，直接放回背包
                    self.game.player.backpack.append(self.dragging_item)
            
            # 3. 清空拖拽状态
            self.dragging_item = None

    def draw(self, surface):
        # 绘制上一层画面（剧情界面）作为背景
        if len(self.game.state_stack) > 1:
            self.game.state_stack[-2].draw(surface)
        
        # 绘制半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 绘制面板
        draw_panel(surface, self.slot_panel_rect, "装备", self.game.fonts['large'])
        draw_panel(surface, self.backpack_panel_rect, "背包 (按B或ESC关闭)", self.game.fonts['large'])

        # 绘制装备槽中的物品
        for slot_name, item_list in self.game.player.slots.items():
            rect = self.equipment_slots_rects[slot_name]
            pygame.draw.rect(surface, (0,0,0,100), rect) # 槽位背景
            draw_text(surface, slot_name.upper(), self.game.fonts['small'], (100,100,100), rect)
            if item_list and item_list[0] is not self.dragging_item:
                item_name = getattr(item_list[0], 'display_name', item_list[0].__class__.__name__)
                draw_text(surface, item_name, self.game.fonts['normal'], TEXT_COLOR, rect)

        # 绘制背包中的物品
        for i, item in enumerate(self.game.player.backpack):
            rect = self.backpack_grid_rects[i]
            pygame.draw.rect(surface, (0,0,0,100), rect) # 格子背景
            item_name = getattr(item, 'display_name', item.__class__.__name__)
            draw_text(surface, item_name, self.game.fonts['small'], TEXT_COLOR, rect)
        
        # 绘制正在拖拽的物品
        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            item_name = getattr(self.dragging_item, 'display_name', self.dragging_item.__class__.__name__)
            text_surf = self.game.fonts['normal'].render(item_name, True, HOVER_COLOR)
            text_rect = text_surf.get_rect(center=mouse_pos)
            pygame.draw.rect(surface, PANEL_BG_COLOR, text_rect.inflate(10,10))
            surface.blit(text_surf, text_rect)