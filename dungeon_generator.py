# 文件: dungeon_generator.py (完整替换)

import random
from settings import SCREEN_WIDTH, SCREEN_HEIGHT

class Room:
    def __init__(self, x, y, room_type="combat"):
        self.x, self.y, self.type = x, y, room_type
        self.doors = {"N": False, "S": False, "E": False, "W": False}
        self.is_cleared = False
        self.monsters = []
        # 你还可以添加 event_id, treasure_contents 等字段

class Floor:
    def __init__(self, width=21, height=21):
        self.width, self.height = width, height
        self.rooms, self.start_room, self.boss_room = {}, None, None

    def generate_floor(self, num_rooms=8, floor_data=None):
        """
        使用传入的 floor_data 动态生成楼层内容
        """
        self.rooms.clear()
        grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        
        # 1. 创建房间布局 (这部分逻辑不变)
        sx, sy = self.width // 2, self.height // 2
        start_room = Room(sx, sy, "start")
        start_room.is_cleared = True
        grid[sy][sx] = start_room
        self.rooms[(sx, sy)] = start_room
        
        frontier = [(sx, sy)]
        
        while len(self.rooms) < num_rooms and frontier:
            px, py = random.choice(frontier)
            possible_neighbors = []
            directions = [(0, -1, "N", "S"), (0, 1, "S", "N"), (1, 0, "E", "W"), (-1, 0, "W", "E")]
            for dx, dy, door, opposite_door in directions:
                nx, ny = px + dx, py + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and not grid[ny][nx]:
                    possible_neighbors.append((nx, ny, door, opposite_door))
            
            if possible_neighbors:
                nx, ny, door, opposite_door = random.choice(possible_neighbors)
                new_room = Room(nx, ny)
                grid[ny][nx] = new_room
                self.rooms[(nx, ny)] = new_room
                frontier.append((nx, ny))
                grid[py][px].doors[door] = True
                new_room.doors[opposite_door] = True
            else:
                frontier.remove((px, py))

        # --- 2. 核心修改：根据 floor_data 填充房间内容 ---
        if not floor_data:
            print("错误: 未提供楼层数据，无法填充内容！")
            return

        # 定位Boss房间 (逻辑不变)
        self.start_room = self.rooms[(sx, sy)]
        farthest_dist = -1
        boss_coord = (sx, sy)
        for coord in self.rooms.keys():
            dist = abs(coord[0] - sx) + abs(coord[1] - sy)
            if dist > farthest_dist and self.rooms[coord] is not self.start_room:
                farthest_dist = dist
                boss_coord = coord
        self.boss_room = self.rooms[boss_coord]
        self.boss_room.type = "boss"
        
        # 确定特殊房间类型和数量 (逻辑不变)
        room_type_pool = ["combat"] * 4 + ["event"] * 2 + ["treasure"]*2 + ["shop", "rest", "elite"]
        special_room_candidates = [r for r in self.rooms.values() if r.type == "combat"]
        for room_type in ["event", "treasure", "shop", "rest", "elite"]:
            if special_room_candidates:
                candidate = random.choice(special_room_candidates)
                candidate.type = room_type
                special_room_candidates.remove(candidate)

        # 动态填充怪物
        m_uid = 0
        for room in self.rooms.values():
            if room.type in ["combat", "elite", "boss"]:
                num = 1
                e_id = "slime" # 默认值

                if room.type == "boss":
                    num = 1
                    e_id = floor_data.get("boss_id", "ruin_golem")
                elif room.type == "elite":
                    num = random.randint(2, 3)
                    if floor_data.get("elite_pool"):
                        e_id = random.choice(floor_data["elite_pool"])
                else: # 普通战斗
                    num = random.randint(1, 3)
                    if floor_data.get("monster_pool"):
                        e_id = random.choice(floor_data["monster_pool"])
                
                for _ in range(num):
                    px, py = random.randint(100, SCREEN_WIDTH - 100), random.randint(100, SCREEN_HEIGHT - 100)
                    room.monsters.append({'id': e_id, 'pos': (px, py), 'uid': f'm_{m_uid}'})
                    m_uid += 1