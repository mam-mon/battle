# states/saving.py
import pygame
import time
from states.base import BaseState
from ui import draw_text, Button
from settings import *

class SaveScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.back_button = Button((SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT - 100, 300, 60), "返回", self.game.fonts['normal'])
        self.slot_rects = [pygame.Rect(100, 120 + (i-1) * 50, SCREEN_WIDTH - 200, 50) for i in range(1, 10)]
        self.feedback_message = None
        self.feedback_timer = 0

    def update(self):
        if self.feedback_message and pygame.time.get_ticks() - self.feedback_timer > 2000:
            self.feedback_message = None

    def handle_event(self, event):
        if self.back_button.handle_event(event):
            self.game.state_stack.pop()
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.slot_rects, 1):
                if rect.collidepoint(event.pos):
                    self.feedback_message = self.game.save_to_slot(i)
                    self.feedback_timer = pygame.time.get_ticks()
                    return

    def draw(self, surface):
        surface.fill(BG_COLOR)
        draw_text(surface, "选择要覆盖的存档槽", self.game.fonts['large'], TEXT_COLOR, pygame.Rect(0, 50, SCREEN_WIDTH, 100))

        for i, rect in enumerate(self.slot_rects, 1):
            slot_data = self.game.load_from_slot(i)
            is_hovered = rect.collidepoint(pygame.mouse.get_pos())
            if is_hovered:
                pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect.inflate(10, 10), 2, border_radius=5)
            
            text = f"{i}. "
            if slot_data and slot_data.get("player"):
                player = slot_data["player"]
                save_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(slot_data.get("timestamp", 0)))
                text += f"{player.name} - 等级 {player.level} ({save_time})"
            else:
                text += "-- 空 --"
            draw_text(surface, text, self.game.fonts['normal'], TEXT_COLOR, rect)

        if self.feedback_message:
            feedback_rect = pygame.Rect(0, SCREEN_HEIGHT - 150, SCREEN_WIDTH, 40)
            draw_text(surface, self.feedback_message, self.game.fonts['normal'], (100, 255, 100), feedback_rect)
        
        self.back_button.draw(surface)