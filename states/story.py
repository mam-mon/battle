# 文件: states/story.py (完整替换)

import pygame
from .base import BaseState
from .dungeon_screen import DungeonScreen
from .saving import SaveScreen
from .loading import LoadScreen
from .backpack import BackpackScreen
from .talents_screen import TalentsScreen
from ui import draw_text, Button
from settings import *

class StoryScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        
        # --- 核心修改 1: 重新布局，为“天赋”按钮腾出空间 ---
        button_w, button_h = 120, 40
        padding = 15
        # 从右往左依次是 保存 -> 加载 -> 背包 -> 天赋
        save_rect = pygame.Rect(SCREEN_WIDTH - padding - button_w, SCREEN_HEIGHT - padding - button_h - 250, button_w, button_h)
        load_rect = pygame.Rect(save_rect.left - padding - button_w, save_rect.top, button_w, button_h)
        backpack_rect = pygame.Rect(load_rect.left - padding - button_w, load_rect.top, button_w, button_h)
        talents_rect = pygame.Rect(backpack_rect.left - padding - button_w, backpack_rect.top, button_w, button_h)
        
        self.buttons = {
            "save": Button(save_rect, "保存(S)", self.game.fonts['small']),
            "load": Button(load_rect, "加载(L)", self.game.fonts['small']),
            "backpack": Button(backpack_rect, "背包(B)", self.game.fonts['small']),
            "talents": Button(talents_rect, "天赋(T)", self.game.fonts['small']) # <-- 新增天赋按钮
        }
        self._initialize_story()

    def _initialize_story(self):
        start_index = getattr(self.game, "loaded_dialogue_index", 0)
        self.dialogue_index = start_index
        self.displayed_chars = 0
        self.typing_complete = False
        self.last_char_time = 0
        self.typewriter_speed = 30
        self.game.loaded_dialogue_index = 0

    def update(self):
        if not self.typing_complete:
            now = pygame.time.get_ticks()
            if now - self.last_char_time > self.typewriter_speed:
                stage_data = self.game.story_data.get(self.game.current_stage, {})
                dialogue_list = stage_data.get("text", [])
                if not dialogue_list or self.dialogue_index >= len(dialogue_list):
                    self.typing_complete = True
                    return
                line = dialogue_list[self.dialogue_index].get("line", "")
                if self.displayed_chars < len(line):
                    self.displayed_chars += 1
                    self.last_char_time = now
                else:
                    self.typing_complete = True
    
    def handle_event(self, event):
        # --- 核心修改 2: 增加对新按钮和快捷键的处理 ---
        if self.buttons['save'].handle_event(event):
            self.game.state_stack.append(SaveScreen(self.game))
            return
        if self.buttons['load'].handle_event(event):
            self.game.state_stack.append(LoadScreen(self.game))
            return
        if self.buttons['backpack'].handle_event(event):
            self.game.state_stack.append(BackpackScreen(self.game))
            return
        # <-- 新增：处理天赋按钮点击事件
        if self.buttons['talents'].handle_event(event):
            self.game.state_stack.append(TalentsScreen(self.game))
            return

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_over_button = any(btn.rect.collidepoint(event.pos) for btn in self.buttons.values())
            if not is_over_button:
                self._advance_dialogue()
        
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self._advance_dialogue()
            elif event.key == pygame.K_s:
                self.game.state_stack.append(SaveScreen(self.game))
            elif event.key == pygame.K_l:
                self.game.state_stack.append(LoadScreen(self.game))
            elif event.key == pygame.K_b:
                self.game.state_stack.append(BackpackScreen(self.game))
            # <-- 新增：处理天赋快捷键 'T'
            elif event.key == pygame.K_t:
                self.game.state_stack.append(TalentsScreen(self.game))

    def _advance_dialogue(self):
        from .combat import CombatScreen
        from .title import TitleScreen

        stage_data = self.game.story_data.get(self.game.current_stage)
        if not stage_data:
            self.game.state_stack = [TitleScreen(self.game)]
            return
            
        dialogue_list = stage_data.get("text", [])

        if not self.typing_complete:
            self.typing_complete = True
            if self.dialogue_index < len(dialogue_list):
                current_line = dialogue_list[self.dialogue_index].get("line", "")
                self.displayed_chars = len(current_line)
            return

        if self.dialogue_index < len(dialogue_list):
            current_dialogue = dialogue_list[self.dialogue_index]
            action = current_dialogue.get("action")
            if action == "start_trial":
                self.game.state_stack.pop()
                self.game.state_stack.append(DungeonScreen(self.game, "sunstone_ruins", 1))
                return

        self.dialogue_index += 1

        if self.dialogue_index >= len(dialogue_list):
            self.game.current_stage = stage_data.get("next", "quit")
            if self.game.current_stage == "quit":
                self.game.state_stack = [TitleScreen(self.game)]
                return
            
            next_stage_data = self.game.story_data.get(self.game.current_stage, {})
            if next_stage_data.get("type") == "combat":
                enemy_id = next_stage_data.get("enemy_id", "slime")
                self.game.state_stack.pop()
                self.game.state_stack.append(CombatScreen(self.game, enemy_id))
            else:
                self._initialize_story()
        else:
            self.displayed_chars = 0
            self.typing_complete = False
            self.last_char_time = 0

    def draw(self, surface):
        surface.fill(BG_COLOR)
        dialogue_box_rect = pygame.Rect(50, SCREEN_HEIGHT - 250, SCREEN_WIDTH - 100, 200)
        pygame.draw.rect(surface, PANEL_BG_COLOR, dialogue_box_rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER_COLOR, dialogue_box_rect, 3, border_radius=10)

        stage_data = self.game.story_data.get(self.game.current_stage, {})
        dialogue_list = stage_data.get("text", [{"speaker": "错误", "line": "未找到剧情文本"}])
        safe_index = min(self.dialogue_index, len(dialogue_list) - 1)
        dialogue = dialogue_list[safe_index]
        speaker, full_line = dialogue["speaker"], dialogue["line"]
        if speaker != "旁白":
            speaker_text_surf = self.game.fonts['normal'].render(speaker, True, TEXT_COLOR)
            speaker_panel_rect = speaker_text_surf.get_rect(topleft=(dialogue_box_rect.left + 30, dialogue_box_rect.top - 35))
            speaker_panel_rect.inflate_ip(20, 10)
            pygame.draw.rect(surface, PANEL_BG_COLOR, speaker_panel_rect, border_radius=5)
            pygame.draw.rect(surface, PANEL_BORDER_COLOR, speaker_panel_rect, 2, border_radius=5)
            surface.blit(speaker_text_surf, (speaker_panel_rect.x + 10, speaker_panel_rect.y + 5))
        text_to_render = full_line[:self.displayed_chars]
        text_rect = dialogue_box_rect.inflate(-40, -40)
        draw_text(surface, text_to_render, self.game.fonts['normal'], TEXT_COLOR, text_rect)
        if self.typing_complete:
            prompt_pos = (dialogue_box_rect.right - 40, dialogue_box_rect.bottom - 40)
            pygame.draw.polygon(surface, TEXT_COLOR, [prompt_pos, (prompt_pos[0] - 20, prompt_pos[1]), (prompt_pos[0] - 10, prompt_pos[1] - 15)])
        
        # 绘制所有按钮 (会自动包含新按钮，无需修改)
        for button in self.buttons.values():
            button.draw(surface)