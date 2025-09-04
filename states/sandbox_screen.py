# 文件: states/sandbox_screen.py (新文件)

import pygame
import inspect
from .base import BaseState
from ui import Button, draw_panel, draw_text
from settings import *
from Character import Character
import Equips
import Talents

class SandboxScreen(BaseState):
# 文件: states/sandbox_screen.py (替换这个函数)

    def __init__(self, game):
        super().__init__(game)
        
        # --- 核心修改：同样使用 PLAYER_BASE_STATS 来创建测试角色 ---
        self.sandbox_player = Character(
            "测试英雄",
            **PLAYER_BASE_STATS # <-- 使用我们定义的标准属性
        )
        
        # 2. 解锁所有装备到背包
        all_equipment_classes = [cls for name, cls in inspect.getmembers(Equips, inspect.isclass) if issubclass(cls, Equips.Equipment) and cls is not Equips.Equipment]
        for eq_class in all_equipment_classes:
            self.sandbox_player.backpack.append(eq_class())
            
        # 3. 解锁所有天赋
        all_talent_classes = [cls for name, cls in inspect.getmembers(Talents, inspect.isclass) if issubclass(cls, Talents.Talent) and cls is not Talents.Talent]
        for talent_class in all_talent_classes:
            self.sandbox_player.learn_talent(talent_class())

        # 4. 设置UI
        self.enemy_ids = list(self.game.enemy_data.keys())
        self.selected_enemy_index = 0
        
        self._setup_ui()

# 文件: states/sandbox_screen.py (替换这三个函数)

    def _setup_ui(self):
        # 按钮定义
        self.backpack_button = Button((100, 150, 300, 60), "配置背包", self.game.fonts['normal'])
        self.talents_button = Button((100, 230, 300, 60), "配置天赋", self.game.fonts['normal'])
        
        # --- 新增：等级控制按钮 ---
        level_y = self.talents_button.rect.bottom + 40
        self.level_down_button = Button((100, level_y, 60, 60), "-", self.game.fonts['large'])
        self.level_up_button = Button((100 + 240, level_y, 60, 60), "+", self.game.fonts['large'])
        # --- 新增结束 ---

        self.start_combat_button = Button((100, 450, 300, 80), "开始战斗", self.game.fonts['large'])
        self.back_button = Button((20, 20, 100, 50), "返回", self.game.fonts['small'])

        # 敌人选择器
        self.prev_enemy_button = Button((SCREEN_WIDTH - 450, 250, 50, 50), "<", self.game.fonts['normal'])
        self.next_enemy_button = Button((SCREEN_WIDTH - 100, 250, 50, 50), ">", self.game.fonts['normal'])
        
    def handle_event(self, event):
        from .backpack import BackpackScreen
        from .talents_screen import TalentsScreen
        from .combat import CombatScreen

        if self.back_button.handle_event(event):
            self.game.state_stack.pop()
            return
            
        if self.backpack_button.handle_event(event):
            self.game.state_stack.append(BackpackScreen(self.game, player_override=self.sandbox_player))
            return
            
        if self.talents_button.handle_event(event):
            self.game.state_stack.append(TalentsScreen(self.game, player_override=self.sandbox_player))
            return

        # --- 新增：处理等级控制按钮的点击事件 ---
        if self.level_up_button.handle_event(event):
            self.sandbox_player.gain_level()
            return
        
        if self.level_down_button.handle_event(event):
            self.sandbox_player.lose_level()
            return
        # --- 新增结束 ---
            
        if self.prev_enemy_button.handle_event(event):
            self.selected_enemy_index = (self.selected_enemy_index - 1 + len(self.enemy_ids)) % len(self.enemy_ids)
        
        if self.next_enemy_button.handle_event(event):
            self.selected_enemy_index = (self.selected_enemy_index + 1) % len(self.enemy_ids)

        if self.start_combat_button.handle_event(event):
            original_player = self.game.player
            self.game.player = self.sandbox_player
            selected_enemy_id = self.enemy_ids[self.selected_enemy_index]
            self.game.state_stack.append(CombatScreen(self.game, selected_enemy_id))
            return

    def draw(self, surface):
        surface.fill(BG_COLOR)
        draw_panel(surface, pygame.Rect(50, 50, 400, SCREEN_HEIGHT - 100), "配置角色", self.game.fonts['large'])
        draw_panel(surface, pygame.Rect(SCREEN_WIDTH - 500, 50, 450, SCREEN_HEIGHT - 100), "选择敌人", self.game.fonts['large'])

        # 绘制按钮
        self.backpack_button.draw(surface)
        self.talents_button.draw(surface)
        self.start_combat_button.draw(surface)
        self.back_button.draw(surface)
        self.prev_enemy_button.draw(surface)
        self.next_enemy_button.draw(surface)
        
        # --- 新增：绘制等级控制器 ---
        self.level_up_button.draw(surface)
        self.level_down_button.draw(surface)
        
        # 绘制当前等级文本
        level_text = f"等级: {self.sandbox_player.level}"
        level_rect = pygame.Rect(self.level_down_button.rect.right, self.level_down_button.rect.top, 
                                 self.level_up_button.rect.left - self.level_down_button.rect.right, 60)
        draw_text(surface, level_text, self.game.fonts['large'], TEXT_COLOR, level_rect)
        # --- 新增结束 ---

        # 绘制当前选择的敌人
        selected_enemy_id = self.enemy_ids[self.selected_enemy_index]
        enemy_name = self.game.enemy_data[selected_enemy_id]['name']
        enemy_rect = pygame.Rect(self.prev_enemy_button.rect.right, self.prev_enemy_button.rect.top, 
                                 self.next_enemy_button.rect.left - self.prev_enemy_button.rect.right, 50)
        draw_text(surface, enemy_name, self.game.fonts['large'], TEXT_COLOR, enemy_rect)