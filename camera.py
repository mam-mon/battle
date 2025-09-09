# camera.py
import pygame
from settings import *

class Camera:
    """一个专门用于处理镜头滚动的类。"""
    def __init__(self, width, height):
        self.camera_rect = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity_rect):
        """将一个世界坐标的矩形(rect)转换为相对于摄像机的屏幕坐标。"""
        return entity_rect.move(self.camera_rect.topleft)

    def update(self, target_entity):
        """让摄像机平滑地跟随目标（通常是玩家）。"""
        x = -target_entity.rect.centerx + int(DUNGEON_VIEW_WIDTH / 2)
        y = -target_entity.rect.centery + int(DUNGEON_VIEW_HEIGHT / 2)
        self.camera_rect.topleft = (x, y)