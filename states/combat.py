# 文件: states/combat.py (现代化重写版本)

import pygame
import time
import random
import math

from states.combat_victory import CombatVictoryScreen
from .base import BaseState
from ui import TooltipManager, Button, get_display_name
from settings import *
from Character import Character
import Talents
from battle_logger import battle_logger

# --- 核心修复：将辅助类的定义从文件末尾移到这里 ---

class ModernButton(Button):
    def __init__(self, rect, text, font, accent_color=(100, 150, 200)):
        super().__init__(rect, text, font)
        self.accent_color = accent_color
    
    def draw(self, surface):
        # 简化的绘制，未来可添加动画
        bg_color = self.accent_color
        border_color = (255, 255, 255)
        
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=8)
        
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

class ModernScrollableLog:
    """现代化可滚动日志"""
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
    
    def draw(self, surface):
        pygame.draw.rect(surface, (20, 25, 40, 220), self.rect, border_radius=10)
        pygame.draw.rect(surface, (70, 80, 100, 180), self.rect, width=2, border_radius=10)
        
        title_font = self._get_font('small', 16)
        title_text = title_font.render("⚔️ 战斗日志", True, (255, 215, 0))
        surface.blit(title_text, (self.rect.x + 15, self.rect.y + 8))
        
        content_rect = pygame.Rect(self.rect.x + 15, self.rect.y + 35, self.rect.width - 30, self.rect.height - 45)
        
        # 使用subsurface实现裁剪效果，防止文字溢出
        clip_area = surface.get_clip()
        surface.set_clip(content_rect)

        start_index = max(0, self.scroll_offset)
        end_index = min(len(self.messages), start_index + self.max_lines)
        
        y_pos = content_rect.y
        for i in range(start_index, end_index):
            message_parts = self.messages[i]
            x_pos = content_rect.x
            for text, color in message_parts:
                text_surface = self.font.render(text, True, color)
                surface.blit(text_surface, (x_pos, y_pos))
                x_pos += text_surface.get_width()
            y_pos += self.line_height

        surface.set_clip(clip_area) # 恢复裁剪区域

    def _get_font(self, font_name, default_size=20):
        # 辅助方法，避免重复代码
        try:
            return pygame.font.SysFont(FONT_NAME_CN, default_size)
        except:
             return pygame.font.Font(None, default_size)

# --- 修复结束 ---


