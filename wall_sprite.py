# wall_sprite.py
import pygame
from settings import *

class Wall(pygame.sprite.Sprite):
    """A simple wall sprite for physical collision."""
    def __init__(self, x, y, width, height):
        super().__init__()
        # We're going back to drawing a solid color rectangle
        self.image = pygame.Surface([width, height])
        self.image.fill((50, 60, 80)) # The color for the walls
        self.rect = self.image.get_rect(topleft=(x, y))