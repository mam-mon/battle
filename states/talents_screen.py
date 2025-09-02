# states/talents_screen.py
import pygame
import inspect
from .base import BaseState
from ui import draw_panel, draw_text, Button, get_display_name, TooltipManager
from settings import *

class TalentsScreen(BaseState):
    def __init__(self, game):
        super().__init__(game)
        self.is_overlay = True
        self.dragging_talent = None
        self.dragging_from = None # 'equipped' or 'learned'
        
        self._setup_layout()
        self.tooltip_manager = TooltipManager(self.game.fonts['small'])

    def _setup_layout(self):
        """设置UI布局，分为左右两个区域"""
        margin, header_height = 40, 80
        self.container_rect = pygame.Rect(margin, margin, SCREEN_WIDTH - 2*margin, SCREEN_HEIGHT - 2*margin)
        self.header_rect = pygame.Rect(self.container_rect.x, self.container_rect.y, self.container_rect.width, header_height)
        
        content_y = self.header_rect.bottom + 10
        content_height = self.container_rect.height - header_height - 10
        
        # 左侧：已装备天赋
        self.equipped_panel_rect = pygame.Rect(self.container_rect.x, content_y, 350, content_height)
        # 右侧：天赋库
        self.learned_panel_rect = pygame.Rect(self.equipped_panel_rect.right + 10, content_y, self.container_rect.right - self.equipped_panel_rect.right - 10, content_height)
        
        self.close_button = Button(pygame.Rect(self.container_rect.right - 45, self.container_rect.top + 10, 35, 35), "X", self.game.fonts['normal'])

    def handle_event(self, event):
        if self.close_button.handle_event(event) or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            if self.dragging_talent: self._return_dragging_talent()
            self.game.state_stack.pop(); return
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: self._handle_mouse_down(event.pos)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1: self._handle_mouse_up(event.pos)

    def _handle_mouse_down(self, pos):
        """处理鼠标按下事件，负责“拾起”天赋"""
        if self.dragging_talent: return
        
        # 检查是否从“已装备”区域拾起
        for i, talent in enumerate(self.game.player.equipped_talents):
            rect = self._get_talent_rect(i, 'equipped')
            if rect.collidepoint(pos):
                self.dragging_talent, self.dragging_from = talent, 'equipped'
                self.game.player.unequip_talent(talent) # 拾起时立刻卸下
                return
        
        # 检查是否从“天赋库”区域拾起
        unequipped = [t for t in self.game.player.learned_talents if t not in self.game.player.equipped_talents]
        for i, talent in enumerate(unequipped):
            rect = self._get_talent_rect(i, 'learned')
            if rect.collidepoint(pos):
                self.dragging_talent, self.dragging_from = talent, 'learned'
                return

    # 文件: states/talents_screen.py (替换这个函数)

    def _handle_mouse_up(self, pos):
        if not self.dragging_talent: return

        talent_to_place = self.dragging_talent
        source_type = self.dragging_from
        self.dragging_talent, self.dragging_from = None, None

        # 检查是否放置在“已装备”区域
        for i in range(self.game.player.max_talent_slots):
            rect = self._get_talent_rect(i, 'equipped')
            if rect.collidepoint(pos):

                # 获取目标槽位原有的天赋
                target_talent = None
                if i < len(self.game.player.equipped_talents):
                    target_talent = self.game.player.equipped_talents[i]

                # 如果目标槽位有天赋，先卸下它
                if target_talent:
                    self.game.player.unequip_talent(target_talent)

                # 尝试装备正在拖拽的天赋
                success = self.game.player.equip_talent(talent_to_place)

                if success:
                    # 如果装备成功，并且原目标槽位有天赋，并且拖拽的天赋来自已装备区
                    # 那么这就是一次“交换”，把目标天赋装备回去 (equip_talent会自动找到空位)
                    if target_talent and source_type == 'equipped':
                        self.game.player.equip_talent(target_talent)
                else:
                    # 如果装备失败，把所有东西都送回原处
                    self._return_dragging_talent(talent_to_place) # 送回拖拽天赋
                    if target_talent: # 送回目标天赋
                        self.game.player.equip_talent(target_talent)

                self.game.player.recalculate_stats()
                return

        # 如果放在其他任何地方，视为卸下 (即返回原处)
        self._return_dragging_talent(talent_to_place)
        self.game.player.recalculate_stats()
        
    def _return_dragging_talent(self, talent):
        """在拖拽被取消或失败时，将天赋送回原处"""
        if self.dragging_from == 'equipped':
            self.game.player.equip_talent(talent)

    def update(self):
        """更新悬浮提示"""
        if self.dragging_talent: self.tooltip_manager.update(None); return
        hovered_talent = None
        mouse_pos = pygame.mouse.get_pos()
        
        all_panels = [('equipped', self.game.player.equipped_talents), 
                      ('learned', [t for t in self.game.player.learned_talents if t not in self.game.player.equipped_talents])]

        for panel_type, talent_list in all_panels:
            for i, talent in enumerate(talent_list):
                rect = self._get_talent_rect(i, panel_type)
                if rect.collidepoint(mouse_pos):
                    hovered_talent = talent; break
            if hovered_talent: break
        
        self.tooltip_manager.update(hovered_talent)

    def _get_talent_rect(self, index, panel_type):
        """计算指定索引的天赋在哪个位置"""
        panel_rect = self.equipped_panel_rect if panel_type == 'equipped' else self.learned_panel_rect
        padding = 20
        item_size, spacing = 60, 10
        cols = (panel_rect.width - 2 * padding + spacing) // (item_size + spacing)
        
        col = index % cols
        row = index // cols
        
        x = panel_rect.left + padding + col * (item_size + spacing)
        y = panel_rect.top + 100 + row * (item_size + spacing)
        return pygame.Rect(x, y, item_size, item_size)

    def draw(self, surface):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA); overlay.fill((0, 0, 0, 180)); surface.blit(overlay, (0, 0))
        draw_panel(surface, self.container_rect, "天赋管理", self.game.fonts['large'])
        
        self._draw_equipped_panel(surface)
        self._draw_learned_panel(surface)
        self._draw_dragging_talent(surface)
        
        self.close_button.draw(surface)
        self.tooltip_manager.draw(surface)

    def _draw_equipped_panel(self, surface):
        player = self.game.player
        title = f"已装备 ({len(player.equipped_talents)}/{player.max_talent_slots})"
        title_rect = self.equipped_panel_rect.copy(); title_rect.height = 50; title_rect.move_ip(0, 40)
        draw_text(surface, title, self.game.fonts['normal'], TEXT_COLOR, title_rect)

        for i in range(player.max_talent_slots):
            rect = self._get_talent_rect(i, 'equipped')
            pygame.draw.rect(surface, (20, 30, 40, 150), rect, border_radius=8)
            pygame.draw.rect(surface, (70, 80, 100, 180), rect, 2, border_radius=8)
            
            if i < len(player.equipped_talents):
                talent = player.equipped_talents[i]
                if talent is not self.dragging_talent:
                    talent_text = talent.display_name[:2] # 显示天赋前两个字
                    draw_text(surface, talent_text, self.game.fonts['normal'], TEXT_COLOR, rect)

    def _draw_learned_panel(self, surface):
        title_rect = self.learned_panel_rect.copy(); title_rect.height = 50; title_rect.move_ip(0, 40)
        draw_text(surface, "天赋库", self.game.fonts['normal'], TEXT_COLOR, title_rect)
        
        unequipped = [t for t in self.game.player.learned_talents if t not in self.game.player.equipped_talents]
        
        # 绘制所有已学习的天赋格子
        for i, talent in enumerate(unequipped):
            if talent is not self.dragging_talent:
                rect = self._get_talent_rect(i, 'learned')
                pygame.draw.rect(surface, PANEL_BG_COLOR, rect, border_radius=8)
                pygame.draw.rect(surface, PANEL_BORDER_COLOR, rect, 2, border_radius=8)
                talent_text = talent.display_name[:2]
                draw_text(surface, talent_text, self.game.fonts['normal'], TEXT_COLOR, rect)

    def _draw_dragging_talent(self, surface):
        if self.dragging_talent:
            mouse_pos = pygame.mouse.get_pos()
            name = get_display_name(self.dragging_talent)
            font = self.game.fonts['normal']
            text_surf = font.render(name, True, TEXT_COLOR)
            rect = text_surf.get_rect(center=mouse_pos)
            
            bg_rect = rect.inflate(20, 12)
            pygame.draw.rect(surface, PANEL_BG_COLOR, bg_rect, border_radius=8)
            pygame.draw.rect(surface, PANEL_BORDER_COLOR, bg_rect, 2, border_radius=8)
            surface.blit(text_surf, rect)