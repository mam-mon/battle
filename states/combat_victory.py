# 文件: states/combat_victory.py (现代化重写版本)

import pygame
import math
import random

import Equips
from .base import BaseState
from ui import draw_character_panel, Button, draw_text_with_outline
from settings import *

class CombatVictoryScreen(BaseState):
    """现代化战斗胜利界面 - 具备庆祝动画和视觉特效"""
    
# states/combat_victory.py (替换 __init__ 函数)

    def __init__(self, game, final_enemy, next_story_stage=None):
        super().__init__(game)
        self.final_enemy = final_enemy
        self.next_story_stage = next_story_stage # <-- 传递剧情信息

        # --- 动画与状态变量 ---
        self.entrance_animation = 0
        self.victory_glow = 0
        self.fireworks = []
        self.sparkles = []
        self.victory_banner_y = -100
        self.stats_reveal_timer = 0
        self.button_pulse = 0
        
        # --- 新增：奖励与动画状态 ---
        self.exp_messages = []
        self.loot_messages = []
        self.level_up_events = []
        self.exp_start_percent = 0
        self.old_level = self.game.player.level
        self.exp_animation_progress = 0.0 # 0.0 到 1.0 的动画进度
        self.level_up_animation_progress = 0.0
        self.rewards_processed = False # 确保奖励只结算一次
        
        self._init_ui()
        self._create_celebration_effects()
        
        # --- 在最后调用奖励结算 ---
        self._process_rewards()
        
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
        # 现代化继续按钮
        button_width, button_height = 300, 60
        button_x = SCREEN_WIDTH // 2 - button_width // 2
        button_y = SCREEN_HEIGHT - 120
        
        self.continue_button = VictoryButton(
            pygame.Rect(button_x, button_y, button_width, button_height),
            "🎉 进入结算",
            self._get_font('normal'),
            (100, 255, 100)
        )
        
        # 胜利信息面板
        panel_width = 600
        panel_height = 250
        self.victory_panel_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - panel_width // 2,
            SCREEN_HEIGHT // 2 - panel_height // 2,
            panel_width,
            panel_height
        )

    def _process_rewards(self):
        """处理所有战斗后的奖励结算"""
        self.exp_messages = []
        self.level_up_events = [] # <-- 新增：用来存储升级信息的列表

        # --- 经验值结算 ---
        enemy_preset = self.game.enemy_data.get(self.final_enemy.id, {})
        exp_gain = enemy_preset.get("exp_reward", 0)

        # 在这里，我们先记录旧的等级和经验信息，用于动画
        self.exp_start_percent = self.game.player.exp / self.game.player.exp_to_next_level
        self.old_level = self.game.player.level

        # 调用玩家的 add_exp，它现在会返回升级信息
        original_level = self.game.player.level
        self.exp_messages = self.game.player.add_exp(exp_gain)

        # 检查是否升级
        if self.game.player.level > original_level:
            # 记录每一次升级的详细信息
            for i in range(original_level + 1, self.game.player.level + 1):
                self.level_up_events.append({
                    "level": i,
                    "hp_bonus": 10, # 根据你 level_up 函数的定义 [cite: 102, 103]
                    "atk_bonus": 2,  # [cite: 102, 103]
                    "def_bonus": 1   # [cite: 102, 103]
                })

        # --- 战利品结算 ---
        self.loot_messages = self._generate_loot()

        # 自动存档
        self.game.save_to_slot(0)

    def _generate_loot(self):
        # 这个函数几乎可以原封不动地从 loot.py 复制过来
        messages = []
        found_any_loot = False

        # Part 1: 装备掉落
        equipment_drops = self.game.loot_data.get(self.final_enemy.id, [])
        if equipment_drops:
            equipment_header_added = False
            for drop_info in equipment_drops:
                if random.random() < drop_info.get("chance", 1.0):
                    if not equipment_header_added:
                        messages.append("--- 战利品 ---")
                        equipment_header_added = True
                    found_any_loot = True
                    item_class_name = drop_info["item_class_name"]
                    try:
                        item_class = getattr(Equips, item_class_name)
                        new_item = item_class()
                        display_name = getattr(new_item, 'display_name', item_class_name)
                        # 我们不再直接打印 feedback，而是格式化后加入列表
                        feedback = self.game.player.pickup_item(new_item)
                        if "放入你的背包" in feedback:
                            messages.append(f"获得了装备：{display_name}！")
                        else:
                            messages.append(feedback) # 处理转化为金币的情况
                    except AttributeError:
                        messages.append(f"错误：未找到物品 {item_class_name}。")

        # Part 2: 天赋掉落
        import Talents
        if self.final_enemy.equipped_talents:
            talent_header_added = False
            for possessed_talent in self.final_enemy.equipped_talents:
                if possessed_talent and random.random() < 0.15: # 15% 掉落率
                    was_new = self.game.player.learn_talent(possessed_talent)
                    if was_new:
                        if not talent_header_added:
                            messages.append("--- 能力领悟 ---")
                            talent_header_added = True
                        found_any_loot = True
                        messages.append(f"你领悟了「{possessed_talent.display_name}」！")

        if not found_any_loot:
            messages.append("敌人没有留下任何有价值的东西。")

        return messages

    def _create_celebration_effects(self):
        """创建庆祝特效"""
        # 创建烟花效果
        for _ in range(8):
            firework = {
                'x': random.uniform(SCREEN_WIDTH * 0.2, SCREEN_WIDTH * 0.8),
                'y': random.uniform(SCREEN_HEIGHT * 0.2, SCREEN_HEIGHT * 0.6),
                'particles': [],
                'exploded': False,
                'timer': random.uniform(0, 2)
            }
            self.fireworks.append(firework)
        
        # 创建闪光粒子
        for _ in range(30):
            sparkle = {
                'x': random.uniform(0, SCREEN_WIDTH),
                'y': random.uniform(0, SCREEN_HEIGHT),
                'size': random.uniform(2, 5),
                'alpha': random.uniform(100, 255),
                'life': random.uniform(1, 3),
                'max_life': 3
            }
            self.sparkles.append(sparkle)

    def handle_event(self, event):
        """处理输入事件"""
        # 等待入场动画完成
        if self.entrance_animation < 1.0:
            return
            
        if self._should_continue(event):
            self._proceed_to_loot()

    def _should_continue(self, event):
        """检查是否应该继续"""
        return (
            self.continue_button.handle_event(event) or
            (event.type == pygame.KEYDOWN and 
             event.key in [pygame.K_RETURN, pygame.K_SPACE])
        )

    def _proceed_to_loot(self):
        """进入战利品界面"""
        from .loot import LootScreen
        self.game.state_stack.pop()
        self.game.state_stack.append(LootScreen(self.game, self.final_enemy))

    def update(self, dt=0):
        """更新所有动画"""
        current_time = pygame.time.get_ticks()
        if not hasattr(self, '_last_time'): self._last_time = current_time
        dt_ms = current_time - self._last_time
        self._last_time = current_time
        dt_sec = dt_ms / 1000.0
        
        # --- 主动画更新 ---
        self.entrance_animation = min(1.0, self.entrance_animation + dt_sec * 1.5)
        self.victory_glow = (self.victory_glow + dt_sec * 3) % (2 * math.pi)
        if self.victory_banner_y < 80: self.victory_banner_y += dt_sec * 300
        self.button_pulse = (self.button_pulse + dt_sec * 2) % (2 * math.pi)
        self._update_fireworks(dt_sec)
        self._update_sparkles(dt_sec)
        
        # --- 新增：奖励动画更新 ---
        if self.entrance_animation >= 1.0: # 等待入场动画结束
            # 1. 经验条动画
            if self.exp_animation_progress < 1.0:
                self.exp_animation_progress = min(1.0, self.exp_animation_progress + dt_sec * 0.5)
            # 2. 等级提升动画 (在经验条动画完成后)
            elif self.level_up_events and self.level_up_animation_progress < 1.0:
                self.level_up_animation_progress = min(1.0, self.level_up_animation_progress + dt_sec * 0.8)
                
    def _update_fireworks(self, dt):
        """更新烟花效果"""
        for firework in self.fireworks:
            if not firework['exploded']:
                firework['timer'] -= dt
                if firework['timer'] <= 0:
                    # 爆炸
                    firework['exploded'] = True
                    for _ in range(15):
                        particle = {
                            'x': firework['x'],
                            'y': firework['y'],
                            'vx': random.uniform(-100, 100),
                            'vy': random.uniform(-100, 100),
                            'life': random.uniform(1, 2),
                            'max_life': 2,
                            'color': random.choice([(255, 100, 100), (100, 255, 100), 
                                                   (100, 100, 255), (255, 255, 100)])
                        }
                        firework['particles'].append(particle)
            
            # 更新粒子
            for particle in firework['particles'][:]:
                particle['x'] += particle['vx'] * dt
                particle['y'] += particle['vy'] * dt
                particle['vy'] += 200 * dt  # 重力
                particle['life'] -= dt
                if particle['life'] <= 0:
                    firework['particles'].remove(particle)

    def _update_sparkles(self, dt):
        """更新闪光粒子"""
        for sparkle in self.sparkles[:]:
            sparkle['life'] -= dt
            sparkle['alpha'] = int(255 * (sparkle['life'] / sparkle['max_life']))
            if sparkle['life'] <= 0:
                # 重新生成闪光
                sparkle['x'] = random.uniform(0, SCREEN_WIDTH)
                sparkle['y'] = random.uniform(0, SCREEN_HEIGHT)
                sparkle['life'] = sparkle['max_life']
                sparkle['alpha'] = random.uniform(100, 255)

    def draw(self, surface):
        """绘制所有界面元素"""
        self._draw_victory_background(surface)
        self._draw_background_effects(surface)
        self._draw_victory_banner(surface)
        
        # --- 核心改动：不再绘制角色面板，而是绘制奖励面板 ---
        self._draw_rewards_panel(surface)
        
        self._draw_continue_button(surface)
        self._draw_foreground_effects(surface)
        self.update() # 确保动画持续更新

    def _draw_rewards_panel(self, surface):
        """绘制集成了所有奖励信息的中央面板"""
        # 使用 entrance_animation 实现面板的缩放淡入效果
        if self.entrance_animation < 1.0:
            scale = 0.8 + 0.2 * self.entrance_animation
            alpha = int(255 * self.entrance_animation)
            panel_w = int(800 * scale)
            panel_h = int(500 * scale)
        else:
            alpha = 255
            panel_w, panel_h = 800, 500
            
        panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)

        # 绘制现代化面板背景
        panel_surf = pygame.Surface(panel_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, (25, 30, 50, 240), panel_surf.get_rect(), border_radius=15)
        pygame.draw.rect(panel_surf, (255, 215, 0, 200), panel_surf.get_rect(), width=3, border_radius=15)
        
        # --- 在面板上绘制所有内容 ---
        self._draw_rewards_title(panel_surf)
        self._draw_exp_bar(panel_surf)
        self._draw_loot_items(panel_surf)
        
        # --- 等级提升特效 ---
        if self.level_up_events and self.exp_animation_progress >= 1.0:
            self._draw_level_up_effect(surface) # 在主 surface 上绘制，实现全屏特效

        panel_surf.set_alpha(alpha)
        surface.blit(panel_surf, panel_rect.topleft)

    def _draw_rewards_title(self, surface):
        """在面板上绘制标题"""
        title_font = self._get_font('large', 32)
        title_text = title_font.render("胜利结算", True, (255, 215, 0))
        title_rect = title_text.get_rect(centerx=surface.get_width() // 2, top=25)
        surface.blit(title_text, title_rect)
        line_y = title_rect.bottom + 15
        pygame.draw.line(surface, (100, 120, 150), (40, line_y), (surface.get_width() - 40, line_y), 2)

    def _draw_exp_bar(self, surface):
        """在面板上绘制经验条和等级信息"""
        bar_rect = pygame.Rect(40, 90, surface.get_width() - 80, 40)
        
        # 等级文本
        level_font = self._get_font('normal', 22)
        level_text = f"等级 {self.old_level}"
        level_surf = level_font.render(level_text, True, TEXT_COLOR)
        surface.blit(level_surf, (bar_rect.x, bar_rect.y - 30))

        # 经验条背景
        pygame.draw.rect(surface, (10, 20, 30), bar_rect, border_radius=8)
        
        # 经验条动画
        start_w = bar_rect.width * self.exp_start_percent
        target_w = bar_rect.width * (self.game.player.exp / self.game.player.exp_to_next_level) if self.game.player.exp_to_next_level > 0 else 0
        
        if self.level_up_events:
            final_w_before_levelup = bar_rect.width
            total_anim_width = (final_w_before_levelup - start_w) + target_w
            anim_split_point = (final_w_before_levelup - start_w) / total_anim_width if total_anim_width > 0 else 1.0
            
            if self.exp_animation_progress < anim_split_point:
                progress = self.exp_animation_progress / anim_split_point if anim_split_point > 0 else 1.0
                current_w = start_w + (final_w_before_levelup - start_w) * progress
            else:
                ### --- 关键修复：在这里添加一个安全检查 --- ###
                denominator = 1 - anim_split_point
                if denominator <= 0:
                    progress = 1.0 # 如果没有动画的第二部分，则直接视为完成
                else:
                    progress = (self.exp_animation_progress - anim_split_point) / denominator
                ### --- 修复结束 --- ###

                current_w = target_w * progress
                level_text = f"等级 {self.game.player.level}"
                level_surf = level_font.render(level_text, True, TEXT_COLOR)
                surface.blit(level_surf, (bar_rect.x, bar_rect.y - 30))
        else:
            current_w = start_w + (target_w - start_w) * self.exp_animation_progress

        # 绘制经验条前景
        if current_w > 0:
            xp_fill_rect = pygame.Rect(bar_rect.x + 2, bar_rect.y + 2, current_w - 4, bar_rect.height - 4)
            pygame.draw.rect(surface, XP_BAR_COLOR, xp_fill_rect, border_radius=6)
        
        # 经验值文本
        exp_font = self._get_font('small', 16)
        exp_text = f"{self.game.player.exp} / {self.game.player.exp_to_next_level}"
        exp_surf = exp_font.render(exp_text, True, TEXT_COLOR)
        surface.blit(exp_surf, exp_surf.get_rect(center=bar_rect.center))
        pygame.draw.rect(surface, PANEL_BORDER_COLOR, bar_rect, 2, border_radius=8)

    def _draw_loot_items(self, surface):
        """在面板上绘制战利品列表"""
        list_rect = pygame.Rect(40, 160, surface.get_width() - 80, surface.get_height() - 240)
        font = self._get_font('normal', 18)
        line_height = 35
        y_pos = list_rect.y
        
        # 使用 exp_messages 和 loot_messages 绘制
        all_messages = self.exp_messages + self.loot_messages
        
        for i, line in enumerate(all_messages):
            # 使用动画逐行显示
            reveal_progress = max(0, min(1, (self.exp_animation_progress * 2 - i * 0.2)))
            if reveal_progress <= 0: continue
                
            alpha = int(255 * reveal_progress)
            offset_x = (1 - reveal_progress) * 50
            
            # 根据内容决定颜色
            color = TEXT_COLOR
            if "获得了装备" in line or "领悟了" in line:
                color = (255, 215, 0) # 金色
            elif "等级提升" in line:
                color = (100, 255, 100) # 绿色
            
            line_surf = font.render(line, True, color)
            line_surf.set_alpha(alpha)
            surface.blit(line_surf, (list_rect.x + offset_x, y_pos))
            y_pos += line_height

    def _draw_level_up_effect(self, surface):
        """绘制全屏的等级提升特效"""
        progress = self.level_up_animation_progress
        
        # 1. 闪光背景
        flash_alpha = int(math.sin(progress * math.pi) * 150)
        flash_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        flash_surf.fill((255, 255, 150, flash_alpha))
        surface.blit(flash_surf, (0, 0))
        
        # 2. "LEVEL UP" 文字
        scale = 1 + math.sin(progress * math.pi) * 0.2
        font_size = int(80 * scale)
        font = self._get_font('large', font_size)
        
        text_surf = font.render("等级提升!", True, (255, 255, 255))
        text_alpha = int(math.sin(progress * math.pi) * 255)
        text_surf.set_alpha(text_alpha)
        
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 100))
        draw_text_with_outline(surface, "等级提升!", font, (255, 255, 100), (100, 80, 0), text_rect.center, 3)

        # 3. 属性增长提示
        stats_font = self._get_font('normal', 24)
        stat_y_start = text_rect.bottom + 20
        for i, event in enumerate(self.level_up_events):
            stat_text = f"生命+{event['hp_bonus']} 攻击+{event['atk_bonus']} 防御+{event['def_bonus']}"
            stat_surf = stats_font.render(stat_text, True, (100, 255, 100))
            stat_surf.set_alpha(text_alpha)
            stat_rect = stat_surf.get_rect(centerx=SCREEN_WIDTH/2, top=stat_y_start + i * 30)
            surface.blit(stat_surf, stat_rect)
            
    def _proceed_to_loot(self):
        """修改：不再进入LootScreen，而是根据情况返回或进入下一剧情"""
        if self.next_story_stage:
            from .story import StoryScreen
            self.game.current_stage = self.next_story_stage
            # 清理状态栈，准备进入新剧情
            self.game.state_stack.pop() # 弹出自己
            if self.game.state_stack and isinstance(self.game.state_stack[-1], StoryScreen):
                self.game.state_stack.pop() # 如果上一个是剧情，也弹出
            self.game.state_stack.append(StoryScreen(self.game))
        else:
            self.game.state_stack.pop() # 如果没有后续剧情（比如在地牢里），直接返回
            
    # (其余的辅助绘制函数如 _draw_victory_background, _draw_fireworks 等保持不变)
    # (VictoryButton 类也保持不变)
    
    def _draw_victory_background(self, surface):
        """绘制胜利背景"""
        # 金色渐变背景
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(50 + progress * 30)
            g = int(40 + progress * 50)
            b = int(20 + progress * 20)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    def _draw_background_effects(self, surface):
        """绘制背景特效"""
        # 闪光粒子
        for sparkle in self.sparkles:
            if sparkle['alpha'] > 0:
                sparkle_surface = pygame.Surface((sparkle['size'] * 2, sparkle['size'] * 2), pygame.SRCALPHA)
                color = (255, 255, 200, sparkle['alpha'])
                pygame.draw.circle(sparkle_surface, color, 
                                 (sparkle['size'], sparkle['size']), sparkle['size'])
                surface.blit(sparkle_surface, (sparkle['x'] - sparkle['size'], 
                                             sparkle['y'] - sparkle['size']))

    def _draw_victory_banner(self, surface):
        """绘制胜利横幅"""
        banner_rect = pygame.Rect(0, self.victory_banner_y, SCREEN_WIDTH, 120)
        
        # 横幅背景
        banner_surface = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
        pygame.draw.rect(banner_surface, (255, 215, 0, 200), (0, 0, SCREEN_WIDTH, 120))
        pygame.draw.rect(banner_surface, (255, 255, 100, 100), (0, 0, SCREEN_WIDTH, 120), width=5)
        
        # 发光效果
        glow_intensity = int((math.sin(self.victory_glow) + 1) * 30 + 20)
        glow_surface = pygame.Surface((SCREEN_WIDTH, 120), pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (255, 255, 255, glow_intensity), (0, 0, SCREEN_WIDTH, 120))
        banner_surface.blit(glow_surface, (0, 0))
        
        surface.blit(banner_surface, (0, self.victory_banner_y))
        
        # 胜利文字
        victory_font = self._get_font('large', 48)
        victory_text = victory_font.render("🏆 战斗胜利！ 🏆", True, (255, 255, 255))
        victory_rect = victory_text.get_rect(center=(SCREEN_WIDTH // 2, self.victory_banner_y + 60))
        
        # 文字阴影
        shadow_surface = victory_font.render("🏆 战斗胜利！ 🏆", True, (100, 50, 0))
        shadow_rect = shadow_surface.get_rect(center=(SCREEN_WIDTH // 2 + 3, self.victory_banner_y + 63))
        surface.blit(shadow_surface, shadow_rect)
        surface.blit(victory_text, victory_rect)

    def _draw_character_panels(self, surface):
        """绘制角色面板"""
        # 稍微缩小面板以腾出空间给特效
        player_rect = pygame.Rect(50, 220, 300, 200)
        enemy_rect = pygame.Rect(SCREEN_WIDTH - 350, 220, 300, 200)
        
        draw_character_panel(surface, self.game.player, player_rect, self.game.fonts)
        draw_character_panel(surface, self.final_enemy, enemy_rect, self.game.fonts)

    def _draw_victory_panel(self, surface):
        """绘制胜利信息面板"""
        # 现代化面板背景
        panel_rect = self.victory_panel_rect
        pygame.draw.rect(surface, (25, 30, 50, 240), panel_rect, border_radius=15)
        pygame.draw.rect(surface, (255, 215, 0, 200), panel_rect, width=3, border_radius=15)
        
        # 内发光
        glow_rect = panel_rect.inflate(-6, -6)
        pygame.draw.rect(surface, (255, 255, 255, 30), glow_rect, width=2, border_radius=12)
        
        # 标题
        title_font = self._get_font('large', 32)
        title_text = title_font.render("胜利统计", True, (255, 215, 0))
        title_rect = title_text.get_rect(centerx=panel_rect.centerx, top=panel_rect.top + 20)
        surface.blit(title_text, title_rect)
        
        # 分割线
        line_y = title_rect.bottom + 15
        pygame.draw.line(surface, (100, 120, 150), 
                        (panel_rect.x + 30, line_y), (panel_rect.right - 30, line_y), 2)
        
        # 统计信息（逐步显示）
        stats_rect = pygame.Rect(panel_rect.x + 40, line_y + 20, 
                                panel_rect.width - 80, panel_rect.height - 100)
        self._draw_victory_stats(surface, stats_rect)

    def _draw_victory_stats(self, surface, rect):
        """绘制胜利统计"""
        font = self._get_font('normal', 18)
        stats = [
            f"🎯 击败了强敌：{self.final_enemy.name}",
            f"⚔️ 剩余生命值：{int(self.game.player.hp)}/{int(self.game.player.max_hp)}",
            f"💰 即将获得丰厚奖励！",
            f"🌟 经验值和装备等你收集"
        ]
        
        line_height = 35
        start_y = rect.y
        
        for i, stat in enumerate(stats):
            # 逐步显示效果
            reveal_progress = max(0, min(1, (self.stats_reveal_timer - i * 0.5) / 0.5))
            if reveal_progress <= 0:
                continue
                
            # 滑入效果
            offset_x = (1 - reveal_progress) * 100
            alpha = int(255 * reveal_progress)
            
            y_pos = start_y + i * line_height
            text_surface = font.render(stat, True, (220, 220, 220))
            text_surface.set_alpha(alpha)
            surface.blit(text_surface, (rect.x + offset_x, y_pos))

    def _draw_continue_button(self, surface):
        """绘制继续按钮"""
        if self.entrance_animation < 1.0:
            return
            
        button_rect = self.continue_button.rect
        
        # 脉冲效果
        pulse = math.sin(self.button_pulse) * 0.1 + 1
        scaled_size = (int(button_rect.width * pulse), int(button_rect.height * pulse))
        scaled_rect = pygame.Rect(0, 0, *scaled_size)
        scaled_rect.center = button_rect.center
        
        # 按钮背景
        bg_color = (100, 255, 100, 200)
        border_color = (255, 255, 255)
        
        pygame.draw.rect(surface, bg_color, scaled_rect, border_radius=12)
        pygame.draw.rect(surface, border_color, scaled_rect, width=3, border_radius=12)
        
        # 发光效果
        glow_intensity = int((math.sin(self.victory_glow) + 1) * 25 + 15)
        glow_surface = pygame.Surface(scaled_rect.size, pygame.SRCALPHA)
        pygame.draw.rect(glow_surface, (100, 255, 100, glow_intensity), 
                       (0, 0, scaled_rect.width, scaled_rect.height), border_radius=12)
        surface.blit(glow_surface, scaled_rect.topleft)
        
        # 按钮文字
        font = self._get_font('normal', 20)
        text_surface = font.render(self.continue_button.text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=scaled_rect.center)
        surface.blit(text_surface, text_rect)

    def _draw_foreground_effects(self, surface):
        """绘制前景特效"""
        # 烟花
        for firework in self.fireworks:
            for particle in firework['particles']:
                if particle['life'] > 0:
                    alpha = int(255 * (particle['life'] / particle['max_life']))
                    color = (*particle['color'], alpha)
                    
                    particle_surface = pygame.Surface((6, 6), pygame.SRCALPHA)
                    pygame.draw.circle(particle_surface, color, (3, 3), 3)
                    surface.blit(particle_surface, (particle['x'] - 3, particle['y'] - 3))


class VictoryButton:
    """胜利界面专用按钮"""
    def __init__(self, rect, text, font, accent_color):
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