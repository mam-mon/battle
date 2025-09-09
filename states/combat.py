# 文件: states/combat.py (最终统一版本)

import pygame
import time
import random
import math

from states.combat_victory import CombatVictoryScreen
from .base import BaseState
from ui import TooltipManager, Button, draw_text_with_outline, get_display_name, draw_text_with_emoji_fallback
from settings import *
from Character import Character
import Talents
from battle_logger import battle_logger

class ModernButton(Button):
    def __init__(self, rect, text, font, accent_color=(100, 150, 200)):
        super().__init__(rect, text, font)
        self.accent_color = accent_color
    
    # 文件: states/combat.py (在 ModernButton 类中，替换 draw 方法)

    def draw(self, surface):
        # 按钮的背景和边框绘制保持不变
        pygame.draw.rect(surface, self.accent_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, (255, 255, 255), self.rect, width=2, border_radius=8)
        
        # --- 核心修复：精确居中 Emoji 和文本 ---
        # 1. 直接使用 self.font 渲染出包含 Emoji 的文本表面。
        #    (我们相信 ui.py 中的字体系统能处理好它)
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        
        # 2. 获取这个渲染好的文本表面的矩形，并将其“中心点”设置为我们按钮的“中心点”。
        #    这是 Pygame 中最标准、最精确的居中方法。
        text_rect = text_surface.get_rect(center=self.rect.center)
        
        # 3. 将文本表面绘制到这个完美计算好的位置上。
        surface.blit(text_surface, text_rect)

class ModernScrollableLog:
    def __init__(self, rect, font, line_height=20):
        self.rect = rect
        self.font = font
        self.line_height = line_height
        self.messages = []
        self.scroll_offset = 0
        self.max_lines = (self.rect.height - 45) // self.line_height
        
    def add_message(self, parts):
        if isinstance(parts, str): parts = [(parts, (200, 200, 200))]
        self.messages.append(parts)
        if len(self.messages) > 100: self.messages.pop(0)
        if len(self.messages) > self.max_lines:
            self.scroll_offset = len(self.messages) - self.max_lines
    
    def handle_event(self, event):
        if self.rect.collidepoint(pygame.mouse.get_pos()):
            if event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, len(self.messages) - self.max_lines)
                self.scroll_offset = max(0, min(max_scroll, self.scroll_offset - event.y))
    
    # 文件: states/combat.py (在 CombatScreen 类中，替换 draw 方法)

    # 文件: states/combat.py (在 ModernScrollableLog 类中，替换这个 draw 方法)

    def draw(self, surface):
        # 绘制日志面板的背景和边框
        pygame.draw.rect(surface, (20, 25, 40, 220), self.rect, border_radius=10)
        pygame.draw.rect(surface, (70, 80, 100, 180), self.rect, width=2, border_radius=10)
        
        # 使用我们安全的方法绘制带Emoji的日志标题
        draw_text_with_emoji_fallback(surface, "⚔️ 战斗日志", (self.rect.x + 15, self.rect.y + 8), (255, 215, 0))

        # --- 以下是绘制滚动文字的核心逻辑 ---
        
        # 定义一个只在日志框内部绘制的“剪切区域”
        content_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 35, self.rect.width - 30, self.rect.height - 45)
        original_clip = surface.get_clip()
        surface.set_clip(content_rect)
        
        y_pos = content_rect.y
        # 从滚动偏移量开始，只绘制可见行数的日志
        for i in range(self.scroll_offset, min(len(self.messages), self.scroll_offset + self.max_lines)):
            x_pos = content_rect.x
            # 绘制一行中的每一个富文本片段
            for text, color in self.messages[i]:
                text_surface = self.font.render(text, True, color)
                surface.blit(text_surface, (x_pos, y_pos))
                x_pos += text_surface.get_width() # 水平移动光标
            y_pos += self.line_height # 垂直换行
            
        # 恢复原始的剪切区域，防止影响其他UI的绘制
        surface.set_clip(original_clip)

    def _get_font(self, font_name, default_size=20):
        try: return pygame.font.SysFont(FONT_NAME_CN, default_size)
        except: return pygame.font.Font(None, default_size)

