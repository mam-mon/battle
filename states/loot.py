# states/loot.py
import pygame
from states.base import BaseState
from ui import draw_panel, draw_text
from settings import *
import random
import Equips

class LootScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self._process_rewards()

    def _process_rewards(self):
        stage_data = self.game.story_data[self.game.current_stage]
        enemy_id = stage_data["enemy_id"]
        enemy_preset = self.game.enemy_data[enemy_id]
        
        self.exp_messages = self.game.player.add_exp(enemy_preset.get("exp_reward", 0))
        self.loot_messages = self._generate_loot(enemy_id)
        
        next_stage = stage_data["next_win"]
        self.game.save_to_slot(0) # 自动存档
        self.game.current_stage = next_stage

    def _generate_loot(self, enemy_id):
        possible_drops = self.game.loot_data.get(enemy_id, [])
        messages = ["战利品结算："]
        found_loot = False
        for drop_info in possible_drops:
            if random.random() < drop_info["chance"]:
                found_loot = True
                item_class_name = drop_info["item_class_name"]
                try:
                    item_class = getattr(Equips, item_class_name)
                    new_item = item_class()
                    display_name = getattr(new_item, 'display_name', item_class_name)
                    self.game.player.pickup_item(new_item)
                    messages.append(f"🎉 获得了装备：{display_name}！")
                except AttributeError:
                    messages.append(f"错误：未找到装备 {item_class_name}。")
        if not found_loot:
            messages.append("没有获得任何战利品。")
        return messages

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
           (event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]):
            from states.story import StoryScreen
            self.game.state_stack.pop()
            if self.game.current_stage != "quit":
                self.game.state_stack.append(StoryScreen(self.game))
            else:
                self.game.running = False
    
    # In states/loot.py

    def draw(self, surface):
        surface.fill(BG_COLOR)
        panel_rect = pygame.Rect(SCREEN_WIDTH * 0.15, SCREEN_HEIGHT * 0.15, SCREEN_WIDTH * 0.7, SCREEN_HEIGHT * 0.7)
        draw_panel(surface, panel_rect, "战斗结算", self.game.fonts['large'])
        
        # --- 这是核心修改 ---
        # 如果消息是 None，则视为空列表 []
        exp_msgs = self.exp_messages or []
        loot_msgs = self.loot_messages or []
        all_messages = exp_msgs + ["-"*20] + loot_msgs
        # --- 修改结束 ---
        
        current_y = panel_rect.top + 120
        for line in all_messages:
            clean_line = line.replace("🎉 ", "")
            text_surf = self.game.fonts['normal'].render(clean_line, True, TEXT_COLOR)
            text_rect = text_surf.get_rect(center=(panel_rect.centerx, current_y))
            surface.blit(text_surf, text_rect)
            current_y += 35
        
        prompt_surf = self.game.fonts['small'].render("点击 / 空格 / 回车 继续...", True, TEXT_COLOR)
        prompt_rect = prompt_surf.get_rect(center=(panel_rect.centerx, panel_rect.bottom - 40))
        surface.blit(prompt_surf, prompt_rect)