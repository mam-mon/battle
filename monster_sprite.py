# monster_sprite.py (完整替换)
import pygame
import random
import math
from dungeon_generator import TILE_SIZE
from settings import *

class Monster(pygame.sprite.Sprite):
    def __init__(self, monster_data, room_rect): # <-- 构造函数现在需要知道它属于哪个房间
        super().__init__()
        self.enemy_id = monster_data['id']
        self.uid = monster_data['uid']
        
        # 将房间的边界矩形保存下来，作为它的“活动范围”
        self.home_room_rect = room_rect

        # 视觉设置
        self.image = pygame.Surface([30, 30])
        color = (255, 0, 0)
        if self.enemy_id == "slime": color = (100, 200, 100)
        elif self.enemy_id == "goblin": color = (200, 150, 50)
        elif self.enemy_id == "ruin_golem":
            self.image = pygame.Surface([60, 60])
            color = (150, 50, 200)
        self.image.fill(color)
        self.rect = self.image.get_rect(center=monster_data['pos'])

        # --- 全新的 AI 状态机 ---
        self.speed = 0.8 # <-- 降低移动速度
        self.ai_state = "idle" # 初始状态为“站立”
        self.ai_timer = random.uniform(1, 3) # 站立1-3秒
        self.target_pos = None # 移动的目标点

    def update(self, walls, dt): # <-- update 函数现在接收墙壁和时间增量 dt
        self.ai_timer -= dt

        # 1. 状态切换逻辑
        if self.ai_timer <= 0:
            if self.ai_state == "idle":
                # 从站立切换到徘徊
                self.ai_state = "wandering"
                self.ai_timer = random.uniform(2, 4) # 徘徊2-4秒
                # 在房间活动范围内随机选择一个目标点
                # 我们在房间边界内留出一些边距，防止怪物紧贴墙壁
                margin = TILE_SIZE 
                self.target_pos = (
                    random.randint(self.home_room_rect.left + margin, self.home_room_rect.right - margin),
                    random.randint(self.home_room_rect.top + margin, self.home_room_rect.bottom - margin)
                )
            elif self.ai_state == "wandering":
                # 从徘徊切换到站立
                self.ai_state = "idle"
                self.ai_timer = random.uniform(1, 3)
                self.target_pos = None

        # 2. 根据当前状态执行动作
        if self.ai_state == "wandering" and self.target_pos:
            # 计算朝向目标点的方向向量
            dx = self.target_pos[0] - self.rect.centerx
            dy = self.target_pos[1] - self.rect.centery
            dist = math.hypot(dx, dy)

            if dist > self.speed: # 如果没到终点
                # 单位化向量并乘以速度
                vx = (dx / dist) * self.speed
                vy = (dy / dist) * self.speed

                # 使用与玩家完全相同的碰撞逻辑
                # 水平移动和碰撞
                self.rect.x += vx
                for wall in pygame.sprite.spritecollide(self, walls, False):
                    if vx > 0: self.rect.right = wall.rect.left
                    if vx < 0: self.rect.left = wall.rect.right
                # 垂直移动和碰撞
                self.rect.y += vy
                for wall in pygame.sprite.spritecollide(self, walls, False):
                    if vy > 0: self.rect.bottom = wall.rect.top
                    if vy < 0: self.rect.top = wall.rect.bottom
        
        # 3. 房间范围限制 (最关键的一步)
        # 无论如何移动，都强制将怪物的位置限制在它的 home_room_rect 内部
        self.rect.clamp_ip(self.home_room_rect)