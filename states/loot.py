# states/loot.py (已修正)
import pygame
import random
from .base import BaseState
from ui import draw_panel, draw_text
from settings import *
import Equips
from Character import Character # 需要导入Character类用于类型检查

class LootScreen(BaseState):
    def __init__(self, game, defeated_enemy_object=None, next_story_stage=None):
        super().__init__(game)
        self.is_overlay = True

        # --- 核心修改在这里 ---
        # defeated_enemy_object 现在是完整的敌人对象
        self.defeated_enemy_object = defeated_enemy_object
        # 我们仍然需要 enemy_id 来查询装备掉落表
        self.defeated_enemy_id = defeated_enemy_object.id if isinstance(defeated_enemy_object, Character) else None

        self.next_story_stage = next_story_stage

        panel_w = SCREEN_WIDTH * 0.7
        panel_h = SCREEN_HEIGHT * 0.7
        self.panel_rect = pygame.Rect(
            (SCREEN_WIDTH - panel_w) / 2,
            (SCREEN_HEIGHT - panel_h) / 2,
            panel_w, panel_h
        )
        self._process_rewards()
        # ------------------------------------

        self._process_rewards()

    def _process_rewards(self):
        self.exp_messages = []
        if self.defeated_enemy_id:
            enemy_preset = self.game.enemy_data.get(self.defeated_enemy_id, {})
            self.exp_messages = self.game.player.add_exp(enemy_preset.get("exp_reward", 0))
        
        self.loot_messages = self._generate_loot()
        self.game.save_to_slot(0)
        


    def _generate_loot(self):
        messages = []
        found_any_loot = False

        # --- Part 1: 装备掉落逻辑 (现在使用 self.defeated_enemy_id) ---
        if self.defeated_enemy_id: # 确保ID存在
            equipment_drops = self.game.loot_data.get(self.defeated_enemy_id, [])
            if equipment_drops:
                messages.append("--- 战利品 ---")
                for drop_info in equipment_drops:
                    if random.random() < drop_info.get("chance", 1.0):
                        found_any_loot = True
                        item_class_name = drop_info["item_class_name"]
                        try:
                            item_class = getattr(Equips, item_class_name)
                            new_item = item_class()
                            display_name = getattr(new_item, 'display_name', item_class_name)
                            feedback = self.game.player.pickup_item(new_item)
                            if "放入你的背包" in feedback:
                                messages.append(f"获得了装备：{display_name}！")
                            else:
                                messages.append(feedback)
                        except AttributeError:
                            messages.append(f"错误：未找到物品 {item_class_name}。")

        # --- Part 2: 全新的、更精确的天赋掉落逻辑 ---
        import Talents

        # 直接从传递过来的敌人对象中获取它实际拥有的天赋列表！
        if self.defeated_enemy_object and self.defeated_enemy_object.equipped_talents:
            messages.append("--- 能力领悟 ---")

            # 遍历这个敌人在战斗中真正拥有的每一个天赋
            for possessed_talent in self.defeated_enemy_object.equipped_talents:
                # 在这里设置一个固定的天赋掉落率，比如 15%
                TALENT_DROP_CHANCE = 0.15 

                if random.random() < TALENT_DROP_CHANCE:
                    # 尝试让玩家学习这个天赋
                    was_new = self.game.player.learn_talent(possessed_talent)

                    if was_new:
                        found_any_loot = True
                        messages.append(f"你从敌人身上领悟了「{possessed_talent.display_name}」！")

        # --- Part 3: 最终总结 ---
        if not found_any_loot:
            messages.append("敌人没有留下任何有价值的东西。")

        return messages

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1) or \
           (event.type == pygame.KEYDOWN and event.key in [pygame.K_RETURN, pygame.K_SPACE]):
            
            if self.next_story_stage:
                from .story import StoryScreen
                self.game.current_stage = self.next_story_stage
                self.game.state_stack.pop()
                if self.game.state_stack and isinstance(self.game.state_stack[-1], StoryScreen):
                    self.game.state_stack.pop()
                self.game.state_stack.append(StoryScreen(self.game))
            else:
                self.game.state_stack.pop()

    def draw(self, surface):
        # 绘制底层界面
        if len(self.game.state_stack) > 1:
            self.game.state_stack[-2].draw(surface)
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
        
        # --- 核心修复：使用 self.panel_rect ---
        title = "战斗胜利" if self.defeated_enemy_id else "打开宝箱"
        draw_panel(surface, self.panel_rect, title, self.game.fonts['large'])
        
        all_messages = self.exp_messages + self.loot_messages
        current_y = self.panel_rect.top + 120
        for line in all_messages:
            clean_line = line.replace("🎉 ", "")
            text_surf = self.game.fonts['normal'].render(clean_line, True, TEXT_COLOR)
            text_rect = text_surf.get_rect(center=(self.panel_rect.centerx, current_y))
            surface.blit(text_surf, text_rect); current_y += 35
            
        prompt_surf = self.game.fonts['small'].render("点击任意处继续...", True, TEXT_COLOR)
        prompt_rect = prompt_surf.get_rect(center=(self.panel_rect.centerx, self.panel_rect.bottom - 40))
        surface.blit(prompt_surf, prompt_rect)