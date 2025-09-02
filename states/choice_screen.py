# states/choice_screen.py (已修正)
import pygame
import inspect
from .base import BaseState
from ui import Button, draw_panel, draw_text
from settings import *

# states/choice_screen.py (修改这个函数)

class ChoiceScreen(BaseState):
    def __init__(self, game, item_choices, origin_room):
        super().__init__(game)
        self.is_overlay = True
        self.item_choices = item_choices
        self.origin_room = origin_room
        self.choice_buttons = []

        # --- 关键修复 3: 初始化“门锁” ---
        # 初始状态下，门是“未上锁”的，允许玩家做出选择。
        self.choice_made = False

        self._setup_ui()

    def _setup_ui(self):
        # ... (此方法无需修改) ...
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

# states/choice_screen.py (替换这个函数)

def handle_event(self, event):
    # 如果门已经“锁上”，则不处理任何后续的点击事件，防止重复触发
    if self.choice_made:
        return

    for button, item in self.choice_buttons:
        # 检查按钮是否被点击
        if button.handle_event(event):

            # --- 关键修复 1: 立刻“上锁”！ ---
            # 一旦玩家做出选择，马上设置标志位，防止任何后续的重复点击。
            self.choice_made = True 

            # 执行拾取物品的逻辑
            feedback = self.game.player.pickup_item(item)
            if feedback:
                from .notification_screen import NotificationScreen
                self.game.state_stack.append(NotificationScreen(self.game, feedback))

            print(f"玩家选择了: {getattr(item, 'display_name', item.__class__.__name__)}")

            # 将房间标记为“已清理”
            self.origin_room.is_cleared = True

            # 更新底层的地牢界面，让门显示出来
            from .dungeon_screen import DungeonScreen
            # 安全地检查状态栈，确保前一个界面是 DungeonScreen
            if len(self.game.state_stack) > 1:
                prev_state = self.game.state_stack[-2]
                if isinstance(prev_state, DungeonScreen):
                    prev_state.door_rects = prev_state._generate_doors()

            # --- 关键修复 2: “演员”退场！ ---
            # 在所有逻辑处理完毕后，将自己从状态栈中弹出。
            self.game.state_stack.pop() 

            # 因为已经处理完并退出了，直接 return 结束该函数
            return
    # ... (draw 方法无需修改) ...
    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
        draw_panel(surface, self.panel_rect, "二选一", self.game.fonts['large'])
        for button, item in self.choice_buttons:
            bg_color = PANEL_BORDER_COLOR if button.is_hovered else PANEL_BG_COLOR
            pygame.draw.rect(surface, bg_color, button.rect, border_radius=10); pygame.draw.rect(surface, PANEL_BORDER_COLOR, button.rect, 2, border_radius=10)
            name = getattr(item, 'display_name', item.__class__.__name__); rarity = getattr(item, 'rarity', 'common'); color = RARITY_COLORS.get(rarity, RARITY_COLORS['common'])
            name_surf = self.game.fonts['normal'].render(f"[ {name} ]", True, color)
            name_rect = name_surf.get_rect(centerx=button.rect.centerx, top=button.rect.top + 20); surface.blit(name_surf, name_rect)
            line_y = name_rect.bottom + 10; pygame.draw.line(surface, PANEL_BORDER_COLOR, (button.rect.left + 20, line_y), (button.rect.right - 20, line_y))
            doc = inspect.getdoc(item) or "效果未知。"; text_rect = button.rect.inflate(-40, -120); text_rect.top = line_y + 15
            draw_text(surface, doc, self.game.fonts['small'], TEXT_COLOR, text_rect)