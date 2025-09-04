import pygame
import random
from .base import BaseState
from dungeon_generator import Floor
from player_sprite import Player
from monster_sprite import Monster
from treasure_sprite import TreasureChest
import Equips
from settings import *
from ui import Button
from portal_sprite import PortalSprite # <-- 新增这一行

NODE_STYLE = {"start": {"color": (100, 255, 100)},"combat": {"color": (200, 200, 200)}, "event": {"color": (255, 255, 100)},"treasure": {"color": (255, 215, 0)},"elite": {"color": (255, 50, 50)},"boss": {"color": (160, 32, 240)},"rest": {"color": (100, 200, 255)},"shop": {"color": (100, 255, 200)},"forge": {"color": (150, 150, 150)}}

# File: states/dungeon_screen.py

class DungeonScreen(BaseState):
    def __init__(self, game, dungeon_id="sunstone_ruins", floor_number=1):
        super().__init__(game)

        self.dungeon_id = dungeon_id
        self.floor_number = floor_number
        self.dungeon_data = self.game.dungeon_data[dungeon_id]

        self.current_floor_data = None
        for pool in self.dungeon_data.get("floor_pools", []):
            if self.floor_number in pool["floors"]:
                self.current_floor_data = pool
                break

        self.floor = Floor()
        self.floor.generate_floor(num_rooms=8, floor_data=self.current_floor_data)

        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.monster_group = pygame.sprite.Group()
        self.chest_group = pygame.sprite.GroupSingle()
        self.portal_group = pygame.sprite.GroupSingle() # <-- 新增传送门组

        self.door_rects = {}
        # self.exit_portal_button = None <-- 删除这一行

        self.current_room = self.floor.start_room
        self._enter_room(self.current_room)

        backpack_button_rect = pygame.Rect(SCREEN_WIDTH - 160, 10, 140, 50)
        self.backpack_button = Button(backpack_button_rect, "背包 (B)", self.game.fonts['small'])
        talents_button_rect = pygame.Rect(backpack_button_rect.left - 150, 10, 140, 50)
        self.talents_button = Button(talents_button_rect, "天赋 (T)", self.game.fonts['small'])
        
        # 文件: states/dungeon_screen.py (替换这个函数)

    def _enter_room(self, room):
        self.current_room = room
        if not (self.current_room.type == 'boss' and self.current_room.is_cleared):
            self.exit_portal_button = None
        print(f"进入房间 ({room.x}, {room.y}), 类型: {room.type}")

        # --- 核心改动在这里 ---
        room_type = self.current_room.type
        is_cleared = self.current_room.is_cleared

        # 只有未清理过的特殊房间才会触发一次性事件
        if not is_cleared:
            if room_type == "event":
                from .event_screen import EventScreen
                event_id = random.choice(list(self.game.event_data.keys()))
                self.game.state_stack.append(EventScreen(self.game, event_id, self.current_room))
            elif room_type == "shop":
                from .shop_screen import ShopScreen
                self.game.state_stack.append(ShopScreen(self.game, self.current_room))
            
            # --- 新增的分支 ---
            elif room_type == "rest":
                from .rest_screen import RestScreen # 导入我们刚创建的休息界面
                # 弹出休息界面，并把当前房间信息传过去
                self.game.state_stack.append(RestScreen(self.game, self.current_room))

        self._sync_sprites()
        self.door_rects = self._generate_doors()

    def _generate_doors(self):
        if not self.current_room.is_cleared: return {}
        doors = {}; door_size, margin = 60, 10
        if self.current_room.doors["N"]: doors["N"] = pygame.Rect(SCREEN_WIDTH/2 - door_size/2, 0, door_size, margin)
        if self.current_room.doors["S"]: doors["S"] = pygame.Rect(SCREEN_WIDTH/2 - door_size/2, SCREEN_HEIGHT - margin, door_size, margin)
        if self.current_room.doors["W"]: doors["W"] = pygame.Rect(0, SCREEN_HEIGHT/2 - door_size/2, margin, door_size)
        if self.current_room.doors["E"]: doors["E"] = pygame.Rect(SCREEN_WIDTH - margin, SCREEN_HEIGHT/2 - door_size/2, margin, door_size)
        return doors

    # 用这个版本完整替换你的 handle_event 方法
    # 文件: states/dungeon_screen.py (替换 handle_event 方法)
    def handle_event(self, event):
        from .backpack import BackpackScreen
        from .talents_screen import TalentsScreen

        if self.backpack_button.handle_event(event):
            self.game.state_stack.append(BackpackScreen(self.game))
            return

        if self.talents_button.handle_event(event):
            self.game.state_stack.append(TalentsScreen(self.game))
            return

        # --- 旧的传送门按钮点击逻辑已从这里移除 ---

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_b:
                self.game.state_stack.append(BackpackScreen(self.game))
            elif event.key == pygame.K_t:
                self.game.state_stack.append(TalentsScreen(self.game))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pass # 这里不再需要处理宝箱点击，所以是空的
                            
    def _sync_sprites(self):
        self.monster_group.empty()
        self.chest_group.empty()

        if not self.current_room.is_cleared:
            if self.current_room.type in ["combat", "elite", "boss"]:
                for monster_data in self.current_room.monsters:
                    self.monster_group.add(Monster(monster_data))
            elif self.current_room.type == "treasure":
                self.chest_group.add(TreasureChest(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))

    def _open_treasure_chest(self, chest_sprite):
        """打开宝箱，并根据当前楼层配置(JSON)生成选项 (带详细调试)"""
        print("--- 进入 _open_treasure_chest 方法 ---")
        
        # 检查点 A: 检查楼层数据是否存在
        if not self.current_floor_data or "treasure_loot" not in self.current_floor_data:
            print(">>> 错误：在dungeon_data.json中未找到当前楼层的 treasure_loot 配置！")
            return

        loot_config = self.current_floor_data["treasure_loot"]
        rarity_weights = loot_config.get("rarity_weights", {"common": 100})
        item_count = loot_config.get("item_count", 2)
        print(f"使用配置: {item_count}个物品, 掉落率: {rarity_weights}")

        # --- 物品生成逻辑 (不变) ---
        item_pool = {rarity: [] for rarity in rarity_weights.keys()}
        all_item_classes = [getattr(Equips, name) for name in dir(Equips) if isinstance(getattr(Equips, name), type) and issubclass(getattr(Equips, name), Equips.Equipment) and getattr(Equips, name) is not Equips.Equipment]
        for item_class in all_item_classes:
            temp_item = item_class()
            if hasattr(temp_item, 'rarity') and temp_item.rarity in item_pool:
                item_pool[temp_item.rarity].append(item_class)
        
        rarities_to_spawn = random.choices(list(rarity_weights.keys()), weights=list(rarity_weights.values()), k=item_count)
        choices = []
        for rarity in rarities_to_spawn:
            if item_pool.get(rarity):
                item_class = random.choice(item_pool[rarity])
                choices.append(item_class())
        
        # 检查点 B: 检查是否成功生成了物品
        print(f"成功生成了 {len(choices)} 个物品选项。")

        if not choices:
            print(">>> 错误: 未能生成任何物品！方法提前退出。")
            self.current_room.is_cleared = True
            self.door_rects = self._generate_doors()
            chest_sprite.kill()
            return

        # 检查点 C: 准备弹出选择界面
        print(f"准备弹出选择界面，物品为: {[getattr(c, 'display_name', '未知') for c in choices]}")
        from .choice_screen import ChoiceScreen
        self.game.state_stack.append(ChoiceScreen(self.game, choices, self.current_room))
        
        # 检查点 D: 确认界面已弹出
        print(">>> 选择界面已弹出到状态栈。 killing chest...")
        
        chest_sprite.kill()

    def on_monster_defeated(self, defeated_monster_uid):
        self.current_room.monsters = [m for m in self.current_room.monsters if m['uid'] != defeated_monster_uid]
        self._sync_sprites()
        if not self.current_room.monsters:
            self.current_room.is_cleared = True
            self.door_rects = self._generate_doors()
            if self.current_room.type == "boss":
                # 不再创建按钮，而是创建传送门精灵并添加到组里
                self.portal_group.add(PortalSprite(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                
    # 文件: states/dungeon_screen.py (替换 update 方法)
    def update(self):
        self.player_group.update()

        if not self.current_room.is_cleared:
            # 检查与怪物的碰撞
            collided_monster = pygame.sprite.spritecollideany(self.player, self.monster_group)
            if collided_monster:
                from .combat import CombatScreen
                self.game.state_stack.append(CombatScreen(self.game, collided_monster.enemy_id, collided_monster.uid))
                self.monster_group.empty()
                return

            # 检查与宝箱的碰撞
            collided_chest = pygame.sprite.spritecollideany(self.player, self.chest_group)
            if collided_chest:
                self._open_treasure_chest(collided_chest)
                return

        else: # 房间已清理
            # --- 核心修改在这里 ---
            # 检查与传送门的碰撞
            collided_portal = pygame.sprite.spritecollideany(self.player, self.portal_group)
            if collided_portal:
                print("进入下一层！")
                next_floor_number = self.floor_number + 1
                self.game.state_stack.pop()
                self.game.state_stack.append(DungeonScreen(self.game, self.dungeon_id, next_floor_number))
                return
            # --- 修改结束 ---

            # 检查与门的碰撞
            for direction, door_rect in self.door_rects.items():
                if self.player.rect.colliderect(door_rect):
                    self._change_room(direction)
                    break
                
    def _change_room(self, direction):
        x, y = self.current_room.x, self.current_room.y; next_room_coord = None
        if direction == "N": next_room_coord = (x, y - 1)
        if direction == "S": next_room_coord = (x, y + 1)
        if direction == "W": next_room_coord = (x - 1, y)
        if direction == "E": next_room_coord = (x + 1, y)
        if next_room_coord in self.floor.rooms:
            next_room = self.floor.rooms[next_room_coord]; self._enter_room(next_room)
            if direction == "N": self.player.rect.bottom = SCREEN_HEIGHT - 15
            if direction == "S": self.player.rect.top = 15
            if direction == "W": self.player.rect.right = SCREEN_WIDTH - 15
            if direction == "E": self.player.rect.left = 15

    # 文件: states/dungeon_screen.py (替换 draw 方法)
    def draw(self, surface):
        surface.fill(BG_COLOR)
        for door_rect in self.door_rects.values(): pygame.draw.rect(surface, (100, 200, 100), door_rect)

        # if self.exit_portal_button: self.exit_portal_button.draw(surface) <-- 删除这行
        self.portal_group.draw(surface) # <-- 新增这行，绘制传送门精灵

        self.monster_group.draw(surface)
        self.chest_group.draw(surface)
        self.player_group.draw(surface)
        self._draw_minimap(surface)
        self.backpack_button.draw(surface)
        self.talents_button.draw(surface)
        
    def _draw_minimap(self, surface):
        minimap_rect = pygame.Rect(10, 10, 230, 230)
        pygame.draw.rect(surface, PANEL_BG_COLOR, minimap_rect); pygame.draw.rect(surface, PANEL_BORDER_COLOR, minimap_rect, 2)
        cell_size = 15
        for (x, y), room in self.floor.rooms.items():
            map_x, map_y = minimap_rect.x + x*cell_size + 5, minimap_rect.y + y*cell_size + 5
            cell_rect = pygame.Rect(map_x, map_y, cell_size - 1, cell_size - 1)
            base_color = NODE_STYLE.get(room.type, {"color": (255,255,255)})["color"]
            final_color = base_color
            if not room.is_cleared and room.type != "start":
                final_color = (base_color[0] // 2, base_color[1] // 2, base_color[2] // 2)
            pygame.draw.rect(surface, final_color, cell_rect)
            if room is self.current_room:
                p1 = (cell_rect.centerx, cell_rect.top + 3); p2 = (cell_rect.left + 3, cell_rect.bottom - 3); p3 = (cell_rect.right - 3, cell_rect.bottom - 3)
                pygame.draw.polygon(surface, (255, 255, 255, 200), [p1, p2, p3])