# treasure_sprite.py
import pygame
from settings import *

class TreasureChest(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # 将来你可以换成漂亮的宝箱图片
        # 现在我们用一个金色的方块代替
        self.image = pygame.Surface([60, 50])
        self.image.fill((255, 215, 0)) # 金色
        self.rect = self.image.get_rect(center=(x, y))