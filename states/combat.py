# states/combat.py
import pygame
import time
from .base import BaseState
from ui import draw_health_bar, draw_text, get_display_name
from settings import *
from Character import Character

class CombatScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self._initialize_combat()

    def _initialize_combat(self):
        stage_data = self.game.story_data[self.game.current_stage]
        enemy_id = stage_data["enemy_id"]
        enemy_preset = self.game.enemy_data[enemy_id]
        self.enemy = Character(name=enemy_preset["name"], **enemy_preset["stats"])
        
        for eq in self.game.player.all_equipment: eq.on_battle_start(self.game.player)
        for eq in self.enemy.all_equipment: eq.on_battle_start(self.enemy)
        self.game.player.update(0)
        self.enemy.update(0)
        
        self.last_update_time = time.time()
        self.latest_action = "战斗开始！"

    def update(self):
        from states.combat_victory import CombatVictoryScreen # <-- Import 移至此处
        from states.title import TitleScreen # <-- Import 移至此处

        now = time.time()
        dt = now - self.last_update_time
        self.last_update_time = now

        self.game.player.update(dt)
        self.enemy.update(dt)

        player_res = self.game.player.try_attack(self.enemy, dt)
        if player_res: self.latest_action = player_res[0]
        
        enemy_res = self.enemy.try_attack(self.game.player, dt)
        if enemy_res: self.latest_action = enemy_res[0]

        if self.game.player.hp <= 0 or self.enemy.hp <= 0:
            winner = self.game.player if self.game.player.hp > 0 else self.enemy
            
            self.game.state_stack.pop()
            if winner is self.game.player:
                self.game.state_stack.append(CombatVictoryScreen(self.game, self.enemy))
            else:
                self.game.state_stack = [TitleScreen(self.game)]

    # In states/combat.py -> inside CombatScreen.draw

    def draw(self, surface):
        surface.fill(BG_COLOR)
        player_hp_rect = pygame.Rect(50, 50, 500, 40)
        draw_health_bar(surface, player_hp_rect, self.game.player)
        enemy_hp_rect = pygame.Rect(SCREEN_WIDTH - 550, 50, 500, 40)
        draw_health_bar(surface, enemy_hp_rect, self.enemy)

        # --- 新增：绘制Buffs ---
        player_buff_rect = pygame.Rect(50, 100, 500, 30)
        self.draw_buffs(surface, self.game.player, player_buff_rect)
        
        enemy_buff_rect = pygame.Rect(SCREEN_WIDTH - 550, 100, 500, 30)
        self.draw_buffs(surface, self.enemy, enemy_buff_rect)
        # --- 结束新增 ---

        action_log_rect = pygame.Rect(0, SCREEN_HEIGHT - 80, SCREEN_WIDTH, 50)
        draw_text(surface, f"最新行动: {self.latest_action}", self.game.fonts['normal'], TEXT_COLOR, action_log_rect)

    def draw_buffs(self, surface, char, rect):
        """在指定区域绘制角色的Buff列表"""
        buff_texts = []
        for buff in char.buffs:
            if getattr(buff, "hidden", False): continue
            
            name = get_display_name(buff)
            if hasattr(buff, 'stacks') and buff.stacks > 1:
                buff_texts.append(f"{name}({buff.stacks})")
            else:
                buff_texts.append(name)
        
        full_text = " ".join(buff_texts)
        draw_text(surface, full_text, self.game.fonts['small'], (100, 200, 255), rect) # 用蓝色显示Buff

    def handle_event(self, event):
        from .confirm_dialog import ConfirmDialog # 局部导入
        from .title import TitleScreen

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            # 定义“确认”后执行的操作：清空状态栈，返回主菜单
            def on_confirm_action():
                self.game.state_stack = [TitleScreen(self.game)]
            
            # 创建并压入确认对话框状态
            confirm_dialog = ConfirmDialog(
                self.game, 
                "所有战斗进度都将丢失，确定要返回主菜单吗？",
                on_confirm_action
            )
            self.game.state_stack.append(confirm_dialog)