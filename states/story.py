# 文件: states/story.py (现代化重写版本)

import pygame
import math
import random
from .base import BaseState
from .dungeon_screen import DungeonScreen
from .saving import SaveScreen
from .loading import LoadScreen
from .backpack import BackpackScreen
from .talents_screen import TalentsScreen
from ui import draw_text, Button
from settings import *

# --- 新增：为这个现代化界面创建一个专属的按钮类 ---
class ModernStoryButton:
    """一个带有颜色和动画支持的现代化按钮"""
    def __init__(self, rect, text, font, accent_color=(100, 150, 200)):
        if isinstance(rect, tuple):
            self.rect = pygame.Rect(*rect)
        else:
            self.rect = rect
        self.text = text
        self.font = font
        self.accent_color = accent_color
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

    def draw(self, surface, hover_alpha):
        """
        根据 hover_alpha (0.0 到 1.0) 动态绘制按钮。
        hover_alpha 由 StoryScreen 的 update 函数计算和传入。
        """
        # 根据悬停程度进行缩放
        scale = 1.0 + hover_alpha * 0.05
        if scale != 1.0:
            scaled_size = (int(self.rect.width * scale), int(self.rect.height * scale))
            draw_rect = pygame.Rect(0, 0, *scaled_size)
            draw_rect.center = self.rect.center
        else:
            draw_rect = self.rect

        # 根据悬停程度调整颜色和透明度
        bg_alpha = int(120 + hover_alpha * 60)
        border_alpha = int(180 + hover_alpha * 75)
        
        bg_color = (*self.accent_color, bg_alpha)
        border_color = (*self.accent_color, border_alpha)
        
        pygame.draw.rect(surface, bg_color, draw_rect, border_radius=10)
        pygame.draw.rect(surface, border_color, draw_rect, width=2, border_radius=10)
        
        # 文字
        text_color = (255, 255, 255) if hover_alpha > 0.3 else (200, 200, 200)
        text_surface = self.font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=draw_rect.center)
        surface.blit(text_surface, text_rect)

