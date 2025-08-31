# states/choice_screen.py
import pygame
import inspect
from .base import BaseState
from ui import Button, draw_panel, draw_text
from settings import *

class ChoiceScreen(BaseState):
    def __init__(self, game, item_choices, origin_room):
        super().__init__(game)
        self.is_overlay = True
        self.item_choices = item_choices
        self.origin_room = origin_room # 记录来源房间，以便后续更新状态

        self.choice_buttons = []
        self._setup_ui()

    def _setup_ui(self):
        """创建UI元素，比如两个选项卡"""
        num_choices = len(self.item_choices)
        panel_width = 350 * num_choices + 100
        panel_height = 500
        
        panel_rect = pygame.Rect(0, 0, panel_width, panel_height)
        panel_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.panel_rect = panel_rect

        card_width, card_height = 300, 400
        spacing = 50
        start_x = panel_rect.centerx - (card_width * num_choices + spacing * (num_choices - 1)) / 2

        for i, item in enumerate(self.item_choices):
            card_x = start_x + i * (card_width + spacing)
            card_rect = pygame.Rect(panel_rect.y + 80, card_x,  card_width, card_height)
            card_rect.topleft = (card_x, panel_rect.y + 80)
            
            # 使用 Button 类来处理点击，但我们自定义绘制
            button = Button(card_rect, "", self.game.fonts['normal'])
            self.choice_buttons.append((button, item))

    def _get_item_description(self, item):
        """获取物品的名称和描述文本"""
        name = getattr(item, 'display_name', item.__class__.__name__)
        doc = inspect.getdoc(item) or "效果未知。"
        return f"[ {name} ]\n" + "-"*15 + f"\n{doc}"

    def handle_event(self, event):
        for button, item in self.choice_buttons:
            if button.handle_event(event):
                # --- 玩家做出了选择 ---
                # 1. 将选中物品加入背包
                self.game.player.pickup_item(item)
                print(f"玩家选择了: {getattr(item, 'display_name', item.__class__.__name__)}")
                
                # 2. 将来源房间标记为“已清理”
                self.origin_room.is_cleared = True
                
                # 3. 通知地图界面更新（如果它存在的话）
                from .dungeon_screen import DungeonScreen
                if len(self.game.state_stack) > 1:
                    prev_state = self.game.state_stack[-2]
                    if isinstance(prev_state, DungeonScreen):
                         # 让地牢界面重新生成门
                        prev_state.door_rects = prev_state._generate_doors()

                # 4. 关闭选择界面
                self.game.state_stack.pop()
                return

    def draw(self, surface):
        # 绘制半透明背景
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        
        # 绘制主面板
        draw_panel(surface, self.panel_rect, "二选一", self.game.fonts['large'])
        
        # 绘制每个选项卡
        for button, item in self.choice_buttons:
            # 根据悬停状态改变背景色
            bg_color = PANEL_BORDER_COLOR if button.is_hovered else PANEL_BG_COLOR
            pygame.draw.rect(surface, bg_color, button.rect, border_radius=10)
            pygame.draw.rect(surface, PANEL_BORDER_COLOR, button.rect, 2, border_radius=10)
            
            # 绘制物品描述
            desc_text = self._get_item_description(item)
            text_rect = button.rect.inflate(-40, -40) # 留出边距
            draw_text(surface, desc_text, self.game.fonts['small'], TEXT_COLOR, text_rect)