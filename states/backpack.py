# states/backpack.py
import pygame
import math
from .base import BaseState
from ui import draw_text, draw_panel, get_display_name
from settings import *

# 插槽类型到中文名称和图标的映射
SLOT_CONFIG = {
    "weapon": {"name": "主武器", "icon": "武", "color": (255, 100, 100)},
    "offhand": {"name": "副手", "icon": "副", "color": (100, 255, 100)},
    "helmet": {"name": "头盔", "icon": "头", "color": (255, 255, 100)},
    "armor": {"name": "胸甲", "icon": "甲", "color": (100, 100, 255)},
    "pants": {"name": "腿甲", "icon": "腿", "color": (255, 100, 255)},
    "accessory": {"name": "饰品", "icon": "饰", "color": (100, 255, 255)},
}

# 物品稀有度配置
RARITY_COLORS = {
    "common": (156, 163, 175),      # 灰色
    "uncommon": (16, 185, 129),     # 绿色  
    "rare": (59, 130, 246),         # 蓝色
    "epic": (139, 92, 246),         # 紫色
    "legendary": (245, 158, 11),    # 橙色
}

class BackpackScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.dragging_item = None
        self.dragging_from = None
        self.dragging_from_info = {}
        self.selected_category = "all"
        self.search_text = ""
        self.search_active = False
        self.tooltip_item = None
        self.tooltip_timer = 0
        self.animation_offset = 0
        self.hover_slot = None
        
        # 现代化UI布局
        self._setup_layout()
        self._setup_animations()

    def _get_font(self, font_name, default_size=20):
        """安全获取字体"""
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)

    def _setup_layout(self):
        """设置现代化布局"""
        margin = 40
        header_height = 80
        sidebar_width = 200
        character_panel_width = 280
        
        # 主容器
        self.container_rect = pygame.Rect(
            margin, margin, 
            SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin
        )
        
        # 顶部标题栏
        self.header_rect = pygame.Rect(
            self.container_rect.x, self.container_rect.y,
            self.container_rect.width, header_height
        )
        
        # 主要内容区域
        content_y = self.header_rect.bottom + 10
        content_height = self.container_rect.height - header_height - 10
        
        # 左侧分类栏
        self.sidebar_rect = pygame.Rect(
            self.container_rect.x, content_y,
            sidebar_width, content_height
        )
        
        # 右侧角色面板
        self.character_panel_rect = pygame.Rect(
            self.container_rect.right - character_panel_width, content_y,
            character_panel_width, content_height
        )
        
        # 中间背包区域
        self.inventory_rect = pygame.Rect(
            self.sidebar_rect.right + 10, content_y,
            self.character_panel_rect.left - self.sidebar_rect.right - 20, content_height
        )
        
        # 搜索框
        self.search_rect = pygame.Rect(
            self.inventory_rect.x + 10, self.inventory_rect.y + 10,
            self.inventory_rect.width - 20, 35
        )
        
        # 背包网格
        grid_y = self.search_rect.bottom + 15
        self.grid_rect = pygame.Rect(
            self.inventory_rect.x + 10, grid_y,
            self.inventory_rect.width - 20, self.inventory_rect.height - 60
        )
        
        self._generate_ui_elements()

    def _setup_animations(self):
        """设置动画参数"""
        self.hover_animation = {}
        self.glow_animation = 0

    def _generate_ui_elements(self):
        """生成UI元素"""
        # 分类按钮
        self.category_buttons = []
        categories = [
            ("all", "[全]", "全部物品"),
            ("weapon", "[武]", "武器装备"),
            ("armor", "[甲]", "防具护甲"), 
            ("consumable", "[药]", "消耗品"),
            ("material", "[材]", "制作材料"),
            ("misc", "[杂]", "杂项物品")
        ]
        
        button_height = 45
        button_spacing = 8
        start_y = self.sidebar_rect.y + 20
        
        for i, (cat_id, icon, name) in enumerate(categories):
            rect = pygame.Rect(
                self.sidebar_rect.x + 15, 
                start_y + i * (button_height + button_spacing),
                self.sidebar_rect.width - 30, button_height
            )
            self.category_buttons.append({
                "id": cat_id, "icon": icon, "name": name, 
                "rect": rect, "hover": False
            })
        
        # 背包网格
        self.backpack_slots = []
        cols, rows = 10, 6
        slot_size = min(
            (self.grid_rect.width - 20) // cols - 5,
            (self.grid_rect.height - 20) // rows - 5
        )
        
        for row in range(rows):
            for col in range(cols):
                x = self.grid_rect.x + 10 + col * (slot_size + 5)
                y = self.grid_rect.y + 10 + row * (slot_size + 5)
                rect = pygame.Rect(x, y, slot_size, slot_size)
                self.backpack_slots.append(rect)
        
        # 角色装备槽
        self._generate_equipment_slots()

    def _generate_equipment_slots(self):
        """生成角色装备槽"""
        self.equipment_slots = {}
        
        # 角色模型区域
        model_rect = pygame.Rect(
            self.character_panel_rect.x + 20,
            self.character_panel_rect.y + 20,
            self.character_panel_rect.width - 40, 200
        )
        
        slot_size = 50
        center_x = model_rect.centerx
        
        # 装备槽位置
        positions = {
            "helmet": (center_x - slot_size//2, model_rect.y + 10),
            "armor": (center_x - slot_size//2, model_rect.y + 75),
            "pants": (center_x - slot_size//2, model_rect.y + 140),
            "weapon": (center_x - slot_size - 25, model_rect.y + 75),
            "offhand": (center_x + 25, model_rect.y + 75),
        }
        
        # 饰品槽（底部）
        accessory_y = model_rect.bottom + 20
        accessory_slots = []
        for i in range(3):
            x = center_x - slot_size * 1.5 + i * slot_size
            accessory_slots.append(pygame.Rect(x, accessory_y, slot_size, slot_size))
        
        # 生成装备槽
        for slot_type, (x, y) in positions.items():
            if slot_type == "accessory":
                self.equipment_slots[slot_type] = accessory_slots
            else:
                self.equipment_slots[slot_type] = [pygame.Rect(x, y, slot_size, slot_size)]

    def handle_event(self, event):
        """处理事件"""
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_b, pygame.K_ESCAPE]:
                if self.dragging_item:
                    self._return_dragging_item()
                self.game.state_stack.pop()
                return
            elif event.key == pygame.K_BACKSPACE and self.search_active:
                self.search_text = self.search_text[:-1]
            elif self.search_active and event.unicode.isprintable():
                self.search_text += event.unicode

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_mouse_down(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._handle_mouse_up(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_motion(event.pos)

    def _handle_mouse_down(self, pos):
        """处理鼠标按下"""
        # 检查搜索框点击
        if self.search_rect.collidepoint(pos):
            self.search_active = True
            return
        else:
            self.search_active = False
        
        # 检查分类按钮
        for button in self.category_buttons:
            if button["rect"].collidepoint(pos):
                self.selected_category = button["id"]
                return
        
        if self.dragging_item:
            return
            
        # 检查装备槽
        for slot_type, slot_rects in self.equipment_slots.items():
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(pos) and i < len(self.game.player.slots.get(slot_type, [])):
                    item = self.game.player.slots[slot_type][i]
                    self.dragging_item = self.game.player.unequip(item)
                    self.dragging_from = 'equipment'
                    self.dragging_from_info = {'slot_type': slot_type, 'index': i}
                    return
        
        # 检查背包槽
        filtered_items = self._get_filtered_items()
        for i, rect in enumerate(self.backpack_slots):
            if rect.collidepoint(pos) and i < len(filtered_items):
                # 找到原始背包中的索引
                original_item = filtered_items[i]
                original_index = self.game.player.backpack.index(original_item)
                self.dragging_item = self.game.player.backpack.pop(original_index)
                self.dragging_from = 'backpack'
                self.dragging_from_info = {'index': original_index}
                return

    def _handle_mouse_up(self, pos):
        """处理鼠标释放"""
        if not self.dragging_item:
            return
            
        item_placed = False
        
        # 尝试装备到装备槽
        for slot_type, slot_rects in self.equipment_slots.items():
            if hasattr(self.dragging_item, 'slot') and self.dragging_item.slot == slot_type:
                for i, rect in enumerate(slot_rects):
                    if rect.collidepoint(pos):
                        # 如果槽位已有装备，先卸下
                        if i < len(self.game.player.slots.get(slot_type, [])):
                            old_item = self.game.player.slots[slot_type][i]
                            self.game.player.unequip(old_item)
                            self.game.player.backpack.append(old_item)
                        
                        self.game.player.equip(self.dragging_item)
                        item_placed = True
                        break
            if item_placed:
                break
        
        # 如果没有装备成功，放回背包
        if not item_placed:
            if self.grid_rect.collidepoint(pos):
                self.game.player.backpack.append(self.dragging_item)
                item_placed = True
        
        # 如果都没成功，返回原位置
        if not item_placed:
            self._return_dragging_item()
        
        self.dragging_item = None

    def _handle_mouse_motion(self, pos):
        """处理鼠标移动"""
        # 更新按钮悬停状态
        for button in self.category_buttons:
            button["hover"] = button["rect"].collidepoint(pos)
        
        # 更新装备槽悬停
        self.hover_slot = None
        for slot_type, slot_rects in self.equipment_slots.items():
            for i, rect in enumerate(slot_rects):
                if rect.collidepoint(pos):
                    self.hover_slot = (slot_type, i)
                    break

    def _get_filtered_items(self):
        """获取过滤后的物品列表"""
        items = self.game.player.backpack.copy()
        
        # 分类过滤
        if self.selected_category != "all":
            items = [item for item in items if getattr(item, 'type', 'misc') == self.selected_category]
        
        # 搜索过滤
        if self.search_text:
            items = [item for item in items if self.search_text.lower() in get_display_name(item).lower()]
        
        return items

    def _return_dragging_item(self):
        """返回拖拽物品到原位置"""
        if not self.dragging_item:
            return
            
        if self.dragging_from == 'backpack':
            self.game.player.backpack.insert(self.dragging_from_info['index'], self.dragging_item)
        elif self.dragging_from == 'equipment':
            self.game.player.equip(self.dragging_item)

    def update(self, dt):
        """更新动画"""
        self.glow_animation = (self.glow_animation + dt * 3) % (2 * math.pi)
        self.animation_offset = math.sin(self.glow_animation) * 2
        
    def update(self, dt=0):
        """更新动画 - 兼容版本"""
        import time
        current_time = time.time()
        if not hasattr(self, '_last_time'):
            self._last_time = current_time
        dt = current_time - self._last_time
        self._last_time = current_time
        
        self.glow_animation = (self.glow_animation + dt * 3) % (2 * math.pi)
        self.animation_offset = math.sin(self.glow_animation) * 2

    def draw(self, surface):
        """绘制界面"""
        # 绘制背景
        if len(self.game.state_stack) > 1:
            self.game.state_stack[-2].draw(surface)
        
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))
        
        # 主容器背景
        self._draw_modern_panel(surface, self.container_rect, (25, 30, 50, 240))
        
        # 绘制各个区域
        self._draw_header(surface)
        self._draw_sidebar(surface)
        self._draw_inventory_area(surface)
        self._draw_character_panel(surface)
        self._draw_dragging_item(surface)
        
        # 调用更新动画
        if hasattr(self, 'update'):
            self.update()

    def _draw_modern_panel(self, surface, rect, color, border_color=None):
        """绘制现代化面板"""
        # 主背景
        pygame.draw.rect(surface, color, rect, border_radius=12)
        
        # 边框
        if border_color is None:
            border_color = (70, 80, 100, 180)
        pygame.draw.rect(surface, border_color, rect, width=2, border_radius=12)
        
        # 内发光效果
        glow_rect = rect.inflate(-4, -4)
        pygame.draw.rect(surface, (255, 255, 255, 10), glow_rect, width=1, border_radius=10)

    def _draw_header(self, surface):
        """绘制标题栏"""
        # 标题背景
        header_bg = self.header_rect.inflate(-10, -10)
        self._draw_modern_panel(surface, header_bg, (35, 40, 65, 200))
        
        # 标题文字 - 兼容性字体处理
        title_font = self._get_font('large', 32)
        title_text = title_font.render("[ 背包系统 ]", True, (255, 215, 0))
        title_rect = title_text.get_rect(
            x=header_bg.x + 20, 
            centery=header_bg.centery
        )
        surface.blit(title_text, title_rect)
        
        # 统计信息
        player = self.game.player
        stats_font = self._get_font('small', 18)
        
        # 安全获取属性值
        gold = getattr(player, 'gold', getattr(player, 'coins', 1250))
        weight = getattr(player, 'weight', 45)
        max_weight = getattr(player, 'max_weight', 100)
        
        stats = [
            f"物品: {len(player.backpack)}/60",
            f"金币: {gold}",
            f"重量: {weight}/{max_weight}"
        ]
        
        # 重新布局统计信息，避免重叠
        stats_x = header_bg.right - 320  # 增加左边距
        stat_width = 100  # 增加每个统计框的宽度
        stat_spacing = 5   # 减少间距
        
        for i, stat in enumerate(stats):
            stat_bg = pygame.Rect(
                stats_x + i * (stat_width + stat_spacing), 
                header_bg.y + 15, 
                stat_width, 25
            )
            pygame.draw.rect(surface, (50, 60, 80, 150), stat_bg, border_radius=6)
            
            # 使用更小的字体避免文字溢出
            stat_text = self._get_font('small', 16).render(stat, True, (200, 200, 200))
            stat_rect = stat_text.get_rect(center=stat_bg.center)
            surface.blit(stat_text, stat_rect)

    def _draw_sidebar(self, surface):
        """绘制侧边栏"""
        sidebar_bg = self.sidebar_rect.inflate(-5, -5)
        self._draw_modern_panel(surface, sidebar_bg, (30, 35, 55, 200))
        
        # 分类按钮
        for button in self.category_buttons:
            is_active = button["id"] == self.selected_category
            is_hover = button["hover"]
            
            # 按钮背景
            if is_active:
                bg_color = (255, 215, 0, 100)
                border_color = (255, 215, 0)
                text_color = (255, 255, 255)
            elif is_hover:
                bg_color = (70, 80, 100, 120)
                border_color = (100, 110, 130)
                text_color = (240, 240, 240)
            else:
                bg_color = (40, 50, 70, 80)
                border_color = (60, 70, 90)
                text_color = (180, 180, 180)
            
            button_rect = button["rect"]
            if is_hover:
                button_rect = button_rect.move(2 + self.animation_offset, 0)
            
            pygame.draw.rect(surface, bg_color, button_rect, border_radius=8)
            pygame.draw.rect(surface, border_color, button_rect, width=2, border_radius=8)
            
            # 图标和文字
            font = self._get_font('small', 18)
            text = f"{button['icon']} {button['name']}"
            text_surface = font.render(text, True, text_color)
            text_rect = text_surface.get_rect(center=button_rect.center)
            surface.blit(text_surface, text_rect)

    def _draw_inventory_area(self, surface):
        """绘制背包区域"""
        inventory_bg = self.inventory_rect.inflate(-5, -5)
        self._draw_modern_panel(surface, inventory_bg, (30, 35, 55, 200))
        
        # 搜索框
        search_bg_color = (50, 60, 80, 150) if self.search_active else (40, 50, 70, 120)
        border_color = (255, 215, 0) if self.search_active else (70, 80, 100)
        
        pygame.draw.rect(surface, search_bg_color, self.search_rect, border_radius=6)
        pygame.draw.rect(surface, border_color, self.search_rect, width=2, border_radius=6)
        
        # 搜索文字
        search_font = self._get_font('small', 18)
        display_text = self.search_text if self.search_text else "搜索物品..."
        text_color = (255, 255, 255) if self.search_text else (150, 150, 150)
        
        search_surface = search_font.render(display_text, True, text_color)
        search_text_rect = search_surface.get_rect(
            x=self.search_rect.x + 10, 
            centery=self.search_rect.centery
        )
        surface.blit(search_surface, search_text_rect)
        
        # 光标
        if self.search_active:
            cursor_x = search_text_rect.right + 2
            cursor_y1 = self.search_rect.y + 8
            cursor_y2 = self.search_rect.bottom - 8
            if int(self.glow_animation * 2) % 2:  # 闪烁效果
                pygame.draw.line(surface, (255, 255, 255), 
                               (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)
        
        # 背包网格
        self._draw_backpack_grid(surface)

    def _draw_backpack_grid(self, surface):
        """绘制背包网格"""
        filtered_items = self._get_filtered_items()
        
        for i, slot_rect in enumerate(self.backpack_slots):
            # 槽位背景
            if i < len(filtered_items):
                item = filtered_items[i]
                rarity = getattr(item, 'rarity', 'common')
                rarity_color = RARITY_COLORS.get(rarity, RARITY_COLORS['common'])
                
                # 带稀有度的背景
                bg_color = (*rarity_color, 30)
                border_color = (*rarity_color, 180)
            else:
                bg_color = (40, 50, 70, 60)
                border_color = (60, 70, 90, 120)
            
            pygame.draw.rect(surface, bg_color, slot_rect, border_radius=6)
            pygame.draw.rect(surface, border_color, slot_rect, width=2, border_radius=6)
            
            # 物品内容
            if i < len(filtered_items):
                item = filtered_items[i]
                if item != self.dragging_item:
                    item_name = get_display_name(item)
                    # 背包物品名称也缩短一些
                    if len(item_name) > 6:
                        item_name = item_name[:5] + ".."
                    
                    # 物品文字 - 使用更小字体
                    item_font = self._get_font('small', 14)
                    item_surface = item_font.render(item_name, True, (255, 255, 255))
                    item_rect = item_surface.get_rect(center=slot_rect.center)
                    surface.blit(item_surface, item_rect)
                    
                    # 稀有度条
                    rarity_rect = pygame.Rect(slot_rect.x, slot_rect.y, slot_rect.width, 3)
                    pygame.draw.rect(surface, rarity_color, rarity_rect, border_radius=2)

    def _draw_character_panel(self, surface):
        """绘制角色面板"""
        panel_bg = self.character_panel_rect.inflate(-5, -5)
        self._draw_modern_panel(surface, panel_bg, (30, 35, 55, 200))
        
        # 角色模型区域
        model_area = pygame.Rect(
            panel_bg.x + 15, panel_bg.y + 15,
            panel_bg.width - 30, 200
        )
        pygame.draw.rect(surface, (20, 25, 40, 150), model_area, border_radius=10)
        
        # 角色预览文字
        model_font = self._get_font('small', 16)
        model_text = model_font.render("[ 角色模型 ]", True, (150, 150, 150))
        model_rect = model_text.get_rect(center=model_area.center)
        surface.blit(model_text, model_rect)
        
        # 装备槽
        self._draw_equipment_slots(surface)
        
        # 角色属性
        self._draw_character_stats(surface, panel_bg)

    def _draw_equipment_slots(self, surface):
        """绘制装备槽"""
        for slot_type, slot_rects in self.equipment_slots.items():
            slot_config = SLOT_CONFIG.get(slot_type, {"name": slot_type, "icon": "?", "color": (100, 100, 100)})
            
            for i, slot_rect in enumerate(slot_rects):
                is_hover = self.hover_slot == (slot_type, i)
                
                # 槽位背景
                if is_hover:
                    bg_color = (*slot_config["color"], 50)
                    border_color = slot_config["color"]
                else:
                    bg_color = (40, 50, 70, 100)
                    border_color = (70, 80, 100)
                
                pygame.draw.rect(surface, bg_color, slot_rect, border_radius=8)
                pygame.draw.rect(surface, border_color, slot_rect, width=2, border_radius=8)
                
                # 装备图标或物品
                equipped_items = self.game.player.slots.get(slot_type, [])
                if i < len(equipped_items):
                    item = equipped_items[i]
                    if item != self.dragging_item:
                        item_name = get_display_name(item)
                        # 更严格的长度限制，适应小槽位
                        if len(item_name) > 4:
                            item_name = item_name[:3] + ".."
                        
                        font = self._get_font('small', 16)  # 使用更小的字体
                        text = font.render(item_name, True, (255, 255, 255))
                        text_rect = text.get_rect(center=slot_rect.center)
                        surface.blit(text, text_rect)
                else:
                    # 空槽位显示槽位类型
                    icon_font = self._get_font('small', 14)  # 使用更小字体
                    icon_text = icon_font.render(slot_config["icon"], True, (120, 120, 120))
                    icon_rect = icon_text.get_rect(center=slot_rect.center)
                    surface.blit(icon_text, icon_rect)
            
            # 槽位标签
            if slot_rects:
                label_font = self._get_font('small', 16)  # 标签也使用小一些的字体
                label_text = label_font.render(slot_config["name"], True, (200, 200, 200))
                
                if slot_type == "accessory":
                    # 饰品标签居中
                    center_x = (slot_rects[0].centerx + slot_rects[-1].centerx) // 2
                    label_rect = label_text.get_rect(centerx=center_x, bottom=slot_rects[0].top - 5)
                else:
                    label_rect = label_text.get_rect(centerx=slot_rects[0].centerx, bottom=slot_rects[0].top - 5)
                
                surface.blit(label_text, label_rect)

    def _draw_character_stats(self, surface, panel_bg):
        """绘制角色属性"""
        stats_y = panel_bg.y + 320
        stats_area = pygame.Rect(panel_bg.x + 15, stats_y, panel_bg.width - 30, 150)
        pygame.draw.rect(surface, (20, 25, 40, 150), stats_area, border_radius=10)
        
        player = self.game.player
        stats_data = [
            ("攻击力", getattr(player, 'attack', 125)),
            ("防御力", getattr(player, 'defense', 89)),
            ("生命值", f"{int(getattr(player, 'hp', 450))}/{int(getattr(player, 'max_hp', 450))}"),
            ("暴击率", f"{getattr(player, 'crit_chance', 0.1) * 100:.0f}%"),
            ("移动速度", getattr(player, 'speed', 315)),
        ]
        
        stats_font = self.game.fonts['small']
        y_offset = stats_area.y + 15
        
        for i, (name, value) in enumerate(stats_data):
            y_pos = y_offset + i * 25
            
            # 属性名
            name_surface = stats_font.render(f"{name}:", True, (180, 180, 180))
            name_rect = name_surface.get_rect(x=stats_area.x + 15, y=y_pos)
            surface.blit(name_surface, name_rect)
            
            # 属性值
            value_surface = stats_font.render(str(value), True, (255, 215, 0))
            value_rect = value_surface.get_rect(right=stats_area.right - 15, y=y_pos)
            surface.blit(value_surface, value_rect)

    def _draw_dragging_item(self, surface):
        """绘制拖拽中的物品"""
        if self.dragging_item:
            mouse_pos = pygame.mouse.get_pos()
            item_name = get_display_name(self.dragging_item)
            
            # 拖拽背景
            font = self._get_font('normal', 20)
            text_surface = font.render(item_name, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=mouse_pos)
            
            bg_rect = text_rect.inflate(20, 12)
            pygame.draw.rect(surface, (40, 50, 80, 220), bg_rect, border_radius=8)
            pygame.draw.rect(surface, (255, 215, 0), bg_rect, width=2, border_radius=8)
            surface.blit(text_surface, text_rect)