class StoryScreen(BaseState):
    """现代化剧情界面 - 具备动态效果和沉浸式体验"""
    
    # 快捷键映射
    HOTKEY_MAP = {
        pygame.K_s: "save",
        pygame.K_l: "load", 
        pygame.K_b: "backpack",
        pygame.K_t: "talents"
    }
    
    def __init__(self, game):
        super().__init__(game)
        
        # 动画系统
        self.typewriter_cursor_blink = 0
        self.dialogue_box_glow = 0
        self.background_particles = []
        self.speaker_entrance_animation = 0
        self.button_hover_animations = {}
        self.text_shake = 0  # 用于紧张场景
        
        self._init_background_effects()
        self._init_ui()
        self._initialize_story()

    def _get_font(self, font_name, default_size=20):
        """安全获取字体"""
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)

    def _init_background_effects(self):
        """初始化背景特效"""
        # 创建漂浮粒子
        for _ in range(25):
            particle = {
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(1, 3),
                'speed': random.uniform(0.1, 0.5),
                'alpha': random.uniform(20, 60),
                'direction': random.uniform(0, 2 * math.pi),
                'phase': random.uniform(0, 2 * math.pi)
            }
            self.background_particles.append(particle)

    def _init_ui(self):
        """初始化UI组件"""
        self.buttons = self._create_buttons()
        
        # 初始化悬停动画
        for button_name in self.buttons:
            self.button_hover_animations[button_name] = 0

    def _create_buttons(self):
        """创建现代化按钮布局"""
        button_configs = [
            ("talents", "天赋 T", (139, 92, 246)),
            ("backpack", "背包 B", (59, 130, 246)), 
            ("load", "加载 L", (245, 158, 11)),
            ("save", "保存 S", (16, 185, 129))
        ]
        
        buttons = {}
        button_w, button_h = 120, 45
        padding = 15
        
        # 从右往左排列按钮
        start_x = SCREEN_WIDTH - padding - button_w
        start_y = SCREEN_HEIGHT - padding - button_h - 260
        
        for i, (key, text, color) in enumerate(button_configs):
            x = start_x - i * (button_w + padding)
            rect = pygame.Rect(x, start_y, button_w, button_h)
            buttons[key] = ModernStoryButton(rect, text, self._get_font('small'), color)
        
        return buttons

    def _initialize_story(self):
        """初始化剧情状态"""
        start_index = getattr(self.game, "loaded_dialogue_index", 0)
        self.dialogue_index = start_index
        self.displayed_chars = 0
        self.typing_complete = False
        self.last_char_time = 0
        self.typewriter_speed = 30
        self.game.loaded_dialogue_index = 0
        
        # 重置说话者动画
        self.speaker_entrance_animation = 0

    def update(self, dt=0):
        """更新动画和打字机效果"""
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): 
            self._last_time = current_time
            
        dt_ms = current_time - self._last_time
        self._last_time = current_time
        dt_sec = dt_ms / 1000.0
        
        # 更新各种动画
        self.typewriter_cursor_blink = (self.typewriter_cursor_blink + dt_sec * 3) % (2 * math.pi)
        self.dialogue_box_glow = (self.dialogue_box_glow + dt_sec * 2) % (2 * math.pi)
        self.speaker_entrance_animation = min(1.0, self.speaker_entrance_animation + dt_sec * 3)
        
        # 更新背景粒子
        for particle in self.background_particles:
            particle['x'] += math.cos(particle['direction']) * particle['speed']
            particle['y'] += math.sin(particle['direction']) * particle['speed']
            particle['alpha'] = 30 + 20 * math.sin(particle['phase'] + current_time * 0.001)
            
            # 边界循环
            if particle['x'] < 0: particle['x'] = SCREEN_WIDTH
            elif particle['x'] > SCREEN_WIDTH: particle['x'] = 0
            if particle['y'] < 0: particle['y'] = SCREEN_HEIGHT  
            elif particle['y'] > SCREEN_HEIGHT: particle['y'] = 0
        
        # 悬停检测
        mouse_pos = pygame.mouse.get_pos()
        for button_name, button in self.buttons.items():
            if button.rect.collidepoint(mouse_pos):
                self.button_hover_animations[button_name] = min(1.0, self.button_hover_animations[button_name] + dt_sec * 4)
            else:
                self.button_hover_animations[button_name] = max(0, self.button_hover_animations[button_name] - dt_sec * 3)
        
        # 打字机效果
        self._update_typewriter(current_time)

    def _update_typewriter(self, current_time):
        """更新打字机效果"""
        if self.typing_complete:
            return
            
        if current_time - self.last_char_time <= self.typewriter_speed:
            return
        
        stage_data = self.game.story_data.get(self.game.current_stage, {})
        dialogue_list = stage_data.get("text", [])
        
        if not dialogue_list or self.dialogue_index >= len(dialogue_list):
            self.typing_complete = True
            return
        
        current_line = dialogue_list[self.dialogue_index].get("line", "")
        
        if self.displayed_chars < len(current_line):
            self.displayed_chars += 1
            self.last_char_time = current_time
        else:
            self.typing_complete = True

    def handle_event(self, event):
        """处理输入事件"""
        if self._handle_button_events(event):
            return
        
        if self._handle_hotkey_events(event):
            return
        
        self._handle_dialogue_events(event)

    def _handle_button_events(self, event):
        """处理按钮点击事件"""
        button_actions = {
            "save": lambda: self.game.state_stack.append(SaveScreen(self.game)),
            "load": lambda: self.game.state_stack.append(LoadScreen(self.game)),
            "backpack": lambda: self.game.state_stack.append(BackpackScreen(self.game)),
            "talents": lambda: self.game.state_stack.append(TalentsScreen(self.game))
        }
        
        for button_name, action in button_actions.items():
            if self.buttons[button_name].handle_event(event):
                action()
                return True
        
        return False

    def _handle_hotkey_events(self, event):
        """处理快捷键事件"""
        if event.type != pygame.KEYDOWN:
            return False
        
        if event.key in self.HOTKEY_MAP:
            button_name = self.HOTKEY_MAP[event.key]
            # 模拟按钮点击行为
            if self.buttons[button_name].handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'button': 1, 'pos': self.buttons[button_name].rect.center})):
                button_actions = {
                    "save": lambda: self.game.state_stack.append(SaveScreen(self.game)),
                    "load": lambda: self.game.state_stack.append(LoadScreen(self.game)),
                    "backpack": lambda: self.game.state_stack.append(BackpackScreen(self.game)),
                    "talents": lambda: self.game.state_stack.append(TalentsScreen(self.game))
                }
                button_actions[button_name]()
                return True
        
        return False

    def _handle_dialogue_events(self, event):
        """处理对话相关事件"""
        should_advance = False
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not any(btn.rect.collidepoint(event.pos) for btn in self.buttons.values()):
                should_advance = True
        
        elif event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]:
            should_advance = True
        
        if should_advance:
            self._advance_dialogue()

    def _advance_dialogue(self):
        """推进对话"""
        if not self.typing_complete:
            self._complete_current_line()
            return
        
        if self._handle_dialogue_action():
            return
        
        self._next_dialogue()

    def _complete_current_line(self):
        """完成当前行的打字效果"""
        stage_data = self.game.story_data.get(self.game.current_stage, {})
        dialogue_list = stage_data.get("text", [])
        
        if self.dialogue_index < len(dialogue_list):
            current_line = dialogue_list[self.dialogue_index].get("line", "")
            self.displayed_chars = len(current_line)
        
        self.typing_complete = True

    def _handle_dialogue_action(self):
        """处理对话中的特殊动作"""
        stage_data = self.game.story_data.get(self.game.current_stage, {})
        dialogue_list = stage_data.get("text", [])
        
        if self.dialogue_index < len(dialogue_list):
            current_dialogue = dialogue_list[self.dialogue_index]
            action = current_dialogue.get("action")
            
            if action == "start_trial":
                self.game.state_stack.pop()
                self.game.state_stack.append(DungeonScreen(self.game, "sunstone_ruins", 1))
                return True
        
        return False

    def _next_dialogue(self):
        """切换到下一段对话"""
        stage_data = self.game.story_data.get(self.game.current_stage, {})
        dialogue_list = stage_data.get("text", [])

        # --- 核心修改：在推进对话前，先记录当前的说话者 ---
        current_speaker = None
        if self.dialogue_index < len(dialogue_list):
            current_speaker = dialogue_list[self.dialogue_index].get("speaker")

        self.dialogue_index += 1 # 推进到下一句
        
        if self.dialogue_index >= len(dialogue_list):
            self._handle_stage_end(stage_data)
        else:
            self._reset_typewriter()

            # --- 核心修改：获取下一句的说话者，并进行比较 ---
            next_speaker = dialogue_list[self.dialogue_index].get("speaker")
            
            # 只有当说话者发生变化时，才重置入场动画
            if current_speaker != next_speaker:
                self.speaker_entrance_animation = 0

    def _handle_stage_end(self, stage_data):
        """处理剧情阶段结束"""
        from .combat import CombatScreen
        from .title import TitleScreen
        
        next_stage = stage_data.get("next", "quit")
        self.game.current_stage = next_stage
        
        if next_stage == "quit":
            self.game.state_stack = [TitleScreen(self.game)]
            return
        
        next_stage_data = self.game.story_data.get(next_stage, {})
        
        if next_stage_data.get("type") == "combat":
            enemy_id = next_stage_data.get("enemy_id", "slime")
            self.game.state_stack.pop()
            self.game.state_stack.append(CombatScreen(self.game, enemy_id))
        else:
            self._initialize_story()

    def _reset_typewriter(self):
        """重置打字机效果"""
        self.displayed_chars = 0
        self.typing_complete = False
        self.last_char_time = 0

    def draw(self, surface):
        """绘制界面"""
        # 动态背景
        self._draw_dynamic_background(surface)
        
        # 背景粒子
        self._draw_background_particles(surface)
        
        # 对话框
        self._draw_modern_dialogue_box(surface)
        
        # 按钮
        self._draw_modern_buttons(surface)
        
        # 更新动画
        self.update()

    def _draw_dynamic_background(self, surface):
        """绘制动态背景"""
        # 根据剧情内容调整背景色调
        dialogue = self._get_current_dialogue()
        speaker = dialogue.get("speaker", "旁白")
        
        # 根据说话者给一个基础色调
        if speaker == "你":
            base_color = (25, 35, 70) # 玩家的蓝色调
        else: # 旁白或其他
            base_color = (20, 30, 50) # 默认的深蓝色调

        # 绘制渐变背景
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(base_color[0] + progress * 20)
            g = int(base_color[1] + progress * 15)
            b = int(base_color[2] + progress * 30)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # --- 以下是新增和补全的绘制函数 ---

    def _draw_background_particles(self, surface):
        """绘制背景粒子"""
        for particle in self.background_particles:
            color = (100, 150, 255, particle['alpha'])
            # 使用一个小的Surface来绘制带透明度的圆，性能更好
            particle_surface = pygame.Surface((particle['size'] * 2, particle['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surface, color, (particle['size'], particle['size']), particle['size'])
            surface.blit(particle_surface, (particle['x'] - particle['size'], particle['y'] - particle['size']))

    def _draw_modern_dialogue_box(self, surface):
        """绘制现代化的对话框"""
        dialogue_box_rect = pygame.Rect(50, SCREEN_HEIGHT - 250, SCREEN_WIDTH - 100, 200)
        
        # 绘制带光晕的面板背景
        glow_size = int(10 + 5 * math.sin(self.dialogue_box_glow))
        glow_color = (70, 80, 100, 50)
        glow_rect = dialogue_box_rect.inflate(glow_size, glow_size)
        pygame.draw.rect(surface, glow_color, glow_rect, border_radius=15)
        
        # 绘制面板主体
        pygame.draw.rect(surface, (25, 30, 50, 230), dialogue_box_rect, border_radius=12)
        pygame.draw.rect(surface, (70, 80, 100, 180), dialogue_box_rect, 2, border_radius=12)
        
        dialogue = self._get_current_dialogue()
        speaker = dialogue.get("speaker", "旁白")
        full_line = dialogue.get("line", "")
        
        if speaker != "旁白":
            self._draw_speaker_name(surface, dialogue_box_rect, speaker)
        
        self._draw_dialogue_text(surface, dialogue_box_rect, full_line)
        
        if self.typing_complete:
            self._draw_continue_prompt(surface, dialogue_box_rect)

    def _draw_speaker_name(self, surface, dialogue_box_rect, speaker):
        """绘制带入场动画的说话者名称"""
        speaker_font = self._get_font('normal')
        speaker_surf = speaker_font.render(speaker, True, (255, 215, 0))
        
        # 计算入场动画偏移
        start_y = dialogue_box_rect.top
        end_y = dialogue_box_rect.top - 35
        current_y = start_y + (end_y - start_y) * self.speaker_entrance_animation

        panel_rect = speaker_surf.get_rect(topleft=(dialogue_box_rect.left + 30, current_y))
        panel_rect.inflate_ip(25, 12)
        
        # 设置透明度
        panel_surface = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        panel_surface.set_alpha(255 * self.speaker_entrance_animation)
        
        pygame.draw.rect(panel_surface, (35, 40, 65, 200), panel_surface.get_rect(), border_radius=8)
        pygame.draw.rect(panel_surface, (100, 120, 150), panel_surface.get_rect(), 2, border_radius=8)
        
        panel_surface.blit(speaker_surf, (12, 6))
        surface.blit(panel_surface, panel_rect.topleft)

    def _draw_dialogue_text(self, surface, dialogue_box_rect, full_line):
        """绘制带打字机效果的文本（已修复光标位置）"""
        text_to_render = full_line[:self.displayed_chars]
        text_rect = dialogue_box_rect.inflate(-80, -80)
        
        # --- 核心修改在这里 ---
        # 1. 调用 draw_text，并要求它返回光标位置
        cursor_pos = draw_text(
            surface, 
            text_to_render, 
            self._get_font('normal'), 
            (220, 220, 220), 
            text_rect,
            return_cursor_pos=True  # <--- 开启新功能！
        )
        
        # 2. 绘制闪烁的光标
        if not self.typing_complete and cursor_pos:
            font = self._get_font('normal')
            cursor_x = cursor_pos[0] + 2
            cursor_y = cursor_pos[1]
            
            # 使用 sin 函数创建平滑的闪烁效果
            cursor_alpha = int(128 + 127 * math.sin(self.typewriter_cursor_blink))
            
            # 创建一个带透明度的临时 surface 来画线，避免影响其他元素
            line_surf = pygame.Surface((2, font.get_height()), pygame.SRCALPHA)
            pygame.draw.line(line_surf, (255, 255, 255, cursor_alpha), 
                             (0, 0), (0, font.get_height() - 5), 2)
            surface.blit(line_surf, (cursor_x, cursor_y))

    def _draw_continue_prompt(self, surface, dialogue_box_rect):
        """绘制带动画的继续提示"""
        pulse = 5 * math.sin(self.dialogue_box_glow)
        prompt_pos = (dialogue_box_rect.right - 40, dialogue_box_rect.bottom - 35 + pulse)
        
        points = [
            prompt_pos, 
            (prompt_pos[0] - 15, prompt_pos[1] - 10), 
            (prompt_pos[0] - 15, prompt_pos[1] + 10)
        ]
        pygame.draw.polygon(surface, (255, 255, 255, 150 + abs(pulse)*10), points)

    def _draw_modern_buttons(self, surface):
        """绘制所有现代化按钮"""
        for button_name, button in self.buttons.items():
            hover_alpha = self.button_hover_animations.get(button_name, 0)
            button.draw(surface, hover_alpha)

    def _get_current_dialogue(self):
        """安全地获取当前对话内容"""
        stage_data = self.game.story_data.get(self.game.current_stage, {})
        dialogue_list = stage_data.get("text", [{"speaker": "旁白", "line": "..."}])
        safe_index = min(self.dialogue_index, len(dialogue_list) - 1)
        return dialogue_list[safe_index]