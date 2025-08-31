import pygame
import random
from .base import BaseState
from ui import draw_panel, draw_text
from settings import *
import Equips

class LootScreen(BaseState):
    def __init__(self, game, defeated_enemy_id=None):
        super().__init__(game)
        self.is_overlay = True
        self.defeated_enemy_id = defeated_enemy_id
        self._process_rewards()

    def _process_rewards(self):
        self.exp_messages = []
        if self.defeated_enemy_id:
            enemy_preset = self.game.enemy_data.get(self.defeated_enemy_id, {})
            self.exp_messages = self.game.player.add_exp(enemy_preset.get("exp_reward", 0))
        
        self.loot_messages = self._generate_loot()
        self.game.save_to_slot(0)
        
    def _generate_loot(self):
        messages = ["--- 战利品 ---"] # 更通用的标题
        found_loot = False
        
        possible_drops = []
        is_battle_loot = self.defeated_enemy_id is not None

        if is_battle_loot:
            # 战斗胜利，从特定敌人的掉落表里随机
            possible_drops = self.game.loot_data.get(self.defeated_enemy_id, [])
        else:
            # 开宝箱，从所有可能的掉落物品中随机挑选一个作为奖励
            all_item_names = [item["item_class_name"] for drops in self.game.loot_data.values() for item in drops]
            if all_item_names:
                random_item_name = random.choice(all_item_names)
                possible_drops.append({"item_class_name": random_item_name, "chance": 1.0})

        for drop_info in possible_drops:
            if random.random() < drop_info.get("chance", 1.0):
                found_loot = True
                item_class_name = drop_info["item_class_name"]
                try:
                    item_class = getattr(Equips, item_class_name)
                    new_item = item_class()
                    display_name = getattr(new_item, 'display_name', item_class_name)
                    self.game.player.pickup_item(new_item)
                    messages.append(f"🎉 获得了：{display_name}！") # 更通用的文本
                except AttributeError:
                    messages.append(f"错误：未找到物品 {item_class_name}。")
        
        # <-- 核心修复 2: 根据不同情况显示正确的“空”提示 -->
        if not found_loot:
            if is_battle_loot:
                messages.append("敌人没有掉落任何东西。")
            else:
                messages.append("宝箱是空的...")
                
        return messages

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
           (event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]):
            self.game.state_stack.pop()
    
    def draw(self, surface):
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
        panel_rect = pygame.Rect(SCREEN_WIDTH * 0.15, SCREEN_HEIGHT * 0.15, SCREEN_WIDTH * 0.7, SCREEN_HEIGHT * 0.7)
        title = "战斗胜利" if self.defeated_enemy_id else "打开宝箱" # 标题逻辑保持不变
        draw_panel(surface, panel_rect, title, self.game.fonts['large'])
        all_messages = self.exp_messages + self.loot_messages
        current_y = panel_rect.top + 120
        for line in all_messages:
            clean_line = line.replace("🎉 ", "")
            text_surf = self.game.fonts['normal'].render(clean_line, True, TEXT_COLOR)
            text_rect = text_surf.get_rect(center=(panel_rect.centerx, current_y))
            surface.blit(text_surf, text_rect); current_y += 35
        prompt_surf = self.game.fonts['small'].render("点击任意处继续...", True, TEXT_COLOR)
        prompt_rect = prompt_surf.get_rect(center=(panel_rect.centerx, panel_rect.bottom - 40))
        surface.blit(prompt_surf, prompt_rect)