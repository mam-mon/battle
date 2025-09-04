# 文件: states/backpack.py (完整替换)

# ... (所有 import 语句保持不变) ...
import pygame
import math
from .base import BaseState
from ui import draw_text, draw_panel, get_display_name, TooltipManager, Button
from settings import *

# ... (SLOT_CONFIG 和 RARITY_COLORS 保持不变) ...
SLOT_CONFIG = {
    "weapon": {"name": "武器", "icon": "武", "color": (255, 100, 100)},
    "offhand": {"name": "副手", "icon": "副", "color": (100, 255, 100)},
    "helmet": {"name": "头盔", "icon": "头", "color": (255, 255, 100)},
    "armor": {"name": "胸甲", "icon": "甲", "color": (100, 100, 255)},
    "pants": {"name": "腿甲", "icon": "腿", "color": (255, 100, 255)},
    "accessory": {"name": "饰品", "icon": "饰", "color": (100, 255, 255)},
}
RARITY_COLORS = {
    "common": (156, 163, 175), "uncommon": (16, 185, 129), "rare": (59, 130, 246),
    "epic": (139, 92, 246), "legendary": (245, 158, 11),
}

class BackpackScreen(BaseState):
    def __init__(self, game, player_override=None): # <-- 核心修改1
        super().__init__(game)
        self.player = player_override or self.game.player # <-- 核心修改2

        # --- 后续所有用到 self.game.player 的地方，都改成 self.player ---
        self.is_overlay = True
        # ... (其他初始化代码不变) ...
        self.dragging_item, self.dragging_from, self.dragging_from_info = None, None, {}
        self.selected_category, self.search_text, self.search_active = "all", "", False
        self.hover_slot = None
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        self._setup_layout()
        self._setup_animations()

    # ... (除了下面被替换的方法，其他所有方法都不变) ...
    def _get_font(self, font_name, default_size=20):
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts: return self.game.fonts[font_name]
        except: pass
        return pygame.font.Font(None, default_size)

    def _setup_layout(self):
        margin, header_height, sidebar_width, char_panel_width = 40, 80, 200, 280
        self.container_rect = pygame.Rect(margin, margin, SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin)
        self.header_rect = pygame.Rect(self.container_rect.x, self.container_rect.y, self.container_rect.width, header_height)
        content_y, content_height = self.header_rect.bottom + 10, self.container_rect.height - header_height - 10
        self.sidebar_rect = pygame.Rect(self.container_rect.x, content_y, sidebar_width, content_height)
        self.character_panel_rect = pygame.Rect(self.container_rect.right - char_panel_width, content_y, char_panel_width, content_height)
        self.inventory_rect = pygame.Rect(self.sidebar_rect.right + 10, content_y, self.character_panel_rect.left - self.sidebar_rect.right - 20, content_height)
        self.search_rect = pygame.Rect(self.inventory_rect.x + 10, self.inventory_rect.y + 10, self.inventory_rect.width - 20, 35)
        self.grid_rect = pygame.Rect(self.inventory_rect.x + 10, self.search_rect.bottom + 15, self.inventory_rect.width - 20, self.inventory_rect.height - 60)
        self._generate_ui_elements()

    def _setup_animations(self): self.hover_animation, self.glow_animation = {}, 0

    def _generate_ui_elements(self):
        self.category_buttons = []
        categories = [("all", "全部"), ("weapon", "武器"), ("armor", "防具"), ("consumable", "消耗"), ("material", "材料"), ("misc", "其他")]
        btn_h, btn_s, start_y = 45, 8, self.sidebar_rect.y + 20
        for i, (cat_id, name) in enumerate(categories):
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
        self.equipment_slots = {}
        player = self.player # <-- 修改点
        model_rect = pygame.Rect(self.character_panel_rect.x + 15, self.character_panel_rect.y + 15, self.character_panel_rect.width - 30, 300)
        slot_size, spacing = 50, 10
        center_x = model_rect.centerx

        self.equipment_slots["helmet"] = [pygame.Rect(center_x - slot_size/2, model_rect.top + 10, slot_size, slot_size)]
        armor_rect = pygame.Rect(center_x - slot_size/2, model_rect.top + slot_size + spacing + 10, slot_size, slot_size)
        self.equipment_slots["armor"] = [armor_rect]
        self.equipment_slots["pants"] = [pygame.Rect(center_x - slot_size/2, armor_rect.bottom + spacing, slot_size, slot_size)]

        weapon_slots = []
        num_weapon_slots = player.SLOT_CAPACITY.get("weapon", 1)
        for i in range(num_weapon_slots):
            x = armor_rect.left - slot_size - spacing
            y = armor_rect.centery - slot_size/2 + i * (slot_size + spacing)
            weapon_slots.append(pygame.Rect(x, y, slot_size, slot_size))
        self.equipment_slots["weapon"] = weapon_slots

        if player.SLOT_CAPACITY.get("offhand", 0) > 0:
            self.equipment_slots["offhand"] = [pygame.Rect(armor_rect.right + spacing, armor_rect.centery - slot_size/2, slot_size, slot_size)]
        else:
            self.equipment_slots["offhand"] = []

        accessory_slots = []
        num_accessory_slots = player.SLOT_CAPACITY.get("accessory", 0)
        total_accessory_width = num_accessory_slots * slot_size + (num_accessory_slots - 1) * 5
        start_x = model_rect.centerx - total_accessory_width / 2
        accessory_y = model_rect.bottom - slot_size - 10
        for i in range(num_accessory_slots):
            x = start_x + i * (slot_size + 5)
            accessory_slots.append(pygame.Rect(x, accessory_y, slot_size, slot_size))
        self.equipment_slots["accessory"] = accessory_slots

    def handle_event(self, event):
        if self.close_button.handle_event(event): self.game.state_stack.pop(); return
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_b, pygame.K_ESCAPE]:
                if self.dragging_item: self._return_dragging_item()
                self.game.state_stack.pop(); return
            elif event.key == pygame.K_BACKSPACE and self.search_active: self.search_text = self.search_text[:-1]
            elif self.search_active and event.unicode.isprintable(): self.search_text += event.unicode
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.close_button.rect.collidepoint(event.pos): self._handle_mouse_down(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1: self._handle_mouse_up(event.pos)
        elif event.type == pygame.MOUSEMOTION: self._handle_mouse_motion(event.pos)

    def _handle_mouse_down(self, pos):
        player = self.player # <-- 修改点
        if self.search_rect.collidepoint(pos): self.search_active = True; return
        else: self.search_active = False
        for button in self.category_buttons:
            if button["rect"].collidepoint(pos): self.selected_category = button["id"]; return
        if self.dragging_item: return
        for slot_type, slot_rects in self.equipment_slots.items():
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(pos) and player.slots[slot_type][i] is not None:
                    item_to_drag = player.slots[slot_type][i]
                    self.dragging_item = player.unequip(item_to_drag)
                    self.dragging_from = 'equipment'
                    self.dragging_from_info = {'slot_type': slot_type, 'index': i}
                    return
        filtered_items = self._get_filtered_items()
        for i, rect in enumerate(self.backpack_slots):
            if rect.collidepoint(pos) and i < len(filtered_items):
                original_item = filtered_items[i]
                original_index_in_backpack = player.backpack.index(original_item)
                self.dragging_item = player.backpack.pop(original_index_in_backpack)
                self.dragging_from = 'backpack'
                self.dragging_from_info = {'index': original_index_in_backpack}
                return

    def _handle_mouse_up(self, pos):
        if not self.dragging_item: return
        player = self.player # <-- 修改点
        source_type, source_info = self.dragging_from, self.dragging_from_info
        for slot_type, slot_rects in self.equipment_slots.items():
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(pos) and self.dragging_item.slot == slot_type:
                    replaced_item = player.equip(self.dragging_item, specific_index=i)
                    if replaced_item:
                        if source_type == 'backpack':
                            player.backpack.append(replaced_item)
                        elif source_type == 'equipment':
                            player.equip(replaced_item, specific_index=source_info['index'])
                    self.dragging_item = None
                    return
        if self.grid_rect.collidepoint(pos):
            player.backpack.append(self.dragging_item)
            self.dragging_item = None
            return
        self._return_dragging_item()
        self.dragging_item = None

    def _handle_mouse_motion(self, pos):
        for button in self.category_buttons: button["hover"] = button["rect"].collidepoint(pos)
        self.hover_slot = None
        for slot_type, slot_rects in self.equipment_slots.items():
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(pos): self.hover_slot = (slot_type, i); break

    def _get_filtered_items(self):
        items = self.player.backpack.copy() # <-- 修改点
        if self.selected_category != "all":
            items = [item for item in items if hasattr(item, 'type') and item.type == self.selected_category]
        if self.search_text:
            items = [item for item in items if self.search_text.lower() in get_display_name(item).lower()]
        return items

    def _return_dragging_item(self):
        if not self.dragging_item: return
        player = self.player # <-- 修改点
        if self.dragging_from == 'backpack': 
            player.backpack.insert(self.dragging_from_info.get('index', 0), self.dragging_item)
        elif self.dragging_from == 'equipment': 
            player.equip(self.dragging_item)

    def _update_hovers(self):
        if self.dragging_item: self.tooltip_manager.update(None); return
        mouse_pos = pygame.mouse.get_pos()
        player = self.player # <-- 修改点
        hovered_item = None
        all_elements = []
        for slot_type, slot_rects in self.equipment_slots.items():
            equipped_items = player.slots.get(slot_type, [])
            for i, rect in enumerate(slot_rects):
                if equipped_items[i] is not None: all_elements.append((rect, equipped_items[i]))
        filtered_items = self._get_filtered_items()
        for i, rect in enumerate(self.backpack_slots):
            if i < len(filtered_items): all_elements.append((rect, filtered_items[i]))
        for rect, obj in all_elements:
            if rect.collidepoint(mouse_pos): hovered_item = obj; break
        self.tooltip_manager.update(hovered_item)

    def update(self, dt=0):
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): self._last_time = current_time
        dt_ms = current_time - self._last_time; self._last_time = current_time; dt_sec = dt_ms / 1000.0
        self.glow_animation = (self.glow_animation + dt_sec * 3) % (2 * math.pi)
        self.animation_offset = math.sin(self.glow_animation) * 2; self._update_hovers()

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 160)); surface.blit(overlay, (0, 0))
        self._draw_modern_panel(surface, self.container_rect, (25, 30, 50, 240))
        self._draw_header(surface); self._draw_sidebar(surface); self._draw_inventory_area(surface)
        self._draw_character_panel(surface); self._draw_dragging_item(surface)
        self.close_button.draw(surface); self.tooltip_manager.draw(surface)
        if hasattr(self, 'update'): self.update()

    def _draw_modern_panel(self, surface, rect, color, border_color=None):
        pygame.draw.rect(surface, color, rect, border_radius=12)
        if border_color is None: border_color = (70, 80, 100, 180)
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=12)
        glow_rect = rect.inflate(-4, -4); pygame.draw.rect(surface, (255, 255, 255, 10), glow_rect, width=1, border_radius=10)

    def _draw_header(self, surface):
        header_bg = self.header_rect.inflate(-10, -10); self._draw_modern_panel(surface, header_bg, (35, 40, 65, 200))
        title_font = self._get_font('large', 32); title_text = title_font.render("背包系统", True, (255, 215, 0))
        title_rect = title_text.get_rect(x=header_bg.x + 20, centery=header_bg.centery); surface.blit(title_text, title_rect)

    def _draw_sidebar(self, surface):
        sidebar_bg = self.sidebar_rect.inflate(-5, -5); self._draw_modern_panel(surface, sidebar_bg, (30, 35, 55, 200))
        for button in self.category_buttons:
            is_active, is_hover = button["id"] == self.selected_category, button["hover"]
            if is_active: bg_color, border_color, text_color = (255, 215, 0, 100), (255, 215, 0), (255, 255, 255)
            elif is_hover: bg_color, border_color, text_color = (70, 80, 100, 120), (100, 110, 130), (240, 240, 240)
            else: bg_color, border_color, text_color = (40, 50, 70, 80), (60, 70, 90), (180, 180, 180)
            button_rect = button["rect"]; 
            if is_hover: button_rect = button_rect.move(2 + self.animation_offset, 0)
            pygame.draw.rect(surface, bg_color, button_rect, border_radius=8); pygame.draw.rect(surface, border_color, button_rect, width=2, border_radius=8)
            font = self._get_font('small', 18); text = f"{button['name']}"; text_surface = font.render(text, True, text_color); text_rect = text_surface.get_rect(center=button_rect.center); surface.blit(text_surface, text_rect)

    def _draw_inventory_area(self, surface):
        inventory_bg = self.inventory_rect.inflate(-5, -5); self._draw_modern_panel(surface, inventory_bg, (30, 35, 55, 200))
        search_bg_color, border_color = ((50, 60, 80, 150), (255, 215, 0)) if self.search_active else ((40, 50, 70, 120), (70, 80, 100))
        pygame.draw.rect(surface, search_bg_color, self.search_rect, border_radius=6); pygame.draw.rect(surface, border_color, self.search_rect, width=2, border_radius=6)
        search_font = self._get_font('small', 18); display_text = self.search_text or "搜索物品..."; text_color = (255, 255, 255) if self.search_text else (150, 150, 150)
        search_surface = search_font.render(display_text, True, text_color); search_text_rect = search_surface.get_rect(x=self.search_rect.x + 10, centery=self.search_rect.centery); surface.blit(search_surface, search_text_rect)
        if self.search_active and int(self.glow_animation * 2) % 2: pygame.draw.line(surface, (255, 255, 255), (search_text_rect.right + 2, self.search_rect.y + 8), (search_text_rect.right + 2, self.search_rect.bottom - 8), 2)
        self._draw_backpack_grid(surface)

    def _draw_backpack_grid(self, surface):
        filtered_items = self._get_filtered_items()
        for i, slot_rect in enumerate(self.backpack_slots):
            rarity_color = RARITY_COLORS['common']; bg_color, border_color = (40, 50, 70, 60), (60, 70, 90, 120)
            if i < len(filtered_items): item = filtered_items[i]; rarity = getattr(item, 'rarity', 'common'); rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['common']); bg_color, border_color = (*rarity_color, 30), (*rarity_color, 180)
            pygame.draw.rect(surface, bg_color, slot_rect, border_radius=6); pygame.draw.rect(surface, border_color, slot_rect, width=2, border_radius=6)
            if i < len(filtered_items):
                item = filtered_items[i]
                if item != self.dragging_item:
                    item_name = get_display_name(item); font = self._get_font('small', 12) 
                    item_surface = font.render(item_name, True, (255, 255, 255)); 
                    if item_surface.get_width() > slot_rect.width - 8: 
                        item_name = item_name[:5] + ".."
                        item_surface = font.render(item_name, True, (255, 255, 255))
                    item_rect = item_surface.get_rect(center=slot_rect.center); surface.blit(item_surface, item_rect)
                    pygame.draw.rect(surface, rarity_color, (slot_rect.x, slot_rect.y, slot_rect.width, 3), border_top_left_radius=2, border_top_right_radius=2)

    def _draw_character_panel(self, surface):
        panel_bg = self.character_panel_rect.inflate(-5, -5); self._draw_modern_panel(surface, panel_bg, (30, 35, 55, 200))
        model_area = pygame.Rect(panel_bg.x + 15, panel_bg.y + 15, panel_bg.width - 30, 300)
        pygame.draw.rect(surface, (20, 25, 40, 150), model_area, border_radius=10)
        self._draw_equipment_slots(surface); self._draw_character_stats(surface, panel_bg)

    def _draw_equipment_slots(self, surface):
        player = self.player # <-- 修改点
        for slot_type, slot_rects in self.equipment_slots.items():
            slot_config = SLOT_CONFIG.get(slot_type, {"name": slot_type, "icon": "?", "color": (100, 100, 100)})
            for i, slot_rect in enumerate(slot_rects):
                is_hover = self.hover_slot == (slot_type, i)
                bg_color, border_color = ((*slot_config["color"], 50), slot_config["color"]) if is_hover else ((40, 50, 70, 100), (70, 80, 100))
                pygame.draw.rect(surface, bg_color, slot_rect, border_radius=8)
                pygame.draw.rect(surface, border_color, slot_rect, width=2, border_radius=8)
                item_in_slot = player.slots[slot_type][i]
                if item_in_slot is not None:
                    if item_in_slot != self.dragging_item:
                        item_name = get_display_name(item_in_slot)
                        font = self._get_font('small', 13)
                        if font.size(item_name)[0] > slot_rect.width - 6: 
                            item_name = item_name[:3] + ".."
                        text = font.render(item_name, True, (255, 255, 255))
                        text_rect = text.get_rect(center=slot_rect.center)
                        surface.blit(text, text_rect)
                else:
                    font = self._get_font('small', 14)
                    text_surf = font.render(slot_config["name"], True, (80, 90, 110))
                    text_rect = text_surf.get_rect(center=slot_rect.center)
                    surface.blit(text_surf, text_rect)

    def _draw_character_stats(self, surface, panel_bg):
        stats_area = pygame.Rect(panel_bg.x + 15, panel_bg.bottom - 185, panel_bg.width - 30, 170)
        pygame.draw.rect(surface, (20, 25, 40, 150), stats_area, border_radius=10)
        player = self.player # <-- 修改点
        stats_data = [("最大生命", f"{int(getattr(player, 'max_hp', 0))}"), ("攻击", f"{int(getattr(player, 'attack', 0))}"), ("防御", f"{int(getattr(player, 'defense', 0))}"), ("攻击速度", f"{getattr(player, 'attack_speed', 0):.2f}"), ("暴击率", f"{getattr(player, 'crit_chance', 0) * 100:.1f}%"), ("暴击伤害", f"{getattr(player, 'crit_multiplier', 0) * 100:.1f}%")]
        stats_font = self.game.fonts['small']; line_height = 26; y_offset = stats_area.y + 12
        for i, (name, value) in enumerate(stats_data):
            y_pos = y_offset + i * line_height
            name_surface = stats_font.render(f"{name}:", True, (180, 180, 180)); name_rect = name_surface.get_rect(x=stats_area.x + 15, centery=y_pos); surface.blit(name_surface, name_rect)
            value_surface = stats_font.render(str(value), True, (255, 215, 0)); value_rect = value_surface.get_rect(right=stats_area.right - 15, centery=y_pos); surface.blit(value_surface, value_rect)

    def _draw_dragging_item(self, surface):
        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos(); item_name = get_display_name(self.dragging_item)
            font = self._get_font('normal', 20); text_surface = font.render(item_name, True, (255, 255, 255)); text_rect = text_surface.get_rect(center=mouse_pos)
            bg_rect = text_rect.inflate(20, 12); pygame.draw.rect(surface, (40, 50, 80, 220), bg_rect, border_radius=8); pygame.draw.rect(surface, (255, 215, 0), bg_rect, width=2, border_radius=8); surface.blit(text_surface, text_rect)