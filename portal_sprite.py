# 文件: portal_sprite.py (新文件)

import pygame
from settings import *

class PortalSprite(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # 创建一个可视化的传送门外观
        self.image = pygame.Surface([120, 120], pygame.SRCALPHA)
        # 画一个紫色的外圈
        pygame.draw.circle(self.image, (160, 32, 240), (60, 60), 60)
        # 画一个深紫色的内圈
        pygame.draw.circle(self.image, (50, 10, 80), (60, 60), 50)
        self.rect = self.image.get_rect(center=(x, y))