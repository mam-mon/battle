# states/choice_screen.py (已更新)
import pygame
import inspect
from .base import BaseState
from ui import Button, draw_panel, draw_text
from settings import *

class ChoiceScreen(BaseState):
    # ... (__init__, _setup_ui, handle_event 保持不变) ...
    def __init__(self, game, item_choices, origin_room):
        super().__init__(game); self.is_overlay = True
        self.item_choices, self.origin_room = item_choices, origin_room
        self.choice_buttons = []; self._setup_ui()
    def _setup_ui(self):
        num_choices = len(self.item_choices)
        panel_width = 350 * num_choices + 100; panel_height = 500
        panel_rect = pygame.Rect(0, 0, panel_width, panel_height); panel_rect.center = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)
        self.panel_rect = panel_rect
        card_width, card_height, spacing = 300, 400, 50
        start_x = panel_rect.centerx - (card_width * num_choices + spacing * (num_choices - 1)) / 2
        for i, item in enumerate(self.item_choices):
            card_x = start_x + i * (card_width + spacing)
            card_rect = pygame.Rect(panel_rect.y + 80, card_x,  card_width, card_height); card_rect.topleft = (card_x, panel_rect.y + 80)
            button = Button(card_rect, "", self.game.fonts['normal']); self.choice_buttons.append((button, item))
    def handle_event(self, event):
        for button, item in self.choice_buttons:
            if button.handle_event(event):
                self.game.player.pickup_item(item); print(f"玩家选择了: {getattr(item, 'display_name', item.__class__.__name__)}")
                self.origin_room.is_cleared = True
                from .dungeon_screen import DungeonScreen
                if len(self.game.state_stack) > 1:
                    prev_state = self.game.state_stack[-2]
                    if isinstance(prev_state, DungeonScreen): prev_state.door_rects = prev_state._generate_doors()
                self.game.state_stack.pop(); return
    
    # --- 核心修改：draw 方法 ---
    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
        draw_panel(surface, self.panel_rect, "二选一", self.game.fonts['large'])
        
        for button, item in self.choice_buttons:
            bg_color = PANEL_BORDER_COLOR if button.is_hovered else PANEL_BG_COLOR
            pygame.draw.rect(surface, bg_color, button.rect, border_radius=10)
            pygame.draw.rect(surface, PANEL_BORDER_COLOR, button.rect, 2, border_radius=10)
            
            # --- 新增：根据品质显示颜色 ---
            name = getattr(item, 'display_name', item.__class__.__name__)
            rarity = getattr(item, 'rarity', 'common')
            color = RARITY_COLORS.get(rarity, RARITY_COLORS['common'])
            
            # 绘制带颜色的标题
            name_surf = self.game.fonts['normal'].render(f"[ {name} ]", True, color)
            name_rect = name_surf.get_rect(centerx=button.rect.centerx, top=button.rect.top + 20)
            surface.blit(name_surf, name_rect)

            # 绘制分割线
            line_y = name_rect.bottom + 10
            pygame.draw.line(surface, PANEL_BORDER_COLOR, (button.rect.left + 20, line_y), (button.rect.right - 20, line_y))
            
            # 绘制描述文本
            doc = inspect.getdoc(item) or "效果未知。"
            text_rect = button.rect.inflate(-40, -120); text_rect.top = line_y + 15
            draw_text(surface, doc, self.game.fonts['small'], TEXT_COLOR, text_rect)