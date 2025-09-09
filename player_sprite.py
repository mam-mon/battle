# player_sprite.py
import pygame
from settings import *

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([40, 40])
        self.image.fill(TEXT_COLOR) # 暂时用一个白色方块代表玩家
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = 5

    # player_sprite.py
    # ... (__init__ 不变) ...
    def update(self, impassable_sprites): # <-- 参数名从 walls 改为 impassable_sprites
        """根据按键更新玩家位置，并处理与不可通行精灵的碰撞。"""
        keys = pygame.key.get_pressed()
        
        # 水平移动
        vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: vx = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: vx = self.speed
        if vx != 0:
            self.rect.x += vx
            # 用新的参数名 impassable_sprites 进行碰撞检测
            for sprite in pygame.sprite.spritecollide(self, impassable_sprites, False):
                if vx > 0: self.rect.right = sprite.rect.left
                if vx < 0: self.rect.left = sprite.rect.right
        
        # 垂直移动
        vy = 0
        if keys[pygame.K_UP] or keys[pygame.K_w]: vy = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: vy = self.speed
        if vy != 0:
            self.rect.y += vy
            # 用新的参数名 impassable_sprites 进行碰撞检测
            for sprite in pygame.sprite.spritecollide(self, impassable_sprites, False):
                if vy > 0: self.rect.bottom = sprite.rect.top
                if vy < 0: self.rect.top = sprite.rect.bottom