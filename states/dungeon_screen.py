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

NODE_STYLE = {"start": {"color": (100, 255, 100)},"combat": {"color": (200, 200, 200)}, "event": {"color": (255, 255, 100)},"treasure": {"color": (255, 215, 0)},"elite": {"color": (255, 50, 50)},"boss": {"color": (160, 32, 240)},"rest": {"color": (100, 200, 255)},"shop": {"color": (100, 255, 200)},"forge": {"color": (150, 150, 150)}}

class DungeonScreen(BaseState):
    # 在 states/dungeon_screen.py 文件中

    def __init__(self, game):
        super().__init__(game)
        self.floor = Floor()
        # <-- 核心修改：确保这里请求的房间数是你想要的（10个以内） -->
        self.floor.generate_floor(num_rooms=8) 
        
        self.player = Player(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.player_group = pygame.sprite.GroupSingle(self.player)
        self.monster_group = pygame.sprite.Group()
        self.chest_group = pygame.sprite.GroupSingle()
        self.door_rects, self.exit_portal_button = {}, None
        self.current_room = self.floor.start_room
        self._enter_room(self.current_room)
        
        backpack_button_rect = pygame.Rect(SCREEN_WIDTH - 160, 10, 140, 50)
        self.backpack_button = Button(backpack_button_rect, "背包 (B)", self.game.fonts['small'])

    def _enter_room(self, room):
        self.current_room = room
        if not (self.current_room.type == 'boss' and self.current_room.is_cleared):
            self.exit_portal_button = None
        print(f"进入房间 ({room.x}, {room.y}), 类型: {room.type}")

        # --- 核心改动：根据房间类型执行不同逻辑 ---
        room_type = self.current_room.type
        is_cleared = self.current_room.is_cleared

        # 只有未清理过的特殊房间才会触发事件
        if not is_cleared:
            if room_type == "event":
                from .event_screen import EventScreen
                event_id = random.choice(list(self.game.event_data.keys()))
                self.game.state_stack.append(EventScreen(self.game, event_id, self.current_room))
            elif room_type == "shop":
                from .shop_screen import ShopScreen
                self.game.state_stack.append(ShopScreen(self.game, self.current_room))

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
        """打开宝箱，并根据品质概率生成两个选项"""
        print("打开宝-箱！")
        
        # 1. 定义品质掉落权重
        rarity_weights = {
            "common": 65,
            "uncommon": 25,
            "rare": 8,
            "epic": 2,
            "legendary": 0.5,
            "mythic": 0.1
        }
        
        # 2. 创建一个所有装备的“数据库”，按品质分类
        item_pool = {rarity: [] for rarity in rarity_weights.keys()}
        all_item_classes = [getattr(Equips, name) for name in dir(Equips) if 
                            isinstance(getattr(Equips, name), type) and 
                            issubclass(getattr(Equips, name), Equips.Equipment) and 
                            getattr(Equips, name) is not Equips.Equipment]
        
        for item_class in all_item_classes:
            # 实例化一个临时对象来获取它的品质
            temp_item = item_class()
            if hasattr(temp_item, 'rarity') and temp_item.rarity in item_pool:
                item_pool[temp_item.rarity].append(item_class)

        # 3. 根据权重，随机选择两个品质
        rarities_to_spawn = random.choices(
            list(rarity_weights.keys()), 
            weights=list(rarity_weights.values()), 
            k=2 # 随机选两次
        )

        # 4. 从对应品质的池子里，随机挑选物品
        choices = []
        for rarity in rarities_to_spawn:
            # 如果该品质的池子不为空，就从中选一个
            if item_pool[rarity]:
                item_class = random.choice(item_pool[rarity])
                choices.append(item_class())

        # 确保我们至少有一个选项，并避免两个选项完全一样
        if not choices: print("错误: 物品池为空！"); return
        while len(choices) < 2:
            # 如果只生成了一个，就再补一个普通的
            if item_pool["common"]:
                choices.append(random.choice(item_pool["common"])())
            else: # 如果连普通都没有，就复制第一个
                choices.append(choices[0].__class__())

        # 5. 弹出选择界面
        from .choice_screen import ChoiceScreen
        self.game.state_stack.append(ChoiceScreen(self.game, choices, self.current_room))
        
        chest_sprite.kill()

    def handle_event(self, event):
        from .backpack import BackpackScreen
        if self.backpack_button.handle_event(event) or \
           (event.type == pygame.KEYDOWN and event.key == pygame.K_b):
            self.game.state_stack.append(BackpackScreen(self.game)); return
            
        if self.exit_portal_button and self.exit_portal_button.handle_event(event):
            print("进入下一层！"); self.__init__(self.game); return
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            chest = self.chest_group.sprite
            if chest and chest.rect.collidepoint(event.pos):
                self._open_treasure_chest(chest)

    def on_monster_defeated(self, defeated_monster_uid):
        self.current_room.monsters = [m for m in self.current_room.monsters if m['uid'] != defeated_monster_uid]
        self._sync_sprites()
        if not self.current_room.monsters:
            self.current_room.is_cleared = True; self.door_rects = self._generate_doors()
            if self.current_room.type == "boss":
                portal_rect = pygame.Rect(0,0,200,80); portal_rect.center = (SCREEN_WIDTH/2, SCREEN_HEIGHT/2)
                self.exit_portal_button = Button(portal_rect, "前往下一层", self.game.fonts['normal'])

    def update(self):
        self.player_group.update()
        if not self.current_room.is_cleared:
            self.monster_group.update()
            collided_monster = pygame.sprite.spritecollideany(self.player, self.monster_group)
            if collided_monster:
                from .combat import CombatScreen
                self.game.state_stack.append(CombatScreen(self.game, collided_monster.enemy_id, collided_monster.uid))
                self.monster_group.empty(); return
        else:
            for direction, door_rect in self.door_rects.items():
                if self.player.rect.colliderect(door_rect):
                    self._change_room(direction); break
    
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

    def draw(self, surface):
        surface.fill(BG_COLOR)
        for door_rect in self.door_rects.values(): pygame.draw.rect(surface, (100, 200, 100), door_rect)
        if self.exit_portal_button: self.exit_portal_button.draw(surface)
        self.monster_group.draw(surface); self.chest_group.draw(surface)
        self.player_group.draw(surface)
        self._draw_minimap(surface); self.backpack_button.draw(surface)
        
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