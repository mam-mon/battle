# 文件: states/title.py (现代化重写版本)

import pygame
import math
import random
from .base import BaseState
from .loading import LoadScreen
from .story import StoryScreen
from .sandbox_screen import SandboxScreen
from ui import Button, draw_text_with_emoji_fallback, draw_text_with_outline
from settings import *

class TitleScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        
        self.hover_animations = {}
        self.glow_animation = 0
        self.title_pulse = 0
        self.background_particles = []
        self.menu_entrance_animation = 0
        
        self._init_background_particles()
        self._setup_buttons()

    def _get_font(self, font_name, default_size=20):
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)

    def _init_background_particles(self):
        for _ in range(50):
            particle = {
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(1, 3),
                'speed': random.uniform(0.2, 0.8),
                'alpha': random.uniform(20, 80),
                'direction': random.uniform(0, 2 * math.pi)
            }
            self.background_particles.append(particle)

    def _setup_buttons(self):
        button_width, button_height = 350, 65
        button_spacing = 20
        start_y = SCREEN_HEIGHT // 2 -50
        
        button_configs = [
            ("new_game", "🎮 开始新游戏", (100, 255, 100)),
            ("continue_game", "📖 继续游戏", (100, 200, 255)),
            ("load_game", "💾 加载游戏", (255, 200, 100)),
            ("sandbox", "⚔️ 沙盒模式", (255, 100, 200))
        ]
        
        self.buttons = {}
        for i, (key, text, color) in enumerate(button_configs):
            y_pos = start_y + i * (button_height + button_spacing)
            button_rect = (SCREEN_WIDTH // 2 - button_width // 2, y_pos, button_width, button_height)
            button = ModernButton(button_rect, text, self._get_font('normal'), color)
            self.buttons[key] = button
            self.hover_animations[key] = 0

    def handle_event(self, event):
        if self.menu_entrance_animation < 1.0:
            return
            
        if self.buttons['new_game'].handle_event(event):
            self.game.start_new_game()
            self.game.state_stack.append(StoryScreen(self.game))

        elif self.buttons['continue_game'].handle_event(event):
            if self.game.load_from_slot(0):
                self.game.state_stack.append(StoryScreen(self.game))
            else:
                self.game.start_new_game()
                self.game.state_stack.append(StoryScreen(self.game))

        elif self.buttons['load_game'].handle_event(event):
            self.game.state_stack.append(LoadScreen(self.game))

        elif self.buttons['sandbox'].handle_event(event):
            self.game.state_stack.append(SandboxScreen(self.game))

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.game.running = False

    def update(self, dt=0):
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): 
            self._last_time = current_time
            
        dt_ms = current_time - self._last_time
        self._last_time = current_time
        dt_sec = dt_ms / 1000.0
        
        self.menu_entrance_animation = min(1.0, self.menu_entrance_animation + dt_sec * 1.5)
        self.title_pulse = (self.title_pulse + dt_sec * 2) % (2 * math.pi)
        self.glow_animation = (self.glow_animation + dt_sec * 3) % (2 * math.pi)
        
        for particle in self.background_particles:
            particle['x'] += math.cos(particle['direction']) * particle['speed']
            particle['y'] += math.sin(particle['direction']) * particle['speed']
            if particle['x'] < 0: particle['x'] = SCREEN_WIDTH
            elif particle['x'] > SCREEN_WIDTH: particle['x'] = 0
            if particle['y'] < 0: particle['y'] = SCREEN_HEIGHT
            elif particle['y'] > SCREEN_HEIGHT: particle['y'] = 0
        
        mouse_pos = pygame.mouse.get_pos()
        for key, button in self.buttons.items():
            if button.rect.collidepoint(mouse_pos):
                self.hover_animations[key] = min(1.0, self.hover_animations[key] + dt_sec * 4)
            else:
                self.hover_animations[key] = max(0, self.hover_animations[key] - dt_sec * 3)

    def draw(self, surface):
        self._draw_gradient_background(surface)
        self._draw_background_particles(surface)
        self._draw_title(surface)
        self._draw_subtitle(surface)
        self._draw_menu_buttons(surface)
        self.update()

    def _draw_gradient_background(self, surface):
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(20 + progress * 30)
            g = int(25 + progress * 20)
            b = int(50 + progress * 80)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _draw_background_particles(self, surface):
        for particle in self.background_particles:
            alpha = int(particle['alpha'] * (0.5 + 0.5 * math.sin(self.glow_animation + particle['x'] * 0.01)))
            color = (100, 150, 255, alpha)
            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, (particle['size'], particle['size']), particle['size'])
            surface.blit(particle_surface, (particle['x'] - particle['size'], particle['y'] - particle['size']))

    def _draw_title(self, surface):
            """绘制游戏标题（恢复为原始的无描边版本）"""
            title_y = 120 + math.sin(self.title_pulse) * 10
            
            # 主标题
            title_font = self._get_font('large', 64)
            title_text = "战斗传奇"
            
            # 标题阴影 [cite: 696]
            shadow_surface = title_font.render(title_text, True, (20, 20, 40))
            shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + 4, title_y + 4))
            surface.blit(shadow_surface, shadow_rect)
            
            # 主标题发光效果 [cite: 697]
            glow_intensity = int((math.sin(self.glow_animation) + 1) * 30 + 50)
            title_color = (255, min(255, 215 + glow_intensity), min(255, 100 + glow_intensity))
            title_surface = title_font.render(title_text, True, title_color)
            title_rect = title_surface.get_rect(center=(SCREEN_WIDTH // 2, title_y))
            
            # 标题外发光 [cite: 698]
            for offset in [(2, 0), (-2, 0), (0, 2), (0, -2), (2, 2), (-2, -2), (2, -2), (-2, 2)]:
                glow_rect = title_rect.move(offset[0], offset[1])
                # 注意：外发光效果的 render 第四个参数 (special_flags) 在某些Pygame版本中不支持，
                # 为了兼容性，我们直接渲染一个半透明的颜色表面。
                # 这里我们简单地重新渲染一个颜色略有不同的表面来模拟。
                glow_surface = title_font.render(title_text, True, (100, 100, 200))
                glow_surface.set_alpha(50) # 设置透明度
                surface.blit(glow_surface, glow_rect)
            
            surface.blit(title_surface, title_rect)
            
            # 装饰性线条 [cite: 699, 700]
            line_width = 200
            line_y = title_rect.bottom + 20
            left_line_start = (SCREEN_WIDTH // 2 - line_width // 2, line_y)
            
            for i in range(line_width):
                alpha = int(255 * (1 - abs(i - line_width // 2) / (line_width // 2)))
                color = (100, 150, 255, alpha)
                x = left_line_start[0] + i
                pygame.draw.circle(surface, color, (x, line_y), 2)
                    
    def _draw_subtitle(self, surface):
        subtitle_font = self._get_font('normal', 24)
        subtitle_text = "一个史诗般的冒险等待着你"
        subtitle_surface = subtitle_font.render(subtitle_text, True, (150, 150, 200))
        subtitle_rect = subtitle_surface.get_rect(center=(SCREEN_WIDTH // 2, 220))
        surface.blit(subtitle_surface, subtitle_rect)
        
        version_font = self._get_font('small', 16)
        version_text = "Version 1.0 Alpha"
        version_surface = version_font.render(version_text, True, (100, 100, 150))
        version_rect = version_surface.get_rect(bottomright=(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 20))
        surface.blit(version_surface, version_rect)

    def _draw_menu_buttons(self, surface):
        if self.menu_entrance_animation < 1.0:
            for i, (key, button) in enumerate(self.buttons.items()):
                delay = i * 0.1
                progress = max(0, min(1, (self.menu_entrance_animation - delay) / 0.8))
                offset_x = (1 - progress) * 200
                temp_rect = button.rect.move(offset_x, 0)
                alpha = int(255 * progress)
                self._draw_button(surface, button, temp_rect, self.hover_animations[key], alpha)
        else:
            for key, button in self.buttons.items():
                hover_alpha = self.hover_animations[key]
                self._draw_button(surface, button, button.rect, hover_alpha, 255)

    def _draw_button(self, surface, button, rect, hover_alpha, alpha):
            """绘制单个按钮"""
            scale = 1.0 + hover_alpha * 0.05
            if scale != 1.0:
                scaled_size = (int(rect.width * scale), int(rect.height * scale))
                scaled_rect = pygame.Rect(0, 0, *scaled_size)
                scaled_rect.center = rect.center
                rect = scaled_rect
            
            bg_alpha = int((120 + hover_alpha * 60) * (alpha / 255))
            border_alpha = int((180 + hover_alpha * 75) * (alpha / 255))
            base_color = getattr(button, 'accent_color', (100, 150, 200))
            bg_color = (*base_color, bg_alpha)
            border_color = (*base_color, border_alpha)
            
            pygame.draw.rect(surface, bg_color, rect, border_radius=12)
            pygame.draw.rect(surface, border_color, rect, width=3, border_radius=12)
            
            if hover_alpha > 0:
                glow_intensity = int((math.sin(self.glow_animation) + 1) * hover_alpha * 20 + 10)
                glow_surface = pygame.Surface(rect.size, pygame.SRCALPHA)
                pygame.draw.rect(glow_surface, (*base_color, glow_intensity), (0, 0, rect.width, rect.height), border_radius=12)
                surface.blit(glow_surface, rect.topleft)
            
            ### --- 核心修复：按钮文字也使用 Emoji 安全函数 --- ###
            font = self._get_font('normal', 20)
            main_text_color = (255, 255, 255) if hover_alpha > 0.3 else (200, 200, 200)

            # 估算位置
            emoji_placeholders = {'🎮':'  ', '📖':'  ', '💾':'  ', '⚔️':'  '}
            text_to_measure = button.text
            for emoji, placeholder in emoji_placeholders.items():
                text_to_measure = text_to_measure.replace(emoji, placeholder)

            estimated_surf = font.render(text_to_measure, True, (0,0,0))
            estimated_rect = estimated_surf.get_rect(center=rect.center)
            
            # 安全绘制 (注意：这会失去描边效果，但能确保Emoji正确显示)
            draw_text_with_emoji_fallback(surface, button.text, estimated_rect.topleft, TEXT_COLOR)


class ModernButton:
    def __init__(self, rect, text, font, accent_color=(100, 150, 200)):
        if isinstance(rect, tuple):
            self.rect = pygame.Rect(*rect)
        else:
            self.rect = rect
        self.text = text
        self.font = font
        self.accent_color = accent_color
        self.is_hovered = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False