class CombatScreen(BaseState):
    # ... (CombatScreen 类的其余部分保持不变，因为 ModernButton 和 ModernScrollableLog 的修复已在上面完成)
    # 此处省略，请使用您当前文件中的版本
    def __init__(self, game, enemy_id, origin_identifier=None):
        super().__init__(game)
        self.enemy_id = enemy_id
        self.origin_id = origin_identifier
        self.battle_ended = False
        self.is_paused = False
        self.shake_intensity = 0
        self.screen_flash = 0
        self.damage_numbers = []
        self.battle_particles = []
        self.glow_animation = 0
        self._initialize_combat()
        self._init_ui()
        self._set_opponents()
        self._init_battle_log()
        self._init_visual_effects()
    def _get_font(self, font_name, default_size=20):
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)
    def _init_ui(self):
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        self.player_ui_elements = {}; self.enemy_ui_elements = {}
        pause_button_rect = pygame.Rect(SCREEN_WIDTH - 80, 20, 60, 50)
        self.pause_button = ModernButton(pause_button_rect, "⏸️", self._get_font('normal'), (100, 150, 200))
        self.end_timer = 0.0; self.END_DELAY = 2.0
    def _initialize_combat(self):
        try:
            enemy_preset = self.game.enemy_data[self.enemy_id]
        except KeyError:
            raise ValueError(f"未找到敌人数据: {self.enemy_id}")
        rolled_talents = self._generate_enemy_talents(enemy_preset)
        self.enemy = Character(id=self.enemy_id, name=enemy_preset["name"], talents=rolled_talents, **enemy_preset["stats"])
        self.displayed_hp = {'player': self.game.player.hp, 'enemy': self.enemy.hp}
        self.displayed_shield = {'player': self.game.player.shield, 'enemy': self.enemy.shield}
        self.game.player.on_enter_combat()
        self.enemy.on_enter_combat()
        self.last_update_time = time.time()
        self._trigger_battle_start_events()
    def _generate_enemy_talents(self, enemy_preset):
        rolled_talents = []
        for talent_info in enemy_preset.get("possible_talents", []):
            if random.random() < talent_info["chance"]:
                talent = self._create_talent(talent_info["talent_class_name"])
                if talent: rolled_talents.append(talent)
        for talent_class_name in enemy_preset.get("talents", []):
            talent = self._create_talent(talent_class_name)
            if talent: rolled_talents.append(talent)
        return rolled_talents
    def _create_talent(self, talent_class_name):
        if hasattr(Talents, talent_class_name):
            return getattr(Talents, talent_class_name)()
        return None
    def _set_opponents(self):
        self.game.player.current_opponent = self.enemy; self.enemy.current_opponent = self.game.player
    def _trigger_battle_start_events(self):
        for char in [self.game.player, self.enemy]:
            for talent in char.equipped_talents:
                if talent and hasattr(talent, 'on_battle_start'): talent.on_battle_start(char, char.current_opponent)
            for eq in char.all_active_items:
                if hasattr(eq, 'on_battle_start'): eq.on_battle_start(char)
    def _init_battle_log(self):
        log_rect = pygame.Rect(40, SCREEN_HEIGHT - 220, SCREEN_WIDTH - 80, 180)
        self.log_renderer = ModernScrollableLog(log_rect, self._get_font('small'), line_height=22)
        battle_logger.register_renderer(self.log_renderer)
        battle_logger.log([(f"⚔️ 战斗开始！遭遇了 ", (200,200,200)), (f"{self.enemy.name}", (255,100,100)), ("！", (200,200,200))])
    def _init_visual_effects(self):
        for _ in range(30):
            self.battle_particles.append({'pos': [random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT)],
                'size': random.uniform(1, 2.5), 'speed': random.uniform(0.1, 0.4), 'alpha': random.uniform(10, 40), 'direction': random.uniform(0, 2 * math.pi)})
    def handle_event(self, event):
        if self._handle_pause_event(event) or self.is_paused: return
        self.log_renderer.handle_event(event)
        self._handle_escape_event(event)
    def _handle_pause_event(self, event):
        pause_triggered = (self.pause_button.handle_event(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_p))
        if pause_triggered:
            self.is_paused = not self.is_paused
            self.pause_button.text = "▶️" if self.is_paused else "⏸️"
            if not self.is_paused: self.last_update_time = time.time()
            return True
        return False
    def _handle_escape_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from .confirm_dialog import ConfirmDialog; from .title import TitleScreen
            def on_confirm_action(): self.game.state_stack = [TitleScreen(self.game)]
            self.game.state_stack.append(ConfirmDialog(self.game, "⚠️ 所有战斗进度都将丢失，确定要返回主菜单吗？", on_confirm_action, title="退出战斗", confirm_text="确认退出", cancel_text="继续战斗"))
            return True
        return False
    def update(self):
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_anim_time'): self._last_anim_time = current_time
        dt_sec = (current_time - self._last_anim_time) / 1000.0
        self._last_anim_time = current_time
        self._update_animations(dt_sec)
        self._update_hovers()
        if self.is_paused: return
        dt = time.time() - self.last_update_time
        self.last_update_time = time.time()
        if self.battle_ended:
            self._handle_battle_end(dt); return
        self._update_characters(dt)
        self._handle_attacks(dt)
        self._check_battle_end()
    def _update_animations(self, dt):
        self.glow_animation = (self.glow_animation + dt * 2) % (2 * math.pi)
        if self.shake_intensity > 0: self.shake_intensity = max(0, self.shake_intensity - dt * 200)
        if self.screen_flash > 0: self.screen_flash = max(0, self.screen_flash - dt * 800)
        for char_type in ['player', 'enemy']:
            char = self.game.player if char_type == 'player' else self.enemy
            for val_type, disp_val in [('hp', self.displayed_hp), ('shield', self.displayed_shield)]:
                target = getattr(char, val_type); current = disp_val[char_type]
                if abs(target - current) > 0.1: disp_val[char_type] += (target - current) * dt * 8
                else: disp_val[char_type] = target
        for dn in self.damage_numbers[:]:
            dn['pos'][1] -= dt * 60; dn['alpha'] -= dt * 350
            if dn['alpha'] <= 0: self.damage_numbers.remove(dn)
        for p in self.battle_particles:
            p['pos'][0] += math.cos(p['direction']) * p['speed']; p['pos'][1] += math.sin(p['direction']) * p['speed']
            if p['pos'][0] < 0: p['pos'][0] = SCREEN_WIDTH
            elif p['pos'][0] > SCREEN_WIDTH: p['pos'][0] = 0
            if p['pos'][1] < 0: p['pos'][1] = SCREEN_HEIGHT
            elif p['pos'][1] > SCREEN_HEIGHT: p['pos'][1] = 0
    def _update_characters(self, dt):
        self.game.player.update(dt); self.enemy.update(dt)
    def _handle_attacks(self, dt):
        for attacker, target, type_str in [(self.game.player, self.enemy, 'player'), (self.enemy, self.game.player, 'enemy')]:
            result = attacker.try_attack(target, dt)
            if result:
                self._log_attack_result(result)
                self._create_attack_effects(type_str, result[2])
    def _log_attack_result(self, attack_result):
        log_parts, extra_logs, _ = attack_result
        battle_logger.log(log_parts)
        for extra_log in extra_logs: battle_logger.log([("  └ ", (150,150,150)), (extra_log, (150,150,150))])
    def _create_attack_effects(self, attacker_type, damage_details):
        self.shake_intensity = 10
        damage_amount = damage_details.get("final_amount", 0)
        if damage_amount <= 0: return
        is_crit = damage_details.get("is_critical", False)
        pos = (SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.25) if attacker_type == 'player' else (SCREEN_WIDTH * 0.25, SCREEN_HEIGHT * 0.25)
        self.damage_numbers.append({'pos': [pos[0] + random.uniform(-20, 20), pos[1]], 'alpha': 255, 'text': str(damage_amount), 'is_crit': is_crit})
    def _check_battle_end(self):
        if not self.battle_ended and (self.enemy.hp <= 0 or self.game.player.hp <= 0):
            self.battle_ended = True; self.end_timer = 0.0
    def _handle_battle_end(self, dt):
        self.end_timer += dt
        if self.end_timer >= self.END_DELAY:
            if self.enemy.hp <= 0: self._on_victory()
            else: self._on_defeat()
    def _on_victory(self):
        self._clear_opponents(); battle_logger.unregister_renderer()
        from .dungeon_screen import DungeonScreen
        next_story_stage_id = None
        if len(self.game.state_stack) > 1 and isinstance(self.game.state_stack[-2], DungeonScreen):
            if self.origin_id: self.game.state_stack[-2].on_monster_defeated(self.origin_id)
        else:
            next_story_stage_id = self.game.story_data.get(self.game.current_stage, {}).get("next_win")
        self.game.state_stack.pop()
        self.game.state_stack.append(CombatVictoryScreen(self.game, self.enemy, next_story_stage=next_story_stage_id))
    def _on_defeat(self):
        from .title import TitleScreen
        self._clear_opponents(); battle_logger.unregister_renderer()
        self.game.state_stack = [TitleScreen(self.game)]
    def _clear_opponents(self):
        self.game.player.current_opponent = None
        if hasattr(self, 'enemy'): self.enemy.current_opponent = None
    def _update_hovers(self):
        mouse_pos = pygame.mouse.get_pos(); hovered_object = None
        all_elements = (self.player_ui_elements.get('talents', []) + self.player_ui_elements.get('buffs', []) + self.enemy_ui_elements.get('talents', []) + self.enemy_ui_elements.get('buffs', []))
        for rect, obj in all_elements:
            if rect.collidepoint(mouse_pos):
                hovered_object = obj; break
        self.tooltip_manager.update(hovered_object)