class CombatScreen(BaseState):
    """现代化战斗界面 - 具备动态效果和视觉反馈"""
    
    def __init__(self, game, enemy_id, origin_identifier=None):
        super().__init__(game)
        self.enemy_id = enemy_id
        self.origin_id = origin_identifier
        self.battle_ended = False
        self.is_paused = False
        
        # 动画系统
        self.shake_intensity = 0
        self.screen_flash = 0
        self.damage_numbers = []
        self.battle_particles = []
        self.glow_animation = 0
        
        # 初始化战斗
        self._initialize_combat()
        self._init_ui()
        self._set_opponents()
        self._init_battle_log()
        self._init_visual_effects()

    def _get_font(self, font_name, default_size=20):
        """安全获取字体"""
        try:
            if hasattr(self.game, 'fonts') and font_name in self.game.fonts:
                return self.game.fonts[font_name]
        except:
            pass
        return pygame.font.Font(None, default_size)

    def _init_ui(self):
        """初始化UI组件"""
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])
        self.player_ui_elements = {}
        self.enemy_ui_elements = {}
        
        pause_button_rect = pygame.Rect(SCREEN_WIDTH - 80, 20, 60, 50)
        self.pause_button = ModernButton(pause_button_rect, "⏸️", self._get_font('normal'), (100, 150, 200))
        
        self.end_timer = 0.0
        self.END_DELAY = 2.0

    def _initialize_combat(self):
        """初始化战斗"""
        try:
            enemy_preset = self.game.enemy_data[self.enemy_id]
        except KeyError:
            raise ValueError(f"未找到敌人数据: {self.enemy_id}")
        
        rolled_talents = self._generate_enemy_talents(enemy_preset)
        
        self.enemy = Character(
            id=self.enemy_id, name=enemy_preset["name"],
            talents=rolled_talents, **enemy_preset["stats"]
        )
        
        self.displayed_hp = {'player': self.game.player.hp, 'enemy': self.enemy.hp}
        self.displayed_shield = {'player': self.game.player.shield, 'enemy': self.enemy.shield}
        
        self.game.player.on_enter_combat()
        self.enemy.on_enter_combat()
        
        self.last_update_time = time.time()
        self._trigger_battle_start_events()

    def _generate_enemy_talents(self, enemy_preset):
        """生成敌人天赋"""
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
        """创建天赋实例"""
        if hasattr(Talents, talent_class_name):
            return getattr(Talents, talent_class_name)()
        return None

    def _set_opponents(self):
        """设置对手关系"""
        self.game.player.current_opponent = self.enemy
        self.enemy.current_opponent = self.game.player

    def _trigger_battle_start_events(self):
        """触发战斗开始相关事件"""
        for char in [self.game.player, self.enemy]:
            for talent in char.equipped_talents:
                if talent and hasattr(talent, 'on_battle_start'):
                    talent.on_battle_start(char, char.current_opponent)
            for eq in char.all_equipment:
                if hasattr(eq, 'on_battle_start'):
                    eq.on_battle_start(char)

    def _init_battle_log(self):
        """初始化战斗日志"""
        log_rect = pygame.Rect(40, SCREEN_HEIGHT - 220, SCREEN_WIDTH - 80, 180)
        self.log_renderer = ModernScrollableLog(log_rect, self._get_font('small'), line_height=22)
        battle_logger.register_renderer(self.log_renderer)
        battle_logger.log([(f"⚔️ 战斗开始！遭遇了 ", (200,200,200)), (f"{self.enemy.name}", (255,100,100)), ("！", (200,200,200))])

    def _init_visual_effects(self):
        """初始化视觉效果"""
        for _ in range(30):
            self.battle_particles.append({
                'pos': [random.uniform(0, SCREEN_WIDTH), random.uniform(0, SCREEN_HEIGHT)],
                'size': random.uniform(1, 2.5), 'speed': random.uniform(0.1, 0.4),
                'alpha': random.uniform(10, 40), 'direction': random.uniform(0, 2 * math.pi)
            })

    def handle_event(self, event):
        """处理输入事件"""
        if self._handle_pause_event(event) or self.is_paused: return
        self.log_renderer.handle_event(event)
        self._handle_escape_event(event)

    def _handle_pause_event(self, event):
        """处理暂停事件"""
        pause_triggered = (self.pause_button.handle_event(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_p))
        if pause_triggered:
            self.is_paused = not self.is_paused
            self.pause_button.text = "▶️" if self.is_paused else "⏸️"
            if not self.is_paused: self.last_update_time = time.time()
            return True
        return False

    def _handle_escape_event(self, event):
        """处理ESC退出事件"""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from .confirm_dialog import ConfirmDialog
            from .title import TitleScreen
            def on_confirm_action(): self.game.state_stack = [TitleScreen(self.game)]
            self.game.state_stack.append(ConfirmDialog(self.game, "⚠️ 所有战斗进度都将丢失，确定要返回主菜单吗？", on_confirm_action, title="退出战斗", confirm_text="确认退出", cancel_text="继续战斗"))
            return True
        return False

    def update(self):
        """更新游戏状态"""
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
            self._handle_battle_end(dt)
            return
        
        self._update_characters(dt)
        self._handle_attacks(dt)
        self._check_battle_end()

    def _update_animations(self, dt):
        """更新动画效果"""
        self.glow_animation = (self.glow_animation + dt * 2) % (2 * math.pi)
        if self.shake_intensity > 0: self.shake_intensity = max(0, self.shake_intensity - dt * 200)
        if self.screen_flash > 0: self.screen_flash = max(0, self.screen_flash - dt * 800)
        
        for char_type in ['player', 'enemy']:
            char = self.game.player if char_type == 'player' else self.enemy
            for val_type, disp_val in [('hp', self.displayed_hp), ('shield', self.displayed_shield)]:
                target = getattr(char, val_type)
                current = disp_val[char_type]
                diff = target - current
                if abs(diff) > 0.1: disp_val[char_type] += diff * dt * 8
                else: disp_val[char_type] = target

        for dn in self.damage_numbers[:]:
            dn['pos'][1] -= dt * 60
            dn['alpha'] -= dt * 350
            if dn['alpha'] <= 0: self.damage_numbers.remove(dn)
        
        for p in self.battle_particles:
            p['pos'][0] += math.cos(p['direction']) * p['speed']
            p['pos'][1] += math.sin(p['direction']) * p['speed']
            if p['pos'][0] < 0: p['pos'][0] = SCREEN_WIDTH
            elif p['pos'][0] > SCREEN_WIDTH: p['pos'][0] = 0
            if p['pos'][1] < 0: p['pos'][1] = SCREEN_HEIGHT
            elif p['pos'][1] > SCREEN_HEIGHT: p['pos'][1] = 0

    def _update_characters(self, dt):
        """更新角色状态"""
        self.game.player.update(dt)
        self.enemy.update(dt)

    def _handle_attacks(self, dt):
        """处理攻击逻辑"""
        for attacker, target, type_str in [(self.game.player, self.enemy, 'player'), (self.enemy, self.game.player, 'enemy')]:
            result = attacker.try_attack(target, dt)
            if result:
                log_parts, _, damage_details = result # <-- 接收 damage_details
                self._log_attack_result(result)
                # 把 damage_details 传递下去 -->
                self._create_attack_effects(type_str, damage_details)
    def _log_attack_result(self, attack_result):
        """记录攻击结果"""
        log_parts, extra_logs, _ = attack_result # <--- 加上一个"_"来忽略第三个值
        battle_logger.log(log_parts)
        for extra_log in extra_logs: battle_logger.log([("  └ ", (150,150,150)), (extra_log, (150,150,150))])

    def _create_attack_effects(self, attacker_type, damage_details):
        """创建攻击特效"""
        self.shake_intensity = 10

        # 直接从 damage_details 获取准确信息，不再解析字符串！
        damage_amount = damage_details.get("final_amount", 0)
        is_crit = damage_details.get("is_critical", False)

        # 如果没有造成伤害，就不显示飘字
        if damage_amount <= 0:
            return

        damage_text = str(damage_amount)

        pos = (SCREEN_WIDTH * 0.75, SCREEN_HEIGHT * 0.25) if attacker_type == 'player' else (SCREEN_WIDTH * 0.25, SCREEN_HEIGHT * 0.25)
        self.damage_numbers.append({'pos': [pos[0] + random.uniform(-20, 20), pos[1]], 'alpha': 255, 'text': damage_text, 'is_crit': is_crit})
        
    def _check_battle_end(self):
        """检查战斗是否结束"""
        if not self.battle_ended and (self.enemy.hp <= 0 or self.game.player.hp <= 0):
            self.battle_ended = True; self.end_timer = 0.0

    def _handle_battle_end(self, dt):
        """处理战斗结束逻辑"""
        self.end_timer += dt
        if self.end_timer >= self.END_DELAY:
            if self.enemy.hp <= 0: self._on_victory()
            else: self._on_defeat()

    def _on_victory(self):
        """处理胜利"""
        self._clear_opponents(); battle_logger.unregister_renderer()
        from .dungeon_screen import DungeonScreen
        from .loot import LootScreen
        
        next_story_stage_id = None
        if len(self.game.state_stack) > 1 and isinstance(self.game.state_stack[-2], DungeonScreen):
             if self.origin_id: self.game.state_stack[-2].on_monster_defeated(self.origin_id)
        else:
             next_story_stage_id = self.game.story_data.get(self.game.current_stage, {}).get("next_win")

        self.game.state_stack.pop()
        self.game.state_stack.append(CombatVictoryScreen(self.game, self.enemy, next_story_stage=next_story_stage_id))

    def _on_defeat(self):
        """处理失败"""
        from .title import TitleScreen
        self._clear_opponents(); battle_logger.unregister_renderer()
        self.game.state_stack = [TitleScreen(self.game)]

    def _clear_opponents(self):
        """清除对手关系"""
        self.game.player.current_opponent = None
        if hasattr(self, 'enemy'): self.enemy.current_opponent = None

    def _update_hovers(self):
        """更新鼠标悬停状态"""
        mouse_pos = pygame.mouse.get_pos()
        hovered_object = None
        all_elements = (self.player_ui_elements.get('talents', []) + self.player_ui_elements.get('buffs', []) +
                        self.enemy_ui_elements.get('talents', []) + self.enemy_ui_elements.get('buffs', []))
        for rect, obj in all_elements:
            if rect.collidepoint(mouse_pos):
                hovered_object = obj; break
        self.tooltip_manager.update(hovered_object)

    def draw(self, surface):
        """绘制所有战斗界面元素"""
        # 1. 应用屏幕晃动效果
        screen_offset = (0, 0)
        if self.shake_intensity > 0:
            screen_offset = (random.uniform(-self.shake_intensity, self.shake_intensity),
                             random.uniform(-self.shake_intensity, self.shake_intensity))

        # 为了让晃动不影响固定的UI元素，我们可以在一个临时的surface上绘制游戏世界
        # 但为了简单起见，我们暂时直接在主surface上绘制
        
        # 2. 绘制战斗背景和粒子
        self._draw_battle_background(surface)

        # 3. 绘制角色面板 (我们从 settings.py 导入了它们的位置)
        self._draw_enhanced_character_panels(surface, PLAYER_PANEL_RECT, ENEMY_PANEL_RECT)
        
        # 4. 绘制行动面板和战斗日志
        self._draw_modern_action_panel(surface)
        self.log_renderer.draw(surface)
        
        # 5. 绘制伤害数字等视觉特效
        self._draw_damage_numbers(surface)
        
        # 6. 绘制顶层UI元素 (不受晃动影响)
        self.pause_button.draw(surface)
        self.tooltip_manager.draw(surface)
        
        # 7. 如果游戏暂停，绘制一个半透明的遮罩
        if self.is_paused:
            overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            
            pause_font = self._get_font('large', 48)
            pause_text = pause_font.render("已暂停", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=surface.get_rect().center)
            
            overlay.blit(pause_text, text_rect)
            surface.blit(overlay, (0, 0))

    def _draw_battle_background(self, surface):
        """绘制战斗背景"""
        surface.fill(BG_COLOR)
        for p in self.battle_particles:
            alpha = int(p['alpha'] * (0.5 + 0.5 * math.sin(self.glow_animation + p['pos'][0] * 0.01)))
            p_surf = pygame.Surface((p['size'] * 2, p['size'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (100, 150, 200, alpha), (p['size'], p['size']), p['size'])
            surface.blit(p_surf, (p['pos'][0] - p['size'], p['pos'][1] - p['size']))

    def _draw_enhanced_character_panels(self, surface, player_rect, enemy_rect):
        """绘制增强的角色面板"""
        self.player_ui_elements = self._draw_base_character_panel(surface, self.game.player, player_rect)
        self.enemy_ui_elements = self._draw_base_character_panel(surface, self.enemy, enemy_rect)
        self._draw_animated_hp_bars(surface, player_rect, enemy_rect)

    def _draw_base_character_panel(self, surface, char, rect):
        """只绘制角色面板的背景、文字、天赋和状态，不绘制血条"""
        ui_elements = {'talents': [], 'buffs': []}
        pygame.draw.rect(surface, (25, 30, 50, 220), rect, border_radius=15)
        pygame.draw.rect(surface, (70, 80, 100, 180), rect, 2, border_radius=15)
        
        name_surf = self._get_font('large').render(char.name, True, TEXT_COLOR)
        level_surf = self._get_font('normal').render(f"Lv. {char.level}", True, TEXT_COLOR)
        surface.blit(name_surf, (rect.left + 20, rect.top + 15))
        surface.blit(level_surf, (rect.left + name_surf.get_width() + 30, rect.top + 28))

        stats_text = f"攻击: {int(char.attack)} | 防御: {int(char.defense)} | 攻速: {char.attack_speed:.2f}"
        stats_surf = self._get_font('small').render(stats_text, True, TEXT_COLOR)
        surface.blit(stats_surf, (rect.left + 20, rect.top + 140))

        for list_type, y_offset, color in [('talents', 170, (255, 215, 0)), ('buffs', 200, TEXT_COLOR)]:
            item_list = [t for t in getattr(char, 'equipped_talents' if list_type == 'talents' else 'buffs') if t and not getattr(t, 'hidden', False)]
            if not item_list: continue
            
            x = rect.left + 20
            label_text = "天赋: " if list_type == 'talents' else "状态: "
            label_surf = self._get_font('small').render(label_text, True, color)
            surface.blit(label_surf, (x, rect.top + y_offset)); x += label_surf.get_width()
            
            for i, item in enumerate(item_list):
                item_text = get_display_name(item)
                item_color = color
                if list_type == 'buffs':
                    if item.max_stacks > 1 and item.stacks > 1: item_text += f"({item.stacks})"
                    item_color = (255, 80, 80) if item.is_debuff else (80, 255, 80)
                
                text_surf = self._get_font('small').render(item_text, True, item_color)
                text_rect = text_surf.get_rect(left=x, top=rect.top + y_offset)
                surface.blit(text_surf, text_rect)
                ui_elements[list_type].append((text_rect, item)); x += text_rect.width
                
                if i < len(item_list) - 1:
                    sep_surf = self._get_font('small').render(" | ", True, color)
                    surface.blit(sep_surf, (x, rect.top + y_offset)); x += sep_surf.get_width()
        return ui_elements
        
    def _draw_animated_hp_bars(self, surface, player_rect, enemy_rect):
        """绘制动画血量条和护盾条"""
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
                # 确保护盾条不会画到血条外面
                actual_shield_width = min(shield_width, (hp_rect.width - 4) - hp_width)
                if actual_shield_width > 0:
                    shield_rect = pygame.Rect(hp_rect.x + 2 + hp_width, hp_rect.y + 2, actual_shield_width, hp_rect.height - 4)
                    pygame.draw.rect(surface, SHIELD_BAR_GREY, shield_rect, border_top_right_radius=6, border_bottom_right_radius=6)
            
            pygame.draw.rect(surface, PANEL_BORDER_COLOR, hp_rect, 2, border_radius=8)
            
            hp_text = f"{int(char.hp)}/{int(max_hp)}" + (f" (+{int(char.shield)})" if char.shield > 0 else "")
            font = self._get_font('small', 16)
            text_surface = font.render(hp_text, True, TEXT_COLOR)
            surface.blit(text_surface, text_surface.get_rect(center=hp_rect.center))

    # 请用这个新版本替换 states/combat.py 文件中的 _draw_modern_action_panel 函数
    def _draw_modern_action_panel(self, surface):
        """绘制现代化行动面板 (自适应位置和尺寸)"""
        # --- 核心修改：动态计算位置和大小 ---

        # 1. 获取顶部UI的底部边界 (以敌人面板为基准)
        top_boundary = ENEMY_PANEL_RECT.bottom + 20 # 加上20像素的间距

        # 2. 获取底部日志面板的顶部边界
        log_top = self.log_renderer.rect.top - 20 # 减去20像素的间距

        # 3. 计算可用的垂直空间
        available_height = log_top - top_boundary

        # 4. 定义面板的宽度和最大高度
        panel_width = 240
        # 面板高度不超过200，并且不能超过实际可用空间
        panel_height = min(200, available_height)

        # 5. 计算面板的最终位置 (水平居中，垂直贴近顶部边界)
        panel_x = (SCREEN_WIDTH - panel_width) / 2
        panel_y = top_boundary

        action_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        # --- 后续的绘制逻辑保持不变 ---
        pygame.draw.rect(surface, (25, 30, 50, 220), action_rect, border_radius=12)
        pygame.draw.rect(surface, (70, 80, 100, 160), action_rect, width=2, border_radius=12)

        title_font = self._get_font('normal', 20)
        title_text = title_font.render("⚔️ 战斗行动", True, (255, 215, 0)) 
        title_rect = title_text.get_rect(centerx=action_rect.centerx, top=action_rect.top + 15) 
        surface.blit(title_text, title_rect) 

        line_y = title_rect.bottom + 10
        pygame.draw.line(surface, (70, 80, 100), (action_rect.x + 20, line_y), (action_rect.right - 20, line_y), 2)

        content_rect = pygame.Rect(action_rect.x + 15, line_y + 15, action_rect.width - 30, action_rect.height - 80) 
        content_text = "🎯 自动战斗中...\n\n⏸️ 按P键暂停\n\n💡 技能系统开发中"
        self._draw_wrapped_text(surface, content_text, self._get_font('small', 14), (200, 200, 200), content_rect)
        
    def _draw_wrapped_text(self, surface, text, font, color, rect):
        """绘制自动换行文本"""
        lines = text.split('\n')
        line_height = font.get_height() + 3
        y_offset = rect.y
        for line in lines:
            if y_offset + line_height > rect.bottom: break
            line_surface = font.render(line, True, color)
            surface.blit(line_surface, (rect.x, y_offset))
            y_offset += line_height

    def _draw_damage_numbers(self, surface):
        """绘制伤害数字"""
        for damage_num in self.damage_numbers:
            alpha = max(0, min(255, damage_num['alpha']))
            font_size = 36 if damage_num['is_crit'] else 28
            font = self._get_font('large', font_size)
            color = CRIT_COLOR if damage_num['is_crit'] else (255, 120, 120)
            
            text_surface = font.render(damage_num['text'], True, color)
            text_surface.set_alpha(alpha)
            
            outline_surf = font.render(damage_num['text'], True, (0,0,0))
            outline_surf.set_alpha(alpha * 0.8)
            pos = damage_num['pos']
            for dx, dy in [(-1,-1), (1,-1), (-1,1), (1,1)]:
                surface.blit(outline_surf, (pos[0] + dx, pos[1] + dy))

            surface.blit(text_surface, pos)