# 文件: states/rest_screen.py (新文件)

import pygame
import random
from .base import BaseState
from ui import Button, draw_panel, draw_text
from settings import *

class RestScreen(BaseState):

    def __init__(self, game, origin_room):
        super().__init__(game)
        self.is_overlay = True
        self.origin_room = origin_room

        self.rest_used = False
        self.forge_used = False
        self.feedback_message = ""

        # --- 核心修改在这里 ---
        from Equips import UPGRADE_MAP 

        # 1. 创建一个包含玩家所有物品（已装备的 + 背包里的）的总列表
        all_player_items = self.game.player.all_equipment + self.game.player.backpack

        # 2. 从这个总列表中，筛选出所有可以被升级的物品
        self.upgradable_items = [
            item for item in all_player_items
            if item.__class__ in UPGRADE_MAP
        ]

        self._setup_ui()

    def _setup_ui(self):
        """初始化用户界面元素"""
        panel_w, panel_h = 800, 500
        self.panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) / 2, (SCREEN_HEIGHT - panel_h) / 2, panel_w, panel_h)

        # 定义两个核心选项按钮的位置
        btn_w, btn_h = 300, 180
        spacing = 50
        start_x = self.panel_rect.centerx - (btn_w * 2 + spacing) / 2

        self.rest_button = Button(
            (start_x, self.panel_rect.centery - btn_h/2, btn_w, btn_h),
            "休息", # 按钮的初始文字
            self.game.fonts['large']
        )
        self.forge_button = Button(
            (start_x + btn_w + spacing, self.panel_rect.centery - btn_h/2, btn_w, btn_h),
            "锻造",
            self.game.fonts['large']
        )
        
        # 离开按钮
        self.leave_button = Button(
            (self.panel_rect.centerx - 150, self.panel_rect.bottom - 100, 300, 60),
            "离开",
            self.game.fonts['normal']
        )

    def handle_event(self, event):
        """处理玩家的输入事件"""
        # --- 休息按钮的逻辑 (不变) ---
        if not self.rest_used and self.rest_button.handle_event(event):
            self.rest_used = True
            heal_amount = int(self.game.player.max_hp * 0.3)
            self.game.player.heal(heal_amount)
            self.feedback_message = f"你恢复了 {heal_amount} 点生命！"
            self.forge_used = True # 休息和锻造二选一
            return

        # --- 全新的、更强大的锻造逻辑 ---
        if not self.forge_used and len(self.upgradable_items) > 0 and self.forge_button.handle_event(event):
            self.forge_used = True
            self.rest_used = True # 休息和锻造二选一

            player = self.game.player

            # 1. 从可升级列表中随机选一件 (现在这个列表包含了背包物品)
            item_to_upgrade = random.choice(self.upgradable_items)
            item_name = getattr(item_to_upgrade, 'display_name', '装备')

            from Equips import UPGRADE_MAP
            upgraded_class = UPGRADE_MAP.get(item_to_upgrade.__class__)

            if upgraded_class:
                # 2. 创建升级后的新装备实例
                upgraded_item = upgraded_class()

                # 3. 从原来的位置移除旧装备
                #    检查它是在身上还是在背包里
                if item_to_upgrade in player.all_equipment:
                    player.unequip(item_to_upgrade)
                elif item_to_upgrade in player.backpack:
                    player.backpack.remove(item_to_upgrade)

                # 4. 将锻造好的新装备放入背包
                #    我们使用 pickup_item 方法，因为它能自动处理重复物品转化为金币的逻辑
                feedback = player.pickup_item(upgraded_item)
                if "放入你的背包" in feedback:
                    self.feedback_message = f"锻造成功！新的「{upgraded_item.display_name}」已放入你的背包！"
                else: # 如果玩家已经有升级版的装备了，会自动转化成金币
                    self.feedback_message = f"锻造成功！但你已拥有同名装备，转化为金币！"

            else:
                self.feedback_message = f"「{item_name}」似乎无法被强化..."

            return

        # --- 处理离开按钮 (不变) ---
        if self.leave_button.handle_event(event):
            self._leave_room()

    def _leave_room(self):
        """处理离开休息室的逻辑"""
        from .dungeon_screen import DungeonScreen
        self.origin_room.is_cleared = True

        # Check the state below this one on the stack
        if len(self.game.state_stack) > 1:
            prev_state = self.game.state_stack[-2]
            if isinstance(prev_state, DungeonScreen):
                # Correctly notify the DungeonScreen that we are returning
                prev_state.is_returning = True

        # Pop the current state (this RestScreen) off the stack
        self.game.state_stack.pop()
        
    def _leave_room(self):
        """处理离开休息室的逻辑"""
        from .dungeon_screen import DungeonScreen
        self.origin_room.is_cleared = True

        if len(self.game.state_stack) > 1:
            prev_state = self.game.state_stack[-2]
            if isinstance(prev_state, DungeonScreen):
                # --- 核心修复：通知地牢界面 ---
                prev_state.is_returning = True
                prev_state.door_rects = prev_state._generate_doors()

        self.game.state_stack.pop()

    def draw(self, surface):
        """绘制所有UI元素到屏幕上"""
        # 绘制半透明的背景遮罩
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))

        # 绘制主面板
        draw_panel(surface, self.panel_rect, "篝火旁的쉼터", self.game.fonts['large'])

        # --- 绘制休息按钮和描述 ---
        self.rest_button.draw(surface)
        rest_desc = "恢复30%最大生命值"
        rest_desc_rect = self.rest_button.rect.copy()
        rest_desc_rect.y += 190 # 调整描述文本的位置
        draw_text(surface, rest_desc, self.game.fonts['small'], TEXT_COLOR, rest_desc_rect)
        if self.rest_used: # 如果已使用，绘制一个遮罩
            s = pygame.Surface(self.rest_button.rect.size, pygame.SRCALPHA)
            s.fill((50,50,50,180))
            surface.blit(s, self.rest_button.rect.topleft)

        # --- 绘制锻造按钮和描述 ---
        self.forge_button.draw(surface)
        forge_desc = "随机强化一件装备"
        if len(self.upgradable_items) == 0:
            forge_desc = "没有可强化的装备"
        forge_desc_rect = self.forge_button.rect.copy()
        forge_desc_rect.y += 190
        draw_text(surface, forge_desc, self.game.fonts['small'], TEXT_COLOR, forge_desc_rect)
        if self.forge_used or len(self.upgradable_items) == 0: # 如果已使用或没有装备，绘制遮罩
            s = pygame.Surface(self.forge_button.rect.size, pygame.SRCALPHA)
            s.fill((50,50,50,180))
            surface.blit(s, self.forge_button.rect.topleft)

        # 绘制操作反馈信息
        if self.feedback_message:
            feedback_rect = pygame.Rect(0, self.panel_rect.top + 100, self.panel_rect.width, 40)
            feedback_rect.centerx = self.panel_rect.centerx
            draw_text(surface, self.feedback_message, self.game.fonts['normal'], HOVER_COLOR, feedback_rect)

        # 绘制离开按钮
        self.leave_button.draw(surface)