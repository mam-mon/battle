# 文件: states/backpack.py (完整替换)

import pygame
import math
import inspect
from .base import BaseState
from ui import draw_text, get_display_name, TooltipManager, Button, draw_text_with_emoji_fallback
from settings import *
from Equips import UPGRADE_MAP

# SLOT_CONFIG and RARITY_COLORS definitions remain the same
SLOT_CONFIG = {
    "weapon": {"name": "武器", "icon": "武", "color": (255, 100, 100)}, "offhand": {"name": "副手", "icon": "副", "color": (100, 255, 100)},
    "helmet": {"name": "头盔", "icon": "头", "color": (255, 255, 100)}, "armor": {"name": "胸甲", "icon": "甲", "color": (100, 100, 255)},
    "pants": {"name": "腿甲", "icon": "腿", "color": (255, 100, 255)}, "accessory": {"name": "饰品", "icon": "饰", "color": (100, 255, 255)},
}
RARITY_COLORS = {
    "common": (156, 163, 175), "uncommon": (16, 185, 129), "rare": (59, 130, 246),
    "epic": (139, 92, 246), "legendary": (245, 158, 11), "mythic": (239, 68, 68)
}

class BackpackScreen(BaseState):
    def __init__(self, game, player_override=None):
        super().__init__(game)
        self.player = player_override or self.game.player
        self.is_overlay = True
        self.categories = [("weapon", "武器"), ("offhand", "副手"), ("helmet", "头盔"), ("armor", "胸甲"), 
                           ("pants", "腿甲"), ("accessory", "饰品"), ("precious", "珍贵"), ("misc", "其他"), ("all", "全部")]
        self.selected_category = self.categories[0][0]
        self.search_text, self.search_active = "", False
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        
        # 状态管理
        self.dragging_item = None
        self.dragging_from_info = None
        self.context_menu_active = False
        self.context_menu_rect = None
        self.context_menu_options = []
        self.context_menu_target_item = None
        self.feedback_message = ""
        self.feedback_timer = 0
        self.selected_item = None # 用于跟踪被点击选中的物品
        
        self._setup_layout()
        self._setup_animations()

    def handle_event(self, event):
        if self.close_button.handle_event(event) or (event.type == pygame.KEYDOWN and event.key in [pygame.K_b, pygame.K_ESCAPE]):
            if self.dragging_item: self._return_dragging_item()
            self.game.state_stack.pop()
            return

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: self._handle_left_mouse_down(event.pos)
            elif event.button == 3: self._handle_right_mouse_down(event.pos)
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_left_mouse_up(event.pos)

        if self.search_active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE: self.search_text = self.search_text[:-1]
            else: self.search_text += event.unicode
            return

    def update(self):
            """每帧更新背包界面的逻辑，主要负责悬停检测和动画。"""
            # 更新操作反馈消息的计时器
            if self.feedback_message and pygame.time.get_ticks() - self.feedback_timer > 3000:
                self.feedback_message = ""
            
            # 调用悬停检测函数，这是驱动Tooltip的关键
            self._update_hovers()
            
    def _handle_left_mouse_down(self, pos):
        if self.context_menu_active:
            for i, option in enumerate(self.context_menu_options):
                if option['rect'].collidepoint(pos):
                    self._perform_context_menu_action(option['action'])
                    self.context_menu_active = False
                    return
            self.context_menu_active = False
            return
            
        if self.search_rect.collidepoint(pos): self.search_active = True; return
        else: self.search_active = False
        for button in self.category_buttons:
            if button["rect"].collidepoint(pos): self.selected_category = button["id"]; return

        # 从装备槽拾起
        for slot_type, slot_rects in self.equipment_slots.items():
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(pos) and self.player.slots[slot_type][i] is not None:
                    self.dragging_item = self.player.slots[slot_type][i]
                    ### --- 核心修改：记录拖拽图标的尺寸 --- ###
                    self.dragging_from_info = {'type': 'equipped', 'slot': slot_type, 'index': i, 'size': rect.size}
                    self.player.unequip(self.dragging_item)
                    return
        # 从背包拾起
        filtered_items = self._get_filtered_items()
        for i, rect in enumerate(self.backpack_slots):
            if rect.collidepoint(pos) and i < len(filtered_items):
                self.dragging_item = filtered_items[i]
                ### --- 核心修改：记录拖拽图标的尺寸 --- ###
                self.dragging_from_info = {'type': 'backpack', 'size': rect.size}
                self.player.backpack.remove(self.dragging_item)
                return

    def _handle_left_mouse_up(self, pos):
        if not self.dragging_item: return

        # 标志位，用于判断是否成功放置
        dropped_successfully = False

        # 1. 检查是否放置在合法的装备槽
        if hasattr(self.dragging_item, 'slot') and self.dragging_item.slot:
            slot_type = self.dragging_item.slot
            if slot_type in self.equipment_slots:
                for i, rect in enumerate(self.equipment_slots[slot_type]):
                    if rect.collidepoint(pos):
                        # 与目标槽位的物品交换
                        target_item = self.player.slots[slot_type][i]
                        if target_item: self.player.unequip(target_item)
                        self.player.equip(self.dragging_item, specific_index=i)
                        if target_item: self.player.backpack.append(target_item)
                        
                        dropped_successfully = True
                        break
                if dropped_successfully:
                    self.dragging_item = None
                    return

        ### --- 核心修复：新增检查是否放置在背包区域 --- ###
        # 2. 如果没有成功装备，则检查是否放置在了背包网格区域内
        if self.grid_rect.collidepoint(pos):
            # 只要是扔回背包区域，就视为成功卸下
            self.player.backpack.append(self.dragging_item)
            dropped_successfully = True
        
        if dropped_successfully:
            self.dragging_item = None
            return
        ### --- 修复结束 --- ###

        # 3. 如果以上所有情况都未发生（比如扔在界面空白处），则视为无效操作，返回原处
        self._return_dragging_item()
    def _handle_right_mouse_down(self, pos):
        # ... (右键菜单逻辑不变, 此处省略以保持简洁) ...
        if self.context_menu_active: self.context_menu_active = False; return
        target_item = None; item_is_equipped = False
        for slot_type, slot_rects in self.equipment_slots.items():
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(pos) and self.player.slots[slot_type][i] is not None:
                    target_item = self.player.slots[slot_type][i]; item_is_equipped = True; break
            if target_item: break
        if not target_item:
            filtered_items = self._get_filtered_items()
            for i, rect in enumerate(self.backpack_slots):
                if rect.collidepoint(pos) and i < len(filtered_items):
                    target_item = filtered_items[i]; break
        if target_item:
            self.context_menu_target_item = target_item; options = []
            if item_is_equipped: options.append({'text': '卸下', 'action': 'unequip'})
            else: options.append({'text': '穿戴', 'action': 'equip'})
            if target_item.__class__ in UPGRADE_MAP: options.append({'text': '淬炼', 'action': 'upgrade'})
            menu_width, menu_height = 120, len(options) * 40 + 10
            self.context_menu_rect = pygame.Rect(pos[0], pos[1], menu_width, menu_height)
            for i, option in enumerate(options):
                option['rect'] = pygame.Rect(self.context_menu_rect.x + 5, self.context_menu_rect.y + 5 + i * 40, menu_width - 10, 35)
            self.context_menu_options = options; self.context_menu_active = True

    def _return_dragging_item(self):
        """将拖拽的物品返回原处或背包。"""
        if self.dragging_item and self.dragging_from_info:
            if self.dragging_from_info['type'] == 'equipped':
                # 如果是从装备槽拖出的，尝试放回原位
                slot, index = self.dragging_from_info['slot'], self.dragging_from_info['index']
                if self.player.slots[slot][index] is None: # 如果原位空了
                    self.player.equip(self.dragging_item, index)
                else: # 如果原位被占了，就放回背包
                    self.player.backpack.append(self.dragging_item)
            else: # 从背包拖出的，直接放回背包
                self.player.backpack.append(self.dragging_item)
        self.dragging_item = None; self.dragging_from_info = None

    def _perform_context_menu_action(self, action):
        item = self.context_menu_target_item
        if action == 'equip':
            if hasattr(item, 'slot') and item.slot:
                unequipped_item = self.player.equip(item)
                if unequipped_item: self.player.backpack.append(unequipped_item)
                if item in self.player.backpack: self.player.backpack.remove(item)
        elif action == 'unequip':
            self.player.unequip(item)
            self.player.backpack.append(item)
        elif action == 'upgrade':
            feedback = self.player.upgrade_equipment(item)
            self.feedback_message = feedback
            self.feedback_timer = pygame.time.get_ticks()
        self.context_menu_target_item = None

    def draw(self, surface):
        # ... (背景和头部绘制不变)
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 160)); surface.blit(overlay, (0, 0))
        self._draw_modern_panel(surface, self.container_rect, (25, 30, 50, 240))
        self._draw_header(surface)
        self._draw_sidebar(surface); self._draw_inventory_area(surface)
        self._draw_character_panel(surface)
        self._draw_item_details_and_upgrade(surface)
        self._draw_dragging_item(surface)
        self._draw_context_menu(surface)
        self.close_button.draw(surface)
        self.tooltip_manager.draw(surface)

    def _draw_dragging_item(self, surface):
        if not self.dragging_item or not self.dragging_from_info: return
        
        mouse_pos = pygame.mouse.get_pos()
        item_name = get_display_name(self.dragging_item)
        rarity = getattr(self.dragging_item, 'rarity', 'common')
        rarity_color = RARITY_COLORS.get(rarity, TEXT_COLOR)
        
        # 使用记录下来的尺寸，如果没有则使用默认值
        card_size = self.dragging_from_info.get('size', (60, 60))
        card_rect = pygame.Rect(0, 0, *card_size)
        card_rect.center = mouse_pos
        
        drag_surf = pygame.Surface(card_size, pygame.SRCALPHA)
        pygame.draw.rect(drag_surf, (*rarity_color, 180), drag_surf.get_rect(), border_radius=8)
        pygame.draw.rect(drag_surf, rarity_color, drag_surf.get_rect(), width=2, border_radius=8)
        
        font = self._get_font('small', 12 if card_size[0] < 60 else 14)
        if font.size(item_name)[0] > card_rect.width - 6:
            item_name = item_name[:4] + ".."
        text = font.render(item_name, True, TEXT_COLOR)
        text_rect = text.get_rect(center=(card_size[0]//2, card_size[1]//2))
        drag_surf.blit(text, text_rect)
        
        surface.blit(drag_surf, card_rect.topleft)

    def _draw_context_menu(self, surface):
        if not self.context_menu_active: return

        mouse_pos = pygame.mouse.get_pos()
        # 绘制菜单背景
        pygame.draw.rect(surface, (30, 35, 55), self.context_menu_rect, border_radius=8)
        pygame.draw.rect(surface, (70, 80, 100), self.context_menu_rect, width=2, border_radius=8)

        # 绘制选项
        font = self._get_font('small', 16)
        for option in self.context_menu_options:
            is_hovered = option['rect'].collidepoint(mouse_pos)
            text_color = HOVER_COLOR if is_hovered else TEXT_COLOR
            
            if is_hovered:
                pygame.draw.rect(surface, (70, 80, 100, 100), option['rect'], border_radius=6)

            text_surf = font.render(option['text'], True, text_color)
            text_rect = text_surf.get_rect(centery=option['rect'].centery, x=option['rect'].x + 10)
            surface.blit(text_surf, text_rect)

    def _get_font(self, font_name, default_size=20):
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts: return self.game.fonts[font_name]
        except: pass
        return pygame.font.Font(None, default_size)
    def _setup_animations(self): self.hover_animation, self.glow_animation = {}, 0
    def _generate_ui_elements(self):
        self.category_buttons = []
        btn_h, btn_s, start_y = 45, 8, self.sidebar_rect.y + 20
        available_height = self.sidebar_rect.height - 40; num_cats = len(self.categories)
        btn_h = (available_height - (num_cats - 1) * btn_s) // num_cats
        for i, (cat_id, name) in enumerate(self.categories):
            rect = pygame.Rect(self.sidebar_rect.x + 15, start_y + i * (btn_h + btn_s), self.sidebar_rect.width - 30, btn_h)
            self.category_buttons.append({"id": cat_id, "name": name, "rect": rect, "hover": False})
        self.backpack_slots = []
        cols, rows, slot_size = 10, 6, min((self.grid_rect.width - 20) // 10 - 5, (self.grid_rect.height - 20) // 6 - 5)
        for row in range(rows):
            for col in range(cols):
                x, y = self.grid_rect.x + 10 + col * (slot_size + 5), self.grid_rect.y + 10 + row * (slot_size + 5)
                self.backpack_slots.append(pygame.Rect(x, y, slot_size, slot_size))
        self._generate_equipment_slots()
        close_btn_rect = pygame.Rect(self.container_rect.right - 45, self.container_rect.top + 10, 35, 35)
        self.close_button = Button(close_btn_rect, "X", self.game.fonts['normal'])
    def _generate_equipment_slots(self):
        self.equipment_slots = {}; player = self.player
        model_rect = pygame.Rect(self.character_panel_rect.x + 15, self.character_panel_rect.y + 15, self.character_panel_rect.width - 30, 300)
        slot_size, spacing = 50, 10; center_x = model_rect.centerx
        self.equipment_slots["helmet"] = [pygame.Rect(center_x - slot_size/2, model_rect.top + 10, slot_size, slot_size)]
        armor_rect = pygame.Rect(center_x - slot_size/2, model_rect.top + slot_size + spacing + 10, slot_size, slot_size)
        self.equipment_slots["armor"] = [armor_rect]
        self.equipment_slots["pants"] = [pygame.Rect(center_x - slot_size/2, armor_rect.bottom + spacing, slot_size, slot_size)]
        weapon_slots = []
        for i in range(player.SLOT_CAPACITY.get("weapon", 1)):
            weapon_slots.append(pygame.Rect(armor_rect.left - slot_size - spacing, armor_rect.centery - slot_size/2 + i * (slot_size + spacing), slot_size, slot_size))
        self.equipment_slots["weapon"] = weapon_slots
        self.equipment_slots["offhand"] = [pygame.Rect(armor_rect.right + spacing, armor_rect.centery - slot_size/2, slot_size, slot_size)] if player.SLOT_CAPACITY.get("offhand", 0) > 0 else []
        accessory_slots = []
        num_accessory_slots = player.SLOT_CAPACITY.get("accessory", 0)
        total_accessory_width = num_accessory_slots * slot_size + (num_accessory_slots - 1) * 5
        start_x = model_rect.centerx - total_accessory_width / 2
        for i in range(num_accessory_slots):
            accessory_slots.append(pygame.Rect(start_x + i * (slot_size + 5), model_rect.bottom - slot_size - 10, slot_size, slot_size))
        self.equipment_slots["accessory"] = accessory_slots
    def _get_filtered_items(self):
        items = self.player.backpack.copy()
        if self.selected_category != "all":
            slot_categories = ["weapon", "offhand", "helmet", "armor", "pants", "accessory"]; type_categories = ["precious", "misc"]
            if self.selected_category in slot_categories: items = [item for item in items if hasattr(item, 'slot') and item.slot == self.selected_category]
            elif self.selected_category in type_categories: items = [item for item in items if hasattr(item, 'type') and item.type == self.selected_category]
        if self.search_text: items = [item for item in items if self.search_text.lower() in get_display_name(item).lower()]
        return items

    def _update_hovers(self):
        mouse_pos = pygame.mouse.get_pos()
        hovered_item = None

        # 如果正在拖拽或右键菜单已打开，则不显示任何提示
        if self.context_menu_active or self.dragging_item:
            self.tooltip_manager.update(None)
            return

        all_elements = []

        # --- 核心修复：简化并修正了检测已装备物品的逻辑 ---
        # 1. 遍历已装备物品
        for slot_type, item_list in self.player.slots.items():
            # 获取该类型槽位的显示矩形
            rect_list = self.equipment_slots.get(slot_type, [])
            for i, item in enumerate(item_list):
                # 确保物品存在，并且有对应的显示矩形
                if item is not None and i < len(rect_list):
                    all_elements.append((rect_list[i], item))
        # --- 修复结束 ---

        # 2. 遍历背包物品 (这部分逻辑是正确的，保持不变)
        filtered_items = self._get_filtered_items()
        for i, rect in enumerate(self.backpack_slots):
            if i < len(filtered_items):
                all_elements.append((rect, filtered_items[i]))
        
        # 3. 检查鼠标是否悬停在任何一个元素上
        for rect, obj in all_elements:
            if rect.collidepoint(mouse_pos):
                hovered_item = obj
                break
        
        # 4. 更新 Tooltip 管理器
        self.tooltip_manager.update(hovered_item)
    def _draw_modern_panel(self, surface, rect, color, border_color=None):
        pygame.draw.rect(surface, color, rect, border_radius=12)
        if border_color is None: border_color = (70, 80, 100, 180)
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=12)
        glow_rect = rect.inflate(-4, -4); pygame.draw.rect(surface, (255, 255, 255, 10), glow_rect, width=1, border_radius=10)
    def _draw_sidebar(self, surface):
        sidebar_bg = self.sidebar_rect.inflate(-5, -5); self._draw_modern_panel(surface, sidebar_bg, (30, 35, 55, 200))
        for button in self.category_buttons:
            is_active, is_hover = button["id"] == self.selected_category, button["rect"].collidepoint(pygame.mouse.get_pos())
            if is_active: bg_color, border_color, text_color = (255, 215, 0, 100), (255, 215, 0), (255, 255, 255)
            elif is_hover: bg_color, border_color, text_color = (70, 80, 100, 120), (100, 110, 130), (240, 240, 240)
            else: bg_color, border_color, text_color = (40, 50, 70, 80), (60, 70, 90), (180, 180, 180)
            button_rect = button["rect"]; pygame.draw.rect(surface, bg_color, button_rect, border_radius=8); pygame.draw.rect(surface, border_color, button_rect, width=2, border_radius=8)
            text_surface = self._get_font('small', 18).render(f"{button['name']}", True, text_color); text_rect = text_surface.get_rect(center=button_rect.center); surface.blit(text_surface, text_rect)
    def _draw_inventory_area(self, surface):
        inventory_bg = self.inventory_rect.inflate(-5, -5); self._draw_modern_panel(surface, inventory_bg, (30, 35, 55, 200))
        search_bg_color, border_color = ((50, 60, 80, 150), (255, 215, 0)) if self.search_active else ((40, 50, 70, 120), (70, 80, 100))
        pygame.draw.rect(surface, search_bg_color, self.search_rect, border_radius=6); pygame.draw.rect(surface, border_color, self.search_rect, width=2, border_radius=6)
        display_text = self.search_text or "搜索物品..."; text_color = (255, 255, 255) if self.search_text else (150, 150, 150)
        search_surface = self._get_font('small', 18).render(display_text, True, text_color); search_text_rect = search_surface.get_rect(x=self.search_rect.x + 10, centery=self.search_rect.centery); surface.blit(search_surface, search_text_rect)
        self._draw_backpack_grid(surface)
    def _draw_backpack_grid(self, surface):
        filtered_items = self._get_filtered_items()
        for i, slot_rect in enumerate(self.backpack_slots):
            bg_color = (50, 60, 80, 30); border_color = (80, 90, 110, 180)
            pygame.draw.rect(surface, bg_color, slot_rect, border_radius=6); pygame.draw.rect(surface, border_color, slot_rect, width=2, border_radius=6)
            if i < len(filtered_items):
                item = filtered_items[i]
                if item == self.dragging_item: continue # Don't draw item in its original slot if dragging
                item_name = get_display_name(item); font = self._get_font('small', 12) 
                rarity = getattr(item, 'rarity', 'common'); rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['common'])
                pygame.draw.rect(surface, (*rarity_color, 40), slot_rect, border_radius=6)
                if font.size(item_name)[0] > slot_rect.width - 8: item_name = item_name[:5] + ".."
                item_surface = font.render(item_name, True, (255, 255, 255)); item_rect = item_surface.get_rect(center=slot_rect.center); surface.blit(item_surface, item_rect)
                pygame.draw.rect(surface, rarity_color, (slot_rect.x, slot_rect.y, slot_rect.width, 3), border_top_left_radius=2, border_top_right_radius=2)

    def _draw_equipment_slots(self, surface):
        EMPTY_SLOT_COLOR = (80, 80, 80) # 定义空槽位的暗灰色

        for slot_type, slot_rects in self.equipment_slots.items():
            slot_config = SLOT_CONFIG.get(slot_type, {"name": slot_type, "icon": "?"})
            
            for i, slot_rect in enumerate(slot_rects):
                item_in_slot = self.player.slots[slot_type][i]

                ### --- 核心修改：根据物品品质动态决定颜色 --- ###
                if item_in_slot:
                    # 如果槽内有物品，使用物品的品质颜色
                    rarity = getattr(item_in_slot, 'rarity', 'common')
                    base_color = RARITY_COLORS.get(rarity, (100, 100, 100))
                else:
                    # 如果槽位为空，使用预设的暗灰色
                    base_color = EMPTY_SLOT_COLOR

                bg_color = (*base_color, 50)
                border_color = base_color
                
                pygame.draw.rect(surface, bg_color, slot_rect, border_radius=8)
                pygame.draw.rect(surface, border_color, slot_rect, width=2, border_radius=8)
                
                # 绘制物品或槽位名称 (这部分逻辑不变)
                if item_in_slot and item_in_slot != self.dragging_item:
                    item_name = get_display_name(item_in_slot)
                    font = self._get_font('small', 13)
                    if font.size(item_name)[0] > slot_rect.width - 6: item_name = item_name[:3] + ".."
                    text = font.render(item_name, True, (255, 255, 255))
                    text_rect = text.get_rect(center=slot_rect.center)
                    surface.blit(text, text_rect)
                elif not item_in_slot:
                    font = self._get_font('small', 14)
                    # 空槽位的文字也使用更暗的颜色
                    text_surf = font.render(slot_config["name"], True, (100, 100, 100))
                    text_rect = text_surf.get_rect(center=slot_rect.center)
                    surface.blit(text_surf, text_rect)
    def _setup_layout(self):
        margin, header_height, sidebar_width, char_panel_width = 40, 80, 200, 320
        self.container_rect = pygame.Rect(margin, margin, SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin)
        self.header_rect = pygame.Rect(self.container_rect.x, self.container_rect.y, self.container_rect.width, header_height)
        content_y, content_height = self.header_rect.bottom + 10, self.container_rect.height - header_height - 10
        self.sidebar_rect = pygame.Rect(self.container_rect.x, content_y, sidebar_width, content_height)
        self.character_panel_rect = pygame.Rect(self.container_rect.right - char_panel_width, content_y, char_panel_width, content_height)
        self.inventory_rect = pygame.Rect(self.sidebar_rect.right + 10, content_y, self.character_panel_rect.left - self.sidebar_rect.right - 20, content_height)
        self.search_rect = pygame.Rect(self.inventory_rect.x + 10, self.inventory_rect.y + 10, self.inventory_rect.width - 20, 35)
        self.grid_rect = pygame.Rect(self.inventory_rect.x + 10, self.search_rect.bottom + 15, self.inventory_rect.width - 20, self.inventory_rect.height - 60)
        self._generate_ui_elements()
    def _draw_header(self, surface):
        header_bg = self.header_rect.inflate(-10, -10); self._draw_modern_panel(surface, header_bg, (35, 40, 65, 200))
        title_font = self._get_font('large', 32); title_text = title_font.render("整备行囊", True, (255, 215, 0))
        title_rect = title_text.get_rect(x=header_bg.x + 20, centery=header_bg.centery); surface.blit(title_text, title_rect)
        OFFSET_FROM_RIGHT = 150
        gold_text = f"💰 {self.player.gold} G"; gold_font = self.game.fonts['normal']
        estimated_gold_surf = gold_font.render(gold_text.replace('💰', '  '), True, (0,0,0))
        estimated_gold_rect = estimated_gold_surf.get_rect(right=header_bg.right - OFFSET_FROM_RIGHT, centery=header_bg.centery + 15)
        draw_text_with_emoji_fallback(surface, gold_text, estimated_gold_rect.topleft, (255, 215, 0))
        crystal_text = f"💎 {self.player.refinement_crystals}"; crystal_font = self.game.fonts['normal']
        estimated_crystal_surf = crystal_font.render(crystal_text.replace('💎', '  '), True, (0,0,0))
        estimated_crystal_rect = estimated_crystal_surf.get_rect(right=header_bg.right - OFFSET_FROM_RIGHT, centery=header_bg.centery - 15)
        draw_text_with_emoji_fallback(surface, crystal_text, estimated_crystal_rect.topleft, (173, 216, 230))
    def _draw_character_panel(self, surface):
        panel_bg = self.character_panel_rect.inflate(-5, -5); self._draw_modern_panel(surface, panel_bg, (30, 35, 55, 200))
        model_area = pygame.Rect(panel_bg.x + 15, panel_bg.y + 15, panel_bg.width - 30, 300)
        pygame.draw.rect(surface, (20, 25, 40, 150), model_area, border_radius=10)
        self._draw_equipment_slots(surface)
        self._draw_item_details_and_upgrade(surface)
    def _draw_item_details_and_upgrade(self, surface):
        details_area = pygame.Rect(self.character_panel_rect.left, self.character_panel_rect.top + 320, self.character_panel_rect.width, self.character_panel_rect.height - 320)
        if self.feedback_message and pygame.time.get_ticks() - self.feedback_timer < 3000:
            color = (100, 255, 100) if "成功" in self.feedback_message else (255, 100, 100)
            draw_text(surface, self.feedback_message, self.game.fonts['small'], color, details_area.inflate(-20, -20)); return
        if not self.selected_item:
            draw_text(surface, "左键拖拽以移动装备。\n右键点击装备以查看选项。", self.game.fonts['small'], (150, 150, 150), details_area.inflate(-20, -20)); return
        item_name = get_display_name(self.selected_item); rarity = getattr(self.selected_item, 'rarity', 'common'); name_color = RARITY_COLORS.get(rarity, TEXT_COLOR)
        name_surf = self.game.fonts['normal'].render(item_name, True, name_color); surface.blit(name_surf, (details_area.x + 20, details_area.y + 10))
        desc = inspect.getdoc(self.selected_item) or "没有更多信息了。"; desc_rect = pygame.Rect(details_area.x + 20, details_area.y + 50, details_area.width - 40, details_area.height - 120)
        draw_text(surface, desc, self.game.fonts['small'], TEXT_COLOR, desc_rect)