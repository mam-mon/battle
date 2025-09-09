# 文件: states/story.py (最终统一版本)

import pygame
import math
import random
from .base import BaseState
from .dungeon_screen import DungeonScreen
from .saving import SaveScreen
from .loading import LoadScreen
from .backpack import BackpackScreen
from .talents_screen import TalentsScreen
from ui import draw_text, ModernStoryButton, draw_text_with_emoji_fallback
from settings import *
from .attributes_screen import AttributesScreen

class StoryScreen(BaseState):
    """现代化剧情界面 - 具备动态效果和沉浸式体验"""
    
    HOTKEY_MAP = {
        pygame.K_s: "save", pygame.K_l: "load", 
        pygame.K_b: "backpack", pygame.K_t: "talents",
        pygame.K_c: "attributes"
    }
    
    def __init__(self, game):
        super().__init__(game)
        
        # 动画系统
        self.typewriter_cursor_blink = 0
        self.dialogue_box_glow = 0
        self.background_particles = []
        self.speaker_entrance_animation = 0
        self.button_hover_animations = {}
        self.text_shake = 0
        
        self._init_background_effects()
        self._init_ui()
        self._initialize_story()

    def _get_font(self, font_name, default_size=20):
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)

    def _init_background_effects(self):
        for _ in range(25):
            particle = {
                'x': random.uniform(0, SCREEN_WIDTH), 'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(1, 3), 'speed': random.uniform(0.1, 0.5),
                'alpha': random.uniform(20, 60), 'direction': random.uniform(0, 2 * math.pi),
                'phase': random.uniform(0, 2 * math.pi)
            }
            self.background_particles.append(particle)

    def _init_ui(self):
        self.buttons = self._create_buttons()
        for button_name in self.buttons:
            self.button_hover_animations[button_name] = 0

    def _create_buttons(self):
        buttons = {}
        button_w, button_h, padding, start_y = 140, 50, 15, SCREEN_HEIGHT - 400
        button_configs = [
            ("attributes", "属性 C", (255, 100, 100)), ("talents", "天赋 T", (139, 92, 246)),
            ("backpack", "背包 B", (59, 130, 246)), ("load", "加载 L", (245, 158, 11)),
            ("save", "保存 S", (16, 185, 129)), ("dungeon", "进入地牢", (200, 80, 80))
        ]
        for i, (key, text, color) in enumerate(button_configs):
            rect = pygame.Rect(SCREEN_WIDTH - padding - button_w, start_y + i * (button_h + padding), button_w, button_h)
            buttons[key] = ModernStoryButton(rect, text, self._get_font('small'), color)
        return buttons

    def _initialize_story(self):
        start_index = getattr(self.game, "loaded_dialogue_index", 0)
        self.dialogue_index = start_index
        self.displayed_chars = 0
        self.typing_complete = False
        self.last_char_time = 0
        self.typewriter_speed = 30
        self.game.loaded_dialogue_index = 0
        self.speaker_entrance_animation = 0

    def handle_event(self, event):
        if self._handle_button_events(event): return
        if self._handle_hotkey_events(event): return
        self._handle_dialogue_events(event)

    def _handle_button_events(self, event):
        action_map = {
            "save": lambda: self.game.state_stack.append(SaveScreen(self.game)),
            "load": lambda: self.game.state_stack.append(LoadScreen(self.game)),
            "backpack": lambda: self.game.state_stack.append(BackpackScreen(self.game)),
            "talents": lambda: self.game.state_stack.append(TalentsScreen(self.game)),
            "attributes": lambda: self.game.state_stack.append(AttributesScreen(self.game)),
            "dungeon": lambda: self.game.state_stack.append(DungeonScreen(self.game, "sunstone_ruins", 1))
        }
        for name, button in self.buttons.items():
            if button.handle_event(event) and name in action_map:
                action_map[name](); return True
        return False

    def _handle_hotkey_events(self, event):
        if event.type != pygame.KEYDOWN: return False
        if event.key in self.HOTKEY_MAP:
            action = self.HOTKEY_MAP[event.key]
            if action in self.buttons:
                # 模拟按钮点击动作
                self._handle_button_events(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=self.buttons[action].rect.center))
            return True
        return False

    def _handle_dialogue_events(self, event):
        should_advance = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not any(btn.rect.collidepoint(event.pos) for btn in self.buttons.values()):
                should_advance = True
        elif event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]:
            should_advance = True
        
        if should_advance: self._advance_dialogue()

    def update(self):
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): self._last_time = current_time
        dt_sec = (current_time - self._last_time) / 1000.0
        self._last_time = current_time
        
        self.typewriter_cursor_blink = (self.typewriter_cursor_blink + dt_sec * 3) % (2 * math.pi)
        self.dialogue_box_glow = (self.dialogue_box_glow + dt_sec * 2) % (2 * math.pi)
        self.speaker_entrance_animation = min(1.0, self.speaker_entrance_animation + dt_sec * 3)
        
        for p in self.background_particles:
            p['x'] += math.cos(p['direction']) * p['speed']; p['y'] += math.sin(p['direction']) * p['speed']
            p['alpha'] = 30 + 20 * math.sin(p['phase'] + current_time * 0.001)
            if p['x'] < 0: p['x'] = SCREEN_WIDTH
            elif p['x'] > SCREEN_WIDTH: p['x'] = 0
            if p['y'] < 0: p['y'] = SCREEN_HEIGHT  
            elif p['y'] > SCREEN_HEIGHT: p['y'] = 0
        
        mouse_pos = pygame.mouse.get_pos()
        for name, button in self.buttons.items():
            if button.rect.collidepoint(mouse_pos):
                self.button_hover_animations[name] = min(1.0, self.button_hover_animations[name] + dt_sec * 4)
            else:
                self.button_hover_animations[name] = max(0, self.button_hover_animations[name] - dt_sec * 3)
        
        self._update_typewriter(current_time)

    def _update_typewriter(self, current_time):
        if self.typing_complete or current_time - self.last_char_time <= self.typewriter_speed: return
        current_line = self._get_current_dialogue().get("line", "")
        if self.displayed_chars < len(current_line):
            self.displayed_chars += 1; self.last_char_time = current_time
        else:
            self.typing_complete = True

    def _advance_dialogue(self):
        if not self.typing_complete: self._complete_current_line(); return
        if self._handle_dialogue_action(): return
        self._next_dialogue()

    def _complete_current_line(self):
        self.displayed_chars = len(self._get_current_dialogue().get("line", "")); self.typing_complete = True

    def _handle_dialogue_action(self):
        if self._get_current_dialogue().get("action") == "start_trial":
            self.game.state_stack.pop(); self.game.state_stack.append(DungeonScreen(self.game, "sunstone_ruins", 1)); return True
        return False

    def _next_dialogue(self):
        current_dialogue = self._get_current_dialogue()
        dialogue_list = self.game.story_data.get(self.game.current_stage, {}).get("text", [])
        self.dialogue_index += 1
        if self.dialogue_index >= len(dialogue_list):
            self._handle_stage_end()
        else:
            self._reset_typewriter()
            if current_dialogue.get("speaker") != self._get_current_dialogue().get("speaker"):
                self.speaker_entrance_animation = 0

    def _handle_stage_end(self):
        from .combat import CombatScreen; from .title import TitleScreen
        stage_data = self.game.story_data.get(self.game.current_stage, {}); next_stage = stage_data.get("next", "quit")
        self.game.current_stage = next_stage
        if next_stage == "quit":
            self.game.state_stack = [TitleScreen(self.game)]; return
        next_stage_data = self.game.story_data.get(next_stage, {})
        if next_stage_data.get("type") == "combat":
            self.game.state_stack.pop(); self.game.state_stack.append(CombatScreen(self.game, next_stage_data.get("enemy_id", "slime")))
        else:
            self._initialize_story()

    def _reset_typewriter(self):
        self.displayed_chars = 0; self.typing_complete = False; self.last_char_time = 0

    def draw(self, surface):
        self._draw_dynamic_background(surface)
        self._draw_background_particles(surface)
        self._draw_modern_dialogue_box(surface)
        self._draw_modern_buttons(surface)

    def _draw_dynamic_background(self, surface):
        speaker = self._get_current_dialogue().get("speaker", "旁白")
        base_color = (25, 35, 70) if speaker == "你" else (20, 30, 50)
        for y in range(SCREEN_HEIGHT):
            p = y / SCREEN_HEIGHT
            r, g, b = int(base_color[0] + p*20), int(base_color[1] + p*15), int(base_color[2] + p*30)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _draw_background_particles(self, surface):
        for p in self.background_particles:
            color = (100, 150, 255, p['alpha'])
            p_surf = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, color, (p['size'], p['size']), p['size'])
            surface.blit(p_surf, (p['x']-p['size'], p['y']-p['size']))

    def _draw_modern_dialogue_box(self, surface):
        rect = pygame.Rect(50, SCREEN_HEIGHT - 250, SCREEN_WIDTH - 100, 200)
        glow_size = int(10 + 5 * math.sin(self.dialogue_box_glow)); glow_rect = rect.inflate(glow_size, glow_size)
        pygame.draw.rect(surface, (70, 80, 100, 50), glow_rect, border_radius=15)
        pygame.draw.rect(surface, (25, 30, 50, 230), rect, border_radius=12)
        pygame.draw.rect(surface, (70, 80, 100, 180), rect, 2, border_radius=12)
        
        dialogue = self._get_current_dialogue()
        if dialogue.get("speaker", "旁白") != "旁白":
            self._draw_speaker_name(surface, rect, dialogue["speaker"])
        self._draw_dialogue_text(surface, rect, dialogue.get("line", ""))
        if self.typing_complete: self._draw_continue_prompt(surface, rect)

    def _draw_speaker_name(self, surface, d_rect, speaker):
        font = self._get_font('normal'); surf = font.render(speaker, True, (255, 215, 0))
        end_y = d_rect.top - 35; current_y = d_rect.top + (end_y - d_rect.top) * self.speaker_entrance_animation
        p_rect = surf.get_rect(topleft=(d_rect.left + 30, current_y)); p_rect.inflate_ip(25, 12)
        p_surf = pygame.Surface(p_rect.size, pygame.SRCALPHA); p_surf.set_alpha(255 * self.speaker_entrance_animation)
        pygame.draw.rect(p_surf, (35, 40, 65, 200), p_surf.get_rect(), border_radius=8)
        pygame.draw.rect(p_surf, (100, 120, 150), p_surf.get_rect(), 2, border_radius=8)
        p_surf.blit(surf, (12, 6)); surface.blit(p_surf, p_rect.topleft)

    def _draw_dialogue_text(self, surface, d_rect, full_line):
        text_to_render = full_line[:self.displayed_chars]; text_rect = d_rect.inflate(-80, -80)
        cursor_pos = draw_text(surface, text_to_render, self._get_font('normal'), (220, 220, 220), text_rect, return_cursor_pos=True)
        
        if not self.typing_complete and cursor_pos:
            font = self._get_font('normal'); alpha = int(128 + 127 * math.sin(self.typewriter_cursor_blink))
            line_surf = pygame.Surface((2, font.get_height()), pygame.SRCALPHA)
            pygame.draw.line(line_surf, (255, 255, 255, alpha), (0, 0), (0, font.get_height() - 5), 2)
            surface.blit(line_surf, (cursor_pos[0] + 2, cursor_pos[1]))

    def _draw_continue_prompt(self, surface, d_rect):
        pulse = 5 * math.sin(self.dialogue_box_glow); p_pos = (d_rect.right-40, d_rect.bottom-35+pulse)
        points = [p_pos, (p_pos[0]-15, p_pos[1]-10), (p_pos[0]-15, p_pos[1]+10)]
        pygame.draw.polygon(surface, (255, 255, 255, 150 + abs(pulse)*10), points)

    def _draw_modern_buttons(self, surface):
        for name, button in self.buttons.items():
            button.draw(surface, self.button_hover_animations.get(name, 0))

    def _get_current_dialogue(self):
        dialogue_list = self.game.story_data.get(self.game.current_stage, {}).get("text", [{"speaker": "旁白", "line": "..."}])
        return dialogue_list[min(self.dialogue_index, len(dialogue_list) - 1)]