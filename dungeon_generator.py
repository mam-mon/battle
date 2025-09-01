# dungeon_generator.py (最终修正版)
import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class Room:
    def __init__(self, x, y, room_type="combat"):
        self.x, self.y, self.type = x, y, room_type
        self.doors = {"N": False, "S": False, "E": False, "W": False}
        self.is_cleared = False
        self.monsters = []

class Floor:
    def __init__(self, width=21, height=21):
        self.width, self.height = width, height
        self.rooms, self.start_room, self.boss_room = {}, None, None

    def generate_floor(self, num_rooms=8): # <-- 默认房间数已改小
        """使用“可控生长”算法，严格控制房间总数"""
        self.rooms.clear()
        grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        # 1. 在中心创建起点
        sx, sy = self.width // 2, self.height // 2
        start_room = Room(sx, sy, "start")
        start_room.is_cleared = True
        grid[sy][sx] = start_room
        self.rooms[(sx, sy)] = start_room
        
        # frontier 存储所有可以向外扩展的房间坐标
        frontier = [(sx, sy)]
        
        # 2. 循环生长，直到达到目标房间数
        while len(self.rooms) < num_rooms and frontier:
            # 随机选择一个边界房间进行扩展
            px, py = random.choice(frontier)
            
            # 寻找该房间所有可用的邻居位置
            possible_neighbors = []
            directions = [(0, -1, "N", "S"), (0, 1, "S", "N"), (1, 0, "E", "W"), (-1, 0, "W", "E")]
            for dx, dy, door, opposite_door in directions:
                nx, ny = px + dx, py + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and not grid[ny][nx]:
                    possible_neighbors.append((nx, ny, door, opposite_door))
            
            if possible_neighbors:
                # 随机选择一个方向进行扩展
                nx, ny, door, opposite_door = random.choice(possible_neighbors)
                
                new_room = Room(nx, ny)
                grid[ny][nx] = new_room
                self.rooms[(nx, ny)] = new_room
                frontier.append((nx, ny)) # 新房间也成为新的边界
                
                # 连接门
                grid[py][px].doors[door] = True
                new_room.doors[opposite_door] = True
            else:
                # 如果一个房间的所有方向都无法扩展，就从边界中移除
                frontier.remove((px, py))

        # --- 后续处理流程不变 ---
        self.start_room = self.rooms[(sx, sy)]
        
        farthest_dist = -1
        boss_coord = (sx, sy)
        for coord in self.rooms.keys():
            dist = abs(coord[0] - sx) + abs(coord[1] - sy)
            if dist > farthest_dist and self.rooms[coord] is not self.start_room:
                farthest_dist = dist; boss_coord = coord
        self.boss_room = self.rooms[boss_coord]; self.boss_room.type = "boss"
        
        room_type_pool = ["combat"] * 4 + ["event"] * 2 + ["treasure"]*2 + ["shop", "rest", "elite"]
        special_room_candidates = [r for r in self.rooms.values() if r.type == "combat"]
        for room_type in ["event", "treasure", "shop", "rest", "elite"]:
            if special_room_candidates:
                candidate = random.choice(special_room_candidates)
                candidate.type = room_type
                special_room_candidates.remove(candidate)

        enemy_pool, m_uid = ["slime", "goblin"], 0
        for room in self.rooms.values():
            if room.type in ["combat", "elite", "boss"]:
                num, e_id = 1, "slime"
                if room.type == "boss": num, e_id = 1, "ruin_golem"
                elif room.type == "elite": num, e_id = random.randint(2,3), "goblin_captain"
                else: num, e_id = random.randint(1, 3), random.choice(enemy_pool)
                for _ in range(num):
                    px, py = random.randint(100, SCREEN_WIDTH - 100), random.randint(100, SCREEN_HEIGHT - 100)
                    room.monsters.append({'id': e_id, 'pos': (px, py), 'uid': f'm_{m_uid}'}); m_uid += 1