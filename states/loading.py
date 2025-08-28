# states/loading.py
import pygame
import time
from states.base import BaseState
from ui import draw_text, Button
from settings import *

class LoadScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.back_button = Button((SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT - 100, 300, 60), "返回", self.game.fonts['normal'])
        self.slot_rects = [pygame.Rect(100, 120 + i * 50, SCREEN_WIDTH - 200, 50) for i in range(10)]
        self.load_fail_message = None

    def handle_event(self, event):
        if self.back_button.handle_event(event):
            self.game.state_stack.pop() # 弹出当前状态，返回上一层
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self.slot_rects):
                if rect.collidepoint(event.pos):
                    if self.game.load_from_slot(i):
                        from states.story import StoryScreen
                        # 加载成功，清空栈并进入新游戏
                        self.game.state_stack = [StoryScreen(self.game)]
                    else:
                        self.load_fail_message = f"槽位 {i} 为空或损坏！"
                    return

    def draw(self, surface):
        surface.fill(BG_COLOR)
        draw_text(surface, "选择要加载的存档", self.game.fonts['large'], TEXT_COLOR, pygame.Rect(0, 50, SCREEN_WIDTH, 100))

        for i, rect in enumerate(self.slot_rects):
            slot_data = self.game.load_from_slot(i) # 使用 game 实例的方法
            is_hovered = rect.collidepoint(pygame.mouse.get_pos())
            if is_hovered:
                pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect.inflate(10, 10), 2, border_radius=5)
            
            text = f"{i}. " + ("(自动)" if i == 0 else "")
            if slot_data and slot_data.get("player"):
                player = slot_data["player"]
                save_time = time.strftime('%Y-%m-%d %H:%M', time.localtime(slot_data.get("timestamp", 0)))
                text += f"{player.name} - 等级 {player.level} ({save_time})"
            else:
                text += "-- 空 --"
            draw_text(surface, text, self.game.fonts['normal'], TEXT_COLOR, rect)

        if self.load_fail_message:
            fail_rect = pygame.Rect(0, SCREEN_HEIGHT - 150, SCREEN_WIDTH, 40)
            draw_text(surface, self.load_fail_message, self.game.fonts['normal'], (255, 100, 100), fail_rect)

        self.back_button.draw(surface)