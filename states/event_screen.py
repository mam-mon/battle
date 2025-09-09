# states/event_screen.py
import pygame
import random
from .base import BaseState
from ui import Button, draw_panel, draw_text
from settings import *
import Talents # 导入天赋模块

class EventScreen(BaseState):
    def __init__(self, game, event_id, origin_room):
        super().__init__(game)
        self.is_overlay = True
        self.event_data = self.game.event_data[event_id]
        self.origin_room = origin_room
        
        # 界面状态管理：'choosing' (选择中) 或 'showing_result' (显示结果)
        self.view_mode = 'choosing' 
        self.result_text = ""
        
        self._setup_ui()

    def _setup_ui(self):
        # 面板
        panel_w, panel_h = 800, 500
        self.panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) / 2, (SCREEN_HEIGHT - panel_h) / 2, panel_w, panel_h)
        
        # 选项按钮
        self.choice_buttons = []
        btn_w, btn_h = 600, 60
        num_choices = len(self.event_data["choices"])
        start_y = self.panel_rect.bottom - (btn_h + 20) * num_choices - 20
        
        for i, choice in enumerate(self.event_data["choices"]):
            rect = pygame.Rect(self.panel_rect.centerx - btn_w / 2, start_y + i * (btn_h + 20), btn_w, btn_h)
            self.choice_buttons.append(Button(rect, choice["text"], self.game.fonts['normal']))
            
        # “继续”按钮（用于显示结果后）
        self.continue_button = Button(self.choice_buttons[-1].rect, "继续...", self.game.fonts['normal'])

    def handle_event(self, event):
        if self.view_mode == 'choosing':
            for i, button in enumerate(self.choice_buttons):
                if button.handle_event(event):
                    self._process_choice(i)
                    return
        elif self.view_mode == 'showing_result':
            if self.continue_button.handle_event(event):
                self._leave_event()

    # 在 states/event_screen.py 文件中，找到并替换这个函数

    def _process_choice(self, choice_index):
        """处理玩家的选择并计算结果"""
        choice_data = self.event_data["choices"][choice_index]
        outcomes = choice_data["outcomes"]
        
        rand_val = random.random()
        cumulative_chance = 0.0
        selected_outcome = None
        for outcome in outcomes:
            cumulative_chance += outcome.get("chance", 1.0)
            if rand_val < cumulative_chance:
                selected_outcome = outcome
                break
        
        if not selected_outcome: return

        outcome_type = selected_outcome["type"]
        self.result_text = selected_outcome["result_text"]
        
        player = self.game.player
        if outcome_type == "HEAL":
            if selected_outcome["amount"] == "full":
                player.hp = player.max_hp
        
        elif outcome_type == "WEAPON_UPGRADE":
            player.base_attack += 5
            player.attack += 5
        
        elif outcome_type == "WEAPON_CURSE":
            player.base_attack = max(1, player.base_attack - 3)
            player.attack = max(1, player.attack - 3)
            
        # --- 核心修复：使用新的天赋学习和装备逻辑 ---
        elif outcome_type == "GAIN_TALENT":
            talent_class_name = selected_outcome["talent_class_name"]
            if hasattr(Talents, talent_class_name):
                talent_instance = getattr(Talents, talent_class_name)()
                
                # 1. 尝试学习新天赋
                was_new = player.learn_talent(talent_instance)
                
                if was_new:
                    # 2. 如果是新学会的，尝试自动装备它
                    was_equipped = player.equip_talent(talent_instance)
                    if not was_equipped:
                        self.result_text += " (天赋槽已满，请在天赋界面(T)手动装备)"
                else:
                    self.result_text = "你似乎已经领悟过类似的能力了..."

        elif outcome_type == "TRIGGER_COMBAT":
            from .combat import CombatScreen
            enemy_id = selected_outcome["enemy_id"]
            self._leave_event()
            # 剧情战斗不需要 origin_id
            self.game.state_stack.append(CombatScreen(self.game, enemy_id)) 
            return
            
        self.view_mode = 'showing_result'

    # states/event_screen.py (替换这个函数)
    def _leave_event(self):
        """离开事件，更新地图并关闭界面"""
        from .dungeon_screen import DungeonScreen
        self.origin_room.is_cleared = True
        if len(self.game.state_stack) > 1:
            prev_state = self.game.state_stack[-2]
            if isinstance(prev_state, DungeonScreen):
                # --- 核心修复：不再调用不存在的函数 ---
                prev_state.is_returning = True
        self.game.state_stack.pop()


    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
        
        draw_panel(surface, self.panel_rect, self.event_data["title"], self.game.fonts['large'])
        
        if self.view_mode == 'choosing':
            desc_rect = self.panel_rect.inflate(-80, -250)
            desc_rect.top = self.panel_rect.top + 100
            draw_text(surface, self.event_data["description"], self.game.fonts['normal'], TEXT_COLOR, desc_rect)
            for button in self.choice_buttons:
                button.draw(surface)
        elif self.view_mode == 'showing_result':
            result_rect = self.panel_rect.inflate(-80, -250)
            result_rect.top = self.panel_rect.top + 150
            draw_text(surface, self.result_text, self.game.fonts['normal'], HOVER_COLOR, result_rect)
            self.continue_button.draw(surface)