# states/dungeon_screen.py (完整替换)

import pygame
import math
import random
import inspect
from .base import BaseState
import dungeon_generator
from player_sprite import Player
from monster_sprite import Monster
from treasure_sprite import TreasureChest
from portal_sprite import PortalSprite
from camera import Camera
import Equips
from settings import *
from ui import ModernStoryButton, draw_text
from door_sprite import Door

NODE_STYLE = {
    "start": {"color": (100, 255, 100), "name": "起始"}, "combat": {"color": (200, 200, 200), "name": "战斗"}, 
    "event": {"color": (255, 255, 100), "name": "事件"}, "treasure": {"color": (255, 215, 0), "name": "宝藏"},
    "elite": {"color": (255, 50, 50), "name": "精英"}, "boss": {"color": (160, 32, 240), "name": "首领"},
    "rest": {"color": (100, 200, 255), "name": "休息"}, "shop": {"color": (100, 255, 200), "name": "商店"},
    "forge": {"color": (150, 150, 150), "name": "锻造"}
}

class DungeonScreen(BaseState):
    def __init__(self, game, dungeon_id="sunstone_ruins", floor_number=1):
        super().__init__(game)
        self.dungeon_id = dungeon_id
        self.floor_number = floor_number
        self.dungeon_data = self.game.dungeon_data.get(dungeon_id, {})
        self.current_floor_data = next((pool for pool in self.dungeon_data.get("floor_pools", []) if floor_number in pool["floors"]), {})
        
        self.impassable_sprites = pygame.sprite.Group()

        # 1. 生成地牢的静态部分（墙壁、地板、门）
        self.all_sprites, self.wall_sprites, self.door_sprites, self.logical_rooms, self.start_room = \
            dungeon_generator.generate_new_dungeon_floor(num_rooms=10, floor_data=self.current_floor_data, impassable_group_for_doors=self.impassable_sprites)
        
        self.impassable_sprites.add(self.wall_sprites)

        # 2. 初始化玩家
        start_pos = self.start_room.world_rect.center
        self.player_sprite = Player(start_pos[0], start_pos[1])
        self.all_sprites.add(self.player_sprite)
        
        # 3. 初始化摄像机
        self.camera = Camera(DUNGEON_VIEW_WIDTH, DUNGEON_VIEW_HEIGHT)
        
        # 4. 初始化空的动态精灵组
        self.monster_sprites = pygame.sprite.Group()
        self.treasure_sprites = pygame.sprite.Group()
        self.portal_sprites = pygame.sprite.Group()
        
        ### --- 核心修改：在这里一次性生成本层所有的动态内容 --- ###
        print("正在预生成本层所有房间内容...")
        for room in self.logical_rooms:
            if not room.is_cleared:
                # 为每个未清空的房间生成怪物
                for m_data in room.monsters:
                    self.monster_sprites.add(Monster(m_data, room.world_rect))
                
                # 如果是宝藏房，生成宝箱
                if room.type == "treasure":
                    self.treasure_sprites.add(TreasureChest(*room.world_rect.center))
            
            # 如果是Boss房，生成传送门
            elif room.type == "boss":
                self.portal_sprites.add(PortalSprite(*room.world_rect.center))
        
        # 将所有新生成的动态精灵一次性加入总绘制组
        self.all_sprites.add(self.monster_sprites, self.treasure_sprites, self.portal_sprites)
        print("内容生成完毕！")
        
        # 5. 初始化状态和UI
        self.is_returning = False
        self.current_room = self.start_room
        self.pending_lockdown_room = None
        self.minimap_glow = 0.0
        self._create_ui_buttons()
        
        # 6. 手动触发一次“进入起始房间”的逻辑（现在只负责关门和特殊事件）
        self._on_enter_room(self.start_room)

    def _on_enter_room(self, new_room):
        """当玩家进入一个新房间时触发。"""
        self.current_room = new_room
        print(f"进入房间: {new_room.x}, {new_room.y}, 类型: {new_room.type}")
        
        ### --- 核心修改：此函数不再负责生成精灵 --- ###
        # self._populate_room_sprites() # <--- 已删除

        # 关门和处理特殊房间的逻辑保持不变
        if not new_room.is_cleared and not new_room.is_corridor and new_room.type in ["combat", "elite", "boss"]:
            self.pending_lockdown_room = new_room
        
        self._handle_special_room_entry()
        
    # ... (其他所有函数，如 update, draw, on_monster_defeated 等，都保持不变) ...
    def handle_event(self, event):
        if self.is_returning: return
        for button_name, button in self.ui_buttons.items():
            if button.handle_event(event): self._handle_ui_button_action(button_name); return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b: self._handle_ui_button_action("backpack")
            elif event.key == pygame.K_t: self._handle_ui_button_action("talents")
            elif event.key == pygame.K_c: self._handle_ui_button_action("attributes")
            elif event.key == pygame.K_ESCAPE: self._handle_ui_button_action("exit")
    def update(self):
        if self.is_returning:
            self.player_sprite.rect.x += 1 
            self.is_returning = False
            
        # 计算时间增量 dt_sec
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_update_time'): self._last_update_time = current_time
        dt_ms = current_time - self._last_update_time
        self._last_update_time = current_time
        dt_sec = dt_ms / 1000.0

        self.player_sprite.update(self.impassable_sprites)
        self.camera.update(self.player_sprite)
        self.monster_sprites.update(self.wall_sprites, dt_sec)
        
        self._check_current_room()
        if self.pending_lockdown_room:
            self._check_and_trigger_lockdown()
        self._check_interactions()
        self._update_animations(dt_sec)
    def draw(self, surface):
        surface.fill((10, 15, 25))
        view_surf = surface.subsurface(pygame.Rect(DUNGEON_VIEW_X, DUNGEON_VIEW_Y, DUNGEON_VIEW_WIDTH, DUNGEON_VIEW_HEIGHT))
        view_surf.fill((10, 15, 25))
        for sprite in self.all_sprites: view_surf.blit(sprite.image, self.camera.apply(sprite.rect))
        self._draw_ui_panel(surface)
    def _check_current_room(self):
        colliding_rooms = [r for r in self.logical_rooms if r.world_rect.colliderect(self.player_sprite.rect)]
        if colliding_rooms and colliding_rooms[0] is not self.current_room: self._on_enter_room(colliding_rooms[0])
    def _check_and_trigger_lockdown(self):
        room_doors = [d for d in self.door_sprites if self.pending_lockdown_room.world_rect.collidepoint(d.rect.center)]
        is_player_clear_of_doors = not any(self.player_sprite.rect.colliderect(d.rect) for d in room_doors)
        if is_player_clear_of_doors:
            print(f"玩家已进入房间 {self.pending_lockdown_room.x}, {self.pending_lockdown_room.y}，正在关门...")
            for door in room_doors: door.close()
            self.pending_lockdown_room = None
    def on_monster_defeated(self, monster_uid):
        self.current_room.monsters = [m for m in self.current_room.monsters if m['uid'] != monster_uid]
        for monster in self.monster_sprites:
            if monster.uid == monster_uid: monster.kill()
        if not self.current_room.monsters and self.current_room.type in ["combat", "elite", "boss"]:
            self.current_room.is_cleared = True
            print(f"房间 {self.current_room.x}, {self.current_room.y} 已清空! 正在开门...")
            for door in self.door_sprites:
                if self.current_room.world_rect.collidepoint(door.rect.center): door.open()
    def _check_interactions(self):
        if not self.current_room.is_cleared:
            collided_monster = pygame.sprite.spritecollideany(self.player_sprite, self.monster_sprites)
            if collided_monster:
                from .combat import CombatScreen
                self.game.state_stack.append(CombatScreen(self.game, collided_monster.enemy_id, collided_monster.uid)); self.is_returning = True; return
            collided_treasure = pygame.sprite.spritecollideany(self.player_sprite, self.treasure_sprites)
            if collided_treasure: self._open_treasure_chest(collided_treasure)
    def _get_font(self, font_name, default_size=20):
        try: return self.game.fonts[font_name]
        except (AttributeError, KeyError): return pygame.font.Font(None, default_size)
    def _create_ui_buttons(self):
        self.ui_buttons = {}; button_w, button_h = 100, 40; padding = 10
        configs = [("backpack", "背包 B", (59, 130, 246)), ("talents", "天赋 T", (139, 92, 246)),
                   ("attributes", "属性 C", (255, 100, 100)), ("exit", "退出", (200, 80, 80))]
        start_y = BUTTON_AREA_UI_Y + padding
        for i, (key, text, color) in enumerate(configs):
            rect = pygame.Rect(BUTTON_AREA_UI_X + (UI_PANEL_WIDTH - button_w) // 2, start_y + i * (button_h + padding), button_w, button_h)
            self.ui_buttons[key] = ModernStoryButton(rect, text, self._get_font('small'), color)
    def _handle_ui_button_action(self, action):
        from .backpack import BackpackScreen; from .talents_screen import TalentsScreen
        from .attributes_screen import AttributesScreen; from .title import TitleScreen
        if action == "backpack": self.game.state_stack.append(BackpackScreen(self.game))
        elif action == "talents": self.game.state_stack.append(TalentsScreen(self.game))
        elif action == "attributes": self.game.state_stack.append(AttributesScreen(self.game))
        elif action == "exit": self.game.state_stack = [TitleScreen(self.game)]
        self.is_returning = True
    def _handle_special_room_entry(self):
        if self.current_room.is_cleared: return
        room_type = self.current_room.type; sub_screen_opened = False
        if room_type == "event":
            from .event_screen import EventScreen
            if self.game.event_data:
                event_id = random.choice(list(self.game.event_data.keys()))
                self.game.state_stack.append(EventScreen(self.game, event_id, self.current_room)); sub_screen_opened = True
        elif room_type == "shop":
            from .shop_screen import ShopScreen
            self.game.state_stack.append(ShopScreen(self.game, self.current_room)); sub_screen_opened = True
        elif room_type == "rest":
            from .rest_screen import RestScreen
            self.game.state_stack.append(RestScreen(self.game, self.current_room)); sub_screen_opened = True
        if sub_screen_opened: self.is_returning = True
    def _open_treasure_chest(self, chest_sprite):
        loot_config = self.current_floor_data.get("treasure_loot", {}); item_count = loot_config.get("item_count", 2)
        all_items = [cls for name, cls in inspect.getmembers(Equips, inspect.isclass) if issubclass(cls, Equips.Equipment) and cls is not Equips.Equipment and cls is not Equips.DragonHeart]
        if all_items:
            choices = [random.choice(all_items)() for _ in range(item_count)]
            from .choice_screen import ChoiceScreen
            self.game.state_stack.append(ChoiceScreen(self.game, choices, self.current_room)); self.is_returning = True
        chest_sprite.kill()
    def _update_animations(self, dt):
        self.minimap_glow = (self.minimap_glow + dt * 3) % (2 * math.pi)
    def _draw_ui_panel(self, surface):
        pygame.draw.rect(surface, (20, 25, 40), (0, 0, UI_PANEL_WIDTH, SCREEN_HEIGHT))
        pygame.draw.line(surface, (50, 60, 80), (UI_PANEL_WIDTH, 0), (UI_PANEL_WIDTH, SCREEN_HEIGHT), 2)
        self._draw_modern_minimap(surface); self._draw_player_info_panel(surface)
        for button in self.ui_buttons.values(): button.draw(surface, 0)
    def _draw_modern_minimap(self, surface):
        minimap_rect = pygame.Rect(MINIMAP_UI_X + 10, MINIMAP_UI_Y + 10, MINIMAP_UI_WIDTH - 20, MINIMAP_UI_HEIGHT - 20)
        pygame.draw.rect(surface, (20, 25, 40, 220), minimap_rect, border_radius=12)
        glow_intensity = int((math.sin(self.minimap_glow) + 1) * 20 + 30)
        pygame.draw.rect(surface, (70, 80, 100, glow_intensity), minimap_rect, width=3, border_radius=12)
        title_font = self._get_font('small', 16)
        title_text = title_font.render(f"第{self.floor_number}层 - {self.dungeon_data.get('name', '未知地牢')}", True, (255, 215, 0))
        surface.blit(title_text, (minimap_rect.x + 10, minimap_rect.y + 5))
        grid_rect = pygame.Rect(minimap_rect.x + 10, minimap_rect.y + 30, minimap_rect.width - 20, minimap_rect.height - 40 - 20)
        cell_size = 18; spacing = 4; padded_cell_size = cell_size + spacing
        map_center_x, map_center_y = grid_rect.center
        center_cell_base_x, center_cell_base_y = map_center_x - cell_size // 2, map_center_y - cell_size // 2
        rooms_to_draw = [r for r in self.logical_rooms if not r.is_corridor]
        for room in rooms_to_draw:
            rel_x, rel_y = (room.x - self.current_room.x) // 2, (room.y - self.current_room.y) // 2
            draw_x, draw_y = center_cell_base_x + rel_x * padded_cell_size, center_cell_base_y + rel_y * padded_cell_size
            cell_rect = pygame.Rect(draw_x, draw_y, cell_size, cell_size)
            if not grid_rect.colliderect(cell_rect): continue
            base_color = NODE_STYLE.get(room.type, {"color": (255, 255, 255)})["color"]
            is_cleared = room.is_cleared or room.type == "start"
            alpha = 255 if is_cleared else 150
            final_color = base_color if is_cleared else tuple(c // 2 for c in base_color)
            pygame.draw.rect(surface, (*final_color, alpha), cell_rect, border_radius=3)
            if room is self.current_room: pygame.draw.rect(surface, (255, 255, 255), cell_rect, 2, border_radius=4)
        legend_y = minimap_rect.bottom - 25; legend_font = self._get_font('small', 12)
        room_name = NODE_STYLE.get(self.current_room.type, {"name": "未知"})["name"]
        legend_text = f"当前: {room_name}房间"
        surface.blit(legend_font.render(legend_text, True, (200, 200, 200)), (minimap_rect.x + 10, legend_y))
    def _draw_player_info_panel(self, surface):
        panel_rect = pygame.Rect(PLAYER_INFO_UI_X + 10, PLAYER_INFO_UI_Y + 10, PLAYER_INFO_UI_WIDTH - 20, PLAYER_INFO_UI_HEIGHT - 20)
        pygame.draw.rect(surface, (20, 25, 40, 220), panel_rect, border_radius=12)
        pygame.draw.rect(surface, (70, 80, 100), panel_rect, width=3, border_radius=12)
        font_small = self._get_font('small'); font_normal = self._get_font('normal')
        player = self.game.player
        draw_text(surface, f"Lv.{player.level} {player.name}", font_normal, TEXT_COLOR, (panel_rect.x + 10, panel_rect.y + 10))
        draw_text(surface, f"HP: {int(player.hp)}/{player.max_hp}", font_small, (255, 100, 100), (panel_rect.x + 10, panel_rect.y + 40))
        pygame.draw.rect(surface, (50, 50, 50), (panel_rect.x + 10, panel_rect.y + 60, panel_rect.width - 30, 10), border_radius=5)
        hp_bar_width = (panel_rect.width - 30) * (player.hp / player.max_hp) if player.max_hp > 0 else 0
        pygame.draw.rect(surface, (200, 50, 50), (panel_rect.x + 10, panel_rect.y + 60, hp_bar_width, 10), border_radius=5)
        draw_text(surface, f"EXP: {player.exp}/{player.exp_to_next_level}", font_small, (100, 255, 100), (panel_rect.x + 10, panel_rect.y + 75))
        pygame.draw.rect(surface, (50, 50, 50), (panel_rect.x + 10, panel_rect.y + 95, panel_rect.width - 30, 10), border_radius=5)
        exp_bar_width = (panel_rect.width - 30) * (player.exp / player.exp_to_next_level) if player.exp_to_next_level > 0 else 0
        pygame.draw.rect(surface, (50, 200, 50), (panel_rect.x + 10, panel_rect.y + 95, exp_bar_width, 10), border_radius=5)
        draw_text(surface, f"攻击: {int(player.attack)}", font_small, TEXT_COLOR, (panel_rect.x + 10, panel_rect.y + 110))
        draw_text(surface, f"防御: {int(player.defense)}", font_small, TEXT_COLOR, (panel_rect.x + 150, panel_rect.y + 110))
        draw_text(surface, f"金币: {player.gold}", font_small, (255, 215, 0), (panel_rect.x + 10, panel_rect.y + 130))