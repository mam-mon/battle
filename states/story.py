# states/story.py
import pygame
from states.base import BaseState
from states.saving import SaveScreen
from states.loading import LoadScreen
from states.combat import CombatScreen
from ui import draw_text
from settings import *

class StoryScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.dialogue_buttons = {
            "save": pygame.Rect(SCREEN_WIDTH - 130, SCREEN_HEIGHT - 45, 120, 35),
            "load": pygame.Rect(SCREEN_WIDTH - 260, SCREEN_HEIGHT - 45, 120, 35)
        }
        self._initialize_story()

    def _initialize_story(self):
        start_index = getattr(self.game, "loaded_dialogue_index", 0)
        self.dialogue_index = start_index
        self.displayed_chars = 0
        self.typing_complete = False
        self.last_char_time = 0
        self.typewriter_speed = 30
        self.game.loaded_dialogue_index = 0 # 用完后重置

    def update(self):
        if not self.typing_complete:
            now = pygame.time.get_ticks()
            if now - self.last_char_time > self.typewriter_speed:
                stage_data = self.game.story_data.get(self.game.current_stage, {})
                line = stage_data.get("text", [{}])[self.dialogue_index].get("line", "")
                if self.displayed_chars < len(line):
                    self.displayed_chars += 1
                    self.last_char_time = now
                else:
                    self.typing_complete = True

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos
            if self.dialogue_buttons["save"].collidepoint(mouse_pos):
                self.game.state_stack.append(SaveScreen(self.game))
                return
            if self.dialogue_buttons["load"].collidepoint(mouse_pos):
                self.game.state_stack.append(LoadScreen(self.game))
                return
            self._advance_dialogue()
        
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self._advance_dialogue()
            elif event.key == pygame.K_s:
                self.game.state_stack.append(SaveScreen(self.game))
            elif event.key == pygame.K_l:
                self.game.state_stack.append(LoadScreen(self.game))
    
    def _advance_dialogue(self):
        if not self.typing_complete:
            self.typing_complete = True
            stage_data = self.game.story_data.get(self.game.current_stage, {})
            line = stage_data.get("text", [{}])[self.dialogue_index].get("line", "")
            self.displayed_chars = len(line)
        else:
            self.dialogue_index += 1
            stage_data = self.game.story_data[self.game.current_stage]
            if self.dialogue_index >= len(stage_data.get("text", [])):
                self.game.current_stage = stage_data["next"]
                if self.game.current_stage == "quit":
                    self.game.running = False
                    return
                next_stage_data = self.game.story_data.get(self.game.current_stage, {})
                if next_stage_data.get("type") == "combat":
                    self.game.state_stack.pop()
                    self.game.state_stack.append(CombatScreen(self.game))
                else:
                    self._initialize_story()
            else:
                self.displayed_chars = 0
                self.typing_complete = False
                self.last_char_time = 0

    def draw(self, surface):
        surface.fill(BG_COLOR) # 清屏
        dialogue_box_rect = pygame.Rect(50, SCREEN_HEIGHT - 250, SCREEN_WIDTH - 100, 200)
        pygame.draw.rect(surface, PANEL_BG_COLOR, dialogue_box_rect, border_radius=10)
        pygame.draw.rect(surface, PANEL_BORDER_COLOR, dialogue_box_rect, 3, border_radius=10)

        stage_data = self.game.story_data.get(self.game.current_stage, {})
        dialogue = stage_data.get("text", [{"speaker": "错误", "line": "未找到剧情文本"}])[self.dialogue_index]
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
        
        mouse_pos = pygame.mouse.get_pos()
        for name, rect in self.dialogue_buttons.items():
            is_hovered = rect.collidepoint(mouse_pos)
            text = "保存 (S)" if name == "save" else "加载 (L)"
            if is_hovered:
                pygame.draw.line(surface, PANEL_BORDER_COLOR, (rect.left, rect.bottom), (rect.right, rect.bottom), 2)
            draw_text(surface, text, self.game.fonts['small'], TEXT_COLOR, rect)