# door_sprite.py (完整替换)
import pygame
from settings import *

class Door(pygame.sprite.Sprite):
    """一个可以开关的门精灵。"""
    def __init__(self, x, y, width, height, impassable_group):
        super().__init__()
        
        self.impassable_group = impassable_group

        # "关门"状态的图片 (一个看得见的色块)
        self.closed_image = pygame.Surface([width, height])
        self.closed_image.fill((139, 69, 19)) # 木门颜色
        
        ### --- 核心修改：将“开门”状态的图片设为完全透明 --- ###
        # 1. 创建一个支持透明通道的 Surface
        self.open_image = pygame.Surface([width, height], pygame.SRCALPHA)
        # 2. 默认就是全透明的，我们不需要再 fill 任何颜色

        self.image = self.open_image # 默认是打开的 (透明的)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.is_closed = False

    def close(self):
        """关门，并将其加入到不可通行的碰撞组中。"""
        if not self.is_closed:
            self.image = self.closed_image
            self.impassable_group.add(self)
            self.is_closed = True

    def open(self):
        """开门，并将其从不可通行的碰撞组中移除。"""
        if self.is_closed:
            self.image = self.open_image # 切换回透明图片
            self.impassable_group.remove(self)
            self.is_closed = False