# 文件: states/combat.py (在 CombatScreen 类中，添加这个完整的 draw 方法)

    # 文件: states/combat.py (在 CombatScreen 类中，替换 draw 方法)

    def draw(self, surface):
        # 1. 绘制背景和粒子效果 (不变)
        self._draw_battle_background(surface)

        # 2. 应用屏幕震动 (不变)
        render_offset = [0, 0]
        if self.shake_intensity > 0:
            render_offset[0] = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
            render_offset[1] = random.randint(-int(self.shake_intensity), int(self.shake_intensity))
        
        # 3. 绘制角色、日志等核心UI (不变)
        player_rect = PLAYER_PANEL_RECT.move(render_offset)
        enemy_rect = ENEMY_PANEL_RECT.move(render_offset)
        self._draw_enhanced_character_panels(surface, player_rect, enemy_rect)
        self._draw_modern_action_panel(surface)
        self.log_renderer.draw(surface)

        # 4. 绘制伤害数字、闪光等特效 (不变)
        self._draw_damage_numbers(surface)
        if self.screen_flash > 0:
            flash_surface = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            flash_surface.fill((255, 255, 255, self.screen_flash))
            surface.blit(flash_surface, (0, 0))

        # 5. 绘制悬浮提示框 (不变)
        self.tooltip_manager.draw(surface)
        
        # --- 核心修复：调整绘制顺序 ---
        
        # 6. 如果游戏已暂停，先绘制半透明遮罩和“游戏已暂停”的文字
        if self.is_paused:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))
            
            pause_font = self._get_font('large', 48)
            draw_text_with_emoji_fallback(surface, "游戏已暂停", pause_font, TEXT_COLOR, (100, 100, 100), surface.get_rect().center)

        # 7. 最后，在所有东西都画完之后，再画我们的暂停按钮。
        #    这样无论是否暂停，它都会显示在最顶层！
        self.pause_button.draw(surface)

    def _draw_battle_background(self, surface):
        surface.fill(BG_COLOR)
        for p in self.battle_particles:
            alpha = int(p['alpha'] * (0.5 + 0.5 * math.sin(self.glow_animation + p['pos'][0] * 0.01)))
            p_surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (100, 150, 200, alpha), (p['size'], p['size']), p['size'])
            surface.blit(p_surf, (p['pos'][0] - p['size'], p['pos'][1] - p['size']))
    def _draw_enhanced_character_panels(self, surface, player_rect, enemy_rect):
        self.player_ui_elements = self._draw_base_character_panel(surface, self.game.player, player_rect)
        self.enemy_ui_elements = self._draw_base_character_panel(surface, self.enemy, enemy_rect)
        self._draw_animated_hp_bars(surface, player_rect, enemy_rect)
    def _draw_base_character_panel(self, surface, char, rect):
        ui_elements = {'talents': [], 'buffs': []}
        pygame.draw.rect(surface, (25, 30, 50, 220), rect, border_radius=15)
        pygame.draw.rect(surface, (70, 80, 100, 180), rect, 2, border_radius=15)
        name_surf = self._get_font('large').render(char.name, True, TEXT_COLOR)
        level_surf = self._get_font('normal').render(f"Lv. {char.level}", True, TEXT_COLOR)
        surface.blit(name_surf, (rect.left + 20, rect.top + 15))
        surface.blit(level_surf, (rect.left + name_surf.get_width() + 30, rect.top + 28))
        stats_text = f"攻击: {int(char.attack)} | 防御: {int(char.defense)} | 攻速: {char.attack_speed:.2f}"; stats_surf = self._get_font('small').render(stats_text, True, TEXT_COLOR)
        surface.blit(stats_surf, (rect.left + 20, rect.top + 140))
        for list_type, y_offset, color in [('talents', 170, (255, 215, 0)), ('buffs', 200, TEXT_COLOR)]:
            item_list = [t for t in getattr(char, 'equipped_talents' if list_type == 'talents' else 'buffs') if t and not getattr(t, 'hidden', False)]
            if not item_list: continue
            x = rect.left + 20; label_text = "天赋: " if list_type == 'talents' else "状态: "; label_surf = self._get_font('small').render(label_text, True, color)
            surface.blit(label_surf, (x, rect.top + y_offset)); x += label_surf.get_width()
            for i, item in enumerate(item_list):
                item_text = get_display_name(item)
                item_color = color
                if list_type == 'buffs':
                    if item.max_stacks > 1 and item.stacks > 1: item_text += f"({item.stacks})"
                    item_color = (255, 80, 80) if item.is_debuff else (80, 255, 80)
                text_surf = self._get_font('small').render(item_text, True, item_color)
                text_rect = text_surf.get_rect(left=x, top=rect.top + y_offset)
                surface.blit(text_surf, text_rect); ui_elements[list_type].append((text_rect, item)); x += text_rect.width
                if i < len(item_list) - 1:
                    sep_surf = self._get_font('small').render(" | ", True, color)
                    surface.blit(sep_surf, (x, rect.top + y_offset)); x += sep_surf.get_width()
        return ui_elements
    def _draw_animated_hp_bars(self, surface, player_rect, enemy_rect):
        for panel_rect, char, char_type in [(player_rect, self.game.player, 'player'), (enemy_rect, self.enemy, 'enemy')]:
            hp_rect = pygame.Rect(panel_rect.x + 20, panel_rect.y + 80, panel_rect.width - 40, 30)
            pygame.draw.rect(surface, (10, 20, 30), hp_rect, border_radius=8)
            max_hp = char.max_hp if char.max_hp > 0 else 1
            hp_percent = max(0, self.displayed_hp[char_type] / max_hp)
            hp_width = int((hp_rect.width - 4) * hp_percent)
            if hp_width > 0:
                hp_color = (100, 255, 100) if hp_percent > 0.6 else (255, 255, 100) if hp_percent > 0.3 else (255, 100, 100)
                pygame.draw.rect(surface, hp_color, (hp_rect.x + 2, hp_rect.y + 2, hp_width, hp_rect.height - 4), border_radius=6)
            shield_val = self.displayed_shield[char_type]
            if shield_val > 0:
                shield_percent = min(shield_val / max_hp, 1.0)
                shield_width = int((hp_rect.width - 4) * shield_percent)
                actual_shield_width = min(shield_width, (hp_rect.width - 4) - hp_width)
                if actual_shield_width > 0:
                    shield_rect = pygame.Rect(hp_rect.x + 2 + hp_width, hp_rect.y + 2, actual_shield_width, hp_rect.height - 4)
                    pygame.draw.rect(surface, SHIELD_BAR_GREY, shield_rect, border_top_right_radius=6, border_bottom_right_radius=6)
            pygame.draw.rect(surface, PANEL_BORDER_COLOR, hp_rect, 2, border_radius=8)
            hp_text = f"{int(char.hp)}/{int(max_hp)}" + (f" (+{int(char.shield)})" if char.shield > 0 else "")
            font = self._get_font('small', 16); text_surface = font.render(hp_text, True, TEXT_COLOR)
            surface.blit(text_surface, text_surface.get_rect(center=hp_rect.center))
    def _draw_modern_action_panel(self, surface):
        top_boundary = ENEMY_PANEL_RECT.bottom + 20
        log_top = self.log_renderer.rect.top - 20
        available_height = log_top - top_boundary
        panel_width = 240
        panel_height = min(200, available_height)
        panel_x = (SCREEN_WIDTH - panel_width) / 2
        panel_y = top_boundary
        action_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(surface, (25, 30, 50, 220), action_rect, border_radius=12)
        pygame.draw.rect(surface, (70, 80, 100, 160), action_rect, width=2, border_radius=12)
        title_font = self._get_font('normal', 20)
        # 修正：title_text现在只包含文本，Emoji在fallback函数中处理
        title_text_content = "战斗行动"
        title_text = f"⚔️ {title_text_content}"
        # 估算位置
        estimated_surf = title_font.render(title_text_content, True, (0,0,0))
        estimated_rect = estimated_surf.get_rect(centerx=action_rect.centerx, top=action_rect.top + 15)
        # 安全绘制
        draw_text_with_emoji_fallback(surface, title_text, estimated_rect.topleft, (255, 215, 0))
        line_y = estimated_rect.bottom + 10
        pygame.draw.line(surface, (70, 80, 100), (action_rect.x + 20, line_y), (action_rect.right - 20, line_y), 2)
        content_rect = pygame.Rect(action_rect.x + 15, line_y + 15, action_rect.width - 30, action_rect.height - 80) 
        content_text = "🎯 自动战斗中...\n\n⏸️ 按P键暂停\n\n💡 技能系统开发中"
        self._draw_wrapped_text(surface, content_text, self._get_font('small', 14), (200, 200, 200), content_rect)
    def _draw_wrapped_text(self, surface, text, font, color, rect):
        lines = text.split('\n'); line_height = font.get_height() + 3; y_offset = rect.y
        for line in lines:
            if y_offset + line_height > rect.bottom: break
            line_surface = font.render(line, True, color)
            surface.blit(line_surface, (rect.x, y_offset)); y_offset += line_height
    def _draw_damage_numbers(self, surface):
        for damage_num in self.damage_numbers:
            alpha = max(0, min(255, damage_num['alpha']))
            font_size = 36 if damage_num['is_crit'] else 28; font = self._get_font('large', font_size)
            color = CRIT_COLOR if damage_num['is_crit'] else (255, 120, 120)
            text_surface = font.render(damage_num['text'], True, color); text_surface.set_alpha(alpha)
            outline_surf = font.render(damage_num['text'], True, (0,0,0)); outline_surf.set_alpha(alpha * 0.8)
            pos = damage_num['pos']
            for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
                surface.blit(outline_surf, (pos[0] + dx, pos[1] + dy))
            surface.blit(text_surface, pos)