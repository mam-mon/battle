# monster_sprite.py (已更新)
import pygame
from settings import *

class Monster(pygame.sprite.Sprite):
    def __init__(self, monster_data): # <-- 改为接收整个 data 字典
        super().__init__()
        self.enemy_id = monster_data['id']
        self.uid = monster_data['uid'] # <-- 新增：记录自己的 uid
        
        self.image = pygame.Surface([30, 30])
        color = (255, 0, 0)
        if self.enemy_id == "slime": color = (100, 200, 100)
        elif self.enemy_id == "goblin": color = (200, 150, 50)
        elif self.enemy_id == "ruin_golem": # Boss用大一点的方块和不同颜色
            self.image = pygame.Surface([60, 60])
            color = (150, 50, 200)
        
        self.image.fill(color)
        self.rect = self.image.get_rect(center=monster_data['pos'])

    def update(self):
        pass