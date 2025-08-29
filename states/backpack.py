# states/backpack.py
import pygame
from .base import BaseState
from ui import draw_text, draw_panel, get_display_name
from settings import *

# 插槽类型到中文名称的映射
SLOT_NAME_MAP = {
    "weapon": "武器", "offhand": "副手", "helmet": "头部",
    "armor": "身体", "pants": "腿部", "accessory": "饰品",
}

class BackpackScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.dragging_item = None
        self.dragging_from = None
        self.dragging_from_info = {}

        # --- 全新的UI布局定义 ---
        self.equipment_area = pygame.Rect(50, 50, SCREEN_WIDTH - 100, 350)
        self.backpack_panel_rect = pygame.Rect(50, 420, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 470)
        
        self.equipment_slots_rects = self._generate_slot_rects()
        self.backpack_grid_rects = self._generate_backpack_rects()

    def _generate_slot_rects(self):
        """生成“纸娃娃”式的装备槽布局"""
        rects = {}
        slot_size = 64  # 所有槽位统一为64x64的方块
        padding = 15
        
        # 定义各区域的起始位置
        left_col_x = self.equipment_area.left + 250
        right_col_x = self.equipment_area.right - 250
        top_row_y = self.equipment_area.top + 80

        # --- 按照部位安排位置 ---
        # 头部
        rects['helmet'] = [pygame.Rect(left_col_x + (right_col_x - left_col_x) / 2 - slot_size / 2, top_row_y, slot_size, slot_size)]
        # 身体
        rects['armor'] = [pygame.Rect(rects['helmet'][0].x, rects['helmet'][0].bottom + padding, slot_size, slot_size)]
        # 腿部
        rects['pants'] = [pygame.Rect(rects['armor'][0].x, rects['armor'][0].bottom + padding, slot_size, slot_size)]
        # 武器
        rects['weapon'] = [pygame.Rect(left_col_x, rects['armor'][0].y, slot_size, slot_size)]
        # 副手
        rects['offhand'] = [pygame.Rect(right_col_x, rects['armor'][0].y, slot_size, slot_size)]
        
        # 饰品 (底部横向排列)
        rects['accessory'] = []
        accessory_y = self.equipment_area.bottom - slot_size - 20
        start_x = self.equipment_area.centerx - (4 * slot_size + 3 * padding) / 2
        for i in range(4):
            rect = pygame.Rect(start_x + i * (slot_size + padding), accessory_y, slot_size, slot_size)
            rects['accessory'].append(rect)
            
        return rects

    def _generate_backpack_rects(self):
        rects = []
        rows, cols = 4, 10
        cell_w = (self.backpack_panel_rect.width - 40) / cols
        cell_h = (self.backpack_panel_rect.height - 80) / rows
        for row in range(rows):
            for col in range(cols):
                rect = pygame.Rect(
                    self.backpack_panel_rect.left + 20 + col * cell_w,
                    self.backpack_panel_rect.top + 70 + row * cell_h,
                    cell_w - 10, cell_h - 10)
                rects.append(rect)
        return rects

    # --- handle_event 方法保持不变，它会自动适应新的rects ---
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in [pygame.K_b, pygame.K_ESCAPE]:
            if self.dragging_item:
                self._return_dragging_item()
            self.game.state_stack.pop()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not self.dragging_item:
            for slot_name, rect_list in self.equipment_slots_rects.items():
                for i, rect in enumerate(rect_list):
                    if rect.collidepoint(event.pos) and i < len(self.game.player.slots[slot_name]):
                        item_to_drag = self.game.player.slots[slot_name][i]
                        self.dragging_item = self.game.player.unequip(item_to_drag)
                        self.dragging_from = 'slots'
                        self.dragging_from_info = {'slot_name': slot_name, 'index': i}
                        return
            
            for i in range(len(self.game.player.backpack) - 1, -1, -1):
                if i < len(self.backpack_grid_rects):
                    rect = self.backpack_grid_rects[i]
                    if rect.collidepoint(event.pos):
                        self.dragging_item = self.game.player.backpack.pop(i)
                        self.dragging_from = 'backpack'
                        self.dragging_from_info = {'index': i}
                        return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging_item:
            mouse_pos = event.pos
            item_was_placed = False

            for slot_name, rect_list in self.equipment_slots_rects.items():
                for i, rect in enumerate(rect_list):
                    if rect.collidepoint(mouse_pos) and self.dragging_item.slot == slot_name:
                        if i < len(self.game.player.slots[slot_name]):
                            old_item = self.game.player.slots[slot_name][i]
                            self.game.player.unequip(old_item)
                            self.game.player.backpack.append(old_item)
                        self.game.player.equip(self.dragging_item)
                        self.game.player.recalculate_stats()
                        item_was_placed = True
                        break
                if item_was_placed: break
            
            if not item_was_placed and self.backpack_panel_rect.collidepoint(mouse_pos):
                self.game.player.backpack.append(self.dragging_item)
                item_was_placed = True
            
            if not item_was_placed:
                self._return_dragging_item()
            
            self.dragging_item = None

    def _return_dragging_item(self):
        if not self.dragging_item: return
        if self.dragging_from == 'backpack':
            self.game.player.backpack.insert(self.dragging_from_info['index'], self.dragging_item)
        else:
            self.game.player.equip(self.dragging_item)
        self.dragging_item = None

    def draw(self, surface):
        # 绘制背景和遮罩 (不变)
        if len(self.game.state_stack) > 1:
            self.game.state_stack[-2].draw(surface)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # --- 这是核心修改部分 ---

        # 1. 使用更小的字体绘制面板标题
        draw_panel(surface, self.equipment_area, "角色装备", self.game.fonts['normal']) # 使用 normal 字体
        draw_panel(surface, self.backpack_panel_rect, "背包 (B/ESC 关闭)", self.game.fonts['normal']) # 使用 normal 字体

        # 2. 全新重构的角色属性面板 (左侧)
        player = self.game.player
        stats_start_x = self.equipment_area.left + 20
        stats_start_y = self.equipment_area.top + 70
        stats_font = self.game.fonts['small'] # 使用小号字体
        line_height = 30
        
        # 属性按两列显示
        stats_to_display = {
            "攻击": player.attack,
            "生命": f"{int(player.hp)}/{int(player.max_hp)}",
            "防御": player.defense,
            "攻速": f"{6.0 / player.attack_interval:.2f}",
            "暴击": f"{player.crit_chance * 100:.1f}%",
            "爆伤": f"{player.crit_multiplier * 100:.1f}%"
        }

        col1_x = stats_start_x
        col2_x = stats_start_x + 180 # 第二列的起始X坐标
        current_y = stats_start_y

        # 将属性名和值分开渲染，确保对齐
        i = 0
        for name, value in stats_to_display.items():
            x_pos = col1_x if i % 2 == 0 else col2_x
            
            name_surf = stats_font.render(f"{name}:", True, (200, 200, 200)) # 标签用灰色
            value_surf = stats_font.render(str(value), True, TEXT_COLOR) # 数值用白色
            
            name_rect = name_surf.get_rect(topleft=(x_pos, current_y))
            value_rect = value_surf.get_rect(topleft=(x_pos + 70, current_y)) # 数值紧跟在标签后面

            surface.blit(name_surf, name_rect)
            surface.blit(value_surf, value_rect)

            # 每显示完两个属性（一整行），就换行
            if i % 2 != 0:
                current_y += line_height
            i += 1

        # 3. 绘制方形装备槽和标签 (位置微调)
        for slot_name, rect_list in self.equipment_slots_rects.items():
            label_text = SLOT_NAME_MAP.get(slot_name, slot_name.upper())
            label_surf = self.game.fonts['small'].render(label_text, True, TEXT_COLOR)
            
            # 标签位置现在基于第一个槽位的顶部中心
            label_rect = label_surf.get_rect(centerx=rect_list[0].centerx, bottom=rect_list[0].top - 5)
            if slot_name == 'accessory': # 饰品标签特殊处理，居中于所有槽位
                total_width = sum(r.width for r in rect_list) + 15 * (len(rect_list) - 1)
                center_x = rect_list[0].left + total_width / 2
                label_rect.centerx = center_x
            surface.blit(label_surf, label_rect)

            for i, rect in enumerate(rect_list):
                pygame.draw.rect(surface, (0,0,0,100), rect, border_radius=5)
                if i < len(self.game.player.slots[slot_name]):
                    item = self.game.player.slots[slot_name][i]
                    if item is not self.dragging_item:
                        item_name = get_display_name(item)
                        text_surf = self.game.fonts['small'].render(item_name, True, TEXT_COLOR)
                        text_rect = text_surf.get_rect(center=rect.center)
                        surface.blit(text_surf, text_rect)
        
        # 4. 背包和拖拽物品绘制 (保持不变)
        for i, item in enumerate(self.game.player.backpack):
            if i < len(self.backpack_grid_rects):
                rect = self.backpack_grid_rects[i]
                pygame.draw.rect(surface, (0,0,0,100), rect)
                item_name = get_display_name(item)
                text_surf = self.game.fonts['small'].render(item_name, True, TEXT_COLOR)
                text_rect = text_surf.get_rect(center=rect.center)
                surface.blit(text_surf, text_rect)
        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            item_name = get_display_name(self.dragging_item)
            text_surf = self.game.fonts['normal'].render(item_name, True, HOVER_COLOR)
            text_rect = text_surf.get_rect(center=mouse_pos)
            pygame.draw.rect(surface, PANEL_BG_COLOR, text_rect.inflate(10,10), border_radius=5)
            surface.blit(text_surf, text_rect)
