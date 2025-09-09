# dungeon_generator.py (完整替换)

import random
import pygame
from settings import *
from wall_sprite import Wall
from door_sprite import Door

# 定义常量
WALL_THICKNESS = 15
TILE_SIZE = 50
ROOM_GRID_WIDTH = 17
ROOM_GRID_HEIGHT = 11
ROOM_PIXEL_WIDTH = TILE_SIZE * ROOM_GRID_WIDTH
ROOM_PIXEL_HEIGHT = TILE_SIZE * ROOM_GRID_HEIGHT

class Room:
    """逻辑房间单元"""
    def __init__(self, x, y, room_type="combat", is_corridor=False):
        self.x, self.y, self.type = x, y, room_type
        self.is_corridor = is_corridor
        self.doors = {"N": False, "S": False, "E": False, "W": False}
        self.is_cleared = False
        self.monsters = []
        self.world_rect = pygame.Rect(
            x * ROOM_PIXEL_WIDTH, y * ROOM_PIXEL_HEIGHT,
            ROOM_PIXEL_WIDTH, ROOM_PIXEL_HEIGHT
        )

def generate_new_dungeon_floor(num_rooms=8, floor_data=None, impassable_group_for_doors=None):
    """一个完整的、带走廊的地牢生成函数。"""
    # === 第1步: 生成房间和走廊的逻辑布局 ===
    grid_width, grid_height = 42, 42
    grid = [[None for _ in range(grid_width)] for _ in range(grid_height)]
    logical_rooms = {}
    sx, sy = grid_width // 2, grid_height // 2
    if sx % 2 != 0: sx -=1
    if sy % 2 != 0: sy -=1
    start_room = Room(sx, sy, "start")
    start_room.is_cleared = True
    grid[sy][sx] = start_room
    logical_rooms[(sx, sy)] = start_room
    room_coords = [(sx, sy)]
    while len(room_coords) < num_rooms and room_coords:
        px, py = random.choice(room_coords)
        directions = [(0, -2, "N", "S"), (0, 2, "S", "N"), (2, 0, "E", "W"), (-2, 0, "W", "E")]
        random.shuffle(directions)
        for dx, dy, door, opposite_door in directions:
            nx, ny = px + dx, py + dy
            if 0 <= nx < grid_width and 0 <= ny < grid_height and not grid[ny][nx]:
                new_room = Room(nx, ny)
                grid[ny][nx] = new_room
                logical_rooms[(nx, ny)] = new_room
                room_coords.append((nx, ny))
                corridor_x, corridor_y = px + dx // 2, py + dy // 2
                corridor = Room(corridor_x, corridor_y, "combat", is_corridor=True)
                corridor.is_cleared = True
                grid[corridor_y][corridor_x] = corridor
                logical_rooms[(corridor_x, corridor_y)] = corridor
                grid[py][px].doors[door] = True
                corridor.doors[opposite_door] = True
                corridor.doors[door] = True
                new_room.doors[opposite_door] = True
                break
        else:
            room_coords.remove((px, py))

    # === 第2步: 为"真正的"房间分配类型 ===
    main_rooms = [r for r in logical_rooms.values() if not r.is_corridor]
    farthest_dist, boss_room = -1, start_room
    for room in main_rooms:
        dist = abs(room.x - sx) + abs(room.y - sy)
        if dist > farthest_dist and room is not start_room:
            farthest_dist, boss_room = dist, room
    boss_room.type = "boss"
    special_room_candidates = [r for r in main_rooms if r.type == "combat"]
    room_types_to_assign = ["event", "treasure", "shop", "rest", "elite"]
    for room_type in room_types_to_assign:
        if special_room_candidates:
            candidate = random.choice(special_room_candidates)
            candidate.type = room_type
            special_room_candidates.remove(candidate)
    
    ### --- 关键修复：恢复并集成怪物数据生成逻辑 --- ###
    # === 第3步: 填充房间内容 (怪物等) ===
    m_uid_counter = 0
    for room in main_rooms:
        if room.type in ["combat", "elite", "boss"]:
            num, e_id = 1, "slime" # 默认生成1个史莱姆
            
            # 只有在 floor_data 存在时，才尝试读取更高级的怪物
            if floor_data:
                if room.type == "boss":
                    num = 1
                    e_id = floor_data.get("boss_id", "ruin_golem")
                elif room.type == "elite":
                    num = random.randint(2, 3)
                    if floor_data.get("elite_pool"): e_id = random.choice(floor_data["elite_pool"])
                else: # 普通战斗房间
                    num = random.randint(1, 3)
                    if floor_data.get("monster_pool"): e_id = random.choice(floor_data["monster_pool"])
            
            for _ in range(num):
                px = random.randint(room.world_rect.left + TILE_SIZE*2, room.world_rect.right - TILE_SIZE*2)
                py = random.randint(room.world_rect.top + TILE_SIZE*2, room.world_rect.bottom - TILE_SIZE*2)
                room.monsters.append({'id': e_id, 'pos': (px, py), 'uid': f'm_{m_uid_counter}'})
                m_uid_counter += 1
    ### --- 修复结束 --- ###

    # === 第4步: 根据所有布局创建实体精灵 ===
    all_sprites = pygame.sprite.Group()
    wall_sprites = pygame.sprite.Group()
    door_sprites = pygame.sprite.Group()
    CORRIDOR_WIDTH = TILE_SIZE * 3

    for room in logical_rooms.values():
        if room.is_corridor:
            is_horizontal = room.doors["E"] and room.doors["W"]
            if is_horizontal:
                floor_rect = pygame.Rect(room.world_rect.left, room.world_rect.centery - CORRIDOR_WIDTH // 2, room.world_rect.width, CORRIDOR_WIDTH)
                wall_sprites.add(Wall(floor_rect.left, floor_rect.top - WALL_THICKNESS, floor_rect.width, WALL_THICKNESS))
                wall_sprites.add(Wall(floor_rect.left, floor_rect.bottom, floor_rect.width, WALL_THICKNESS))
            else:
                floor_rect = pygame.Rect(room.world_rect.centerx - CORRIDOR_WIDTH // 2, room.world_rect.top, CORRIDOR_WIDTH, room.world_rect.height)
                wall_sprites.add(Wall(floor_rect.left - WALL_THICKNESS, floor_rect.top, WALL_THICKNESS, floor_rect.height))
                wall_sprites.add(Wall(floor_rect.right, floor_rect.top, WALL_THICKNESS, floor_rect.height))
            floor_sprite = pygame.sprite.Sprite()
            floor_sprite.image = pygame.Surface(floor_rect.size)
            floor_sprite.image.fill((25, 30, 45))
            floor_sprite.rect = floor_rect.copy()
            all_sprites.add(floor_sprite)
        else:
            floor_sprite = pygame.sprite.Sprite()
            floor_sprite.image = pygame.Surface(room.world_rect.size)
            floor_sprite.image.fill((30, 35, 50))
            floor_sprite.rect = room.world_rect.copy()
            all_sprites.add(floor_sprite)
            door_size = TILE_SIZE * 3
            # ... (墙壁和门的生成逻辑保持不变) ...
            if not room.doors["N"]:
                wall_sprites.add(Wall(room.world_rect.left, room.world_rect.top, room.world_rect.width, WALL_THICKNESS))
            else:
                door_sprites.add(Door(room.world_rect.centerx - door_size/2, room.world_rect.top, door_size, WALL_THICKNESS, impassable_group_for_doors))
                wall_sprites.add(Wall(room.world_rect.left, room.world_rect.top, room.world_rect.width/2 - door_size/2, WALL_THICKNESS))
                wall_sprites.add(Wall(room.world_rect.centerx + door_size/2, room.world_rect.top, room.world_rect.width/2 - door_size/2, WALL_THICKNESS))
            if not room.doors["S"]:
                wall_sprites.add(Wall(room.world_rect.left, room.world_rect.bottom - WALL_THICKNESS, room.world_rect.width, WALL_THICKNESS))
            else:
                door_sprites.add(Door(room.world_rect.centerx - door_size/2, room.world_rect.bottom - WALL_THICKNESS, door_size, WALL_THICKNESS, impassable_group_for_doors))
                wall_sprites.add(Wall(room.world_rect.left, room.world_rect.bottom - WALL_THICKNESS, room.world_rect.width/2 - door_size/2, WALL_THICKNESS))
                wall_sprites.add(Wall(room.world_rect.centerx + door_size/2, room.world_rect.bottom - WALL_THICKNESS, room.world_rect.width/2 - door_size/2, WALL_THICKNESS))
            if not room.doors["W"]:
                wall_sprites.add(Wall(room.world_rect.left, room.world_rect.top, WALL_THICKNESS, room.world_rect.height))
            else:
                door_sprites.add(Door(room.world_rect.left, room.world_rect.centery - door_size/2, WALL_THICKNESS, door_size, impassable_group_for_doors))
                wall_sprites.add(Wall(room.world_rect.left, room.world_rect.top, WALL_THICKNESS, room.world_rect.height/2 - door_size/2))
                wall_sprites.add(Wall(room.world_rect.left, room.world_rect.centery + door_size/2, WALL_THICKNESS, room.world_rect.height/2 - door_size/2))
            if not room.doors["E"]:
                wall_sprites.add(Wall(room.world_rect.right - WALL_THICKNESS, room.world_rect.top, WALL_THICKNESS, room.world_rect.height))
            else:
                door_sprites.add(Door(room.world_rect.right - WALL_THICKNESS, room.world_rect.centery - door_size/2, WALL_THICKNESS, door_size, impassable_group_for_doors))
                wall_sprites.add(Wall(room.world_rect.right - WALL_THICKNESS, room.world_rect.top, WALL_THICKNESS, room.world_rect.height/2 - door_size/2))
                wall_sprites.add(Wall(room.world_rect.right - WALL_THICKNESS, room.world_rect.centery + door_size/2, WALL_THICKNESS, room.world_rect.height/2 - door_size/2))
            
    all_sprites.add(wall_sprites, door_sprites)
    return all_sprites, wall_sprites, door_sprites, list(logical_rooms.values()), start_room