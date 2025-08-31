# settings.py
import pygame
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BG_COLOR = (10, 20, 30)
TEXT_COLOR = (230, 230, 230)
HOVER_COLOR = (200, 220, 255) # 鼠标悬停颜色
PANEL_BG_COLOR = (20, 35, 50)
PANEL_BORDER_COLOR = (100, 180, 255)
HP_BAR_GREEN = (0, 200, 0)
SHIELD_BAR_GREY = (150, 150, 150)
FONT_SIZE_NORMAL = 28
FONT_SIZE_SMALL = 22
FONT_SIZE_LARGE = 48
FONT_NAME_CN = 'Microsoft YaHei'
FONT_NAME_EN = 'Consolas'

# --- 新增颜色和尺寸 ---
XP_BAR_COLOR = (150, 100, 255)      # 经验条颜色
LOG_TEXT_COLOR = (200, 200, 200)    # 战斗日志文字颜色
LOG_BG_COLOR = (30, 45, 60, 200)    # 战斗日志背景色 (带透明度)
BUTTON_CLICK_COLOR = (150, 200, 255) # 按钮点击颜色

# Buff/Debuff 图标尺寸
BUFF_ICON_SIZE = (32, 32)

# --- 布局位置 ---
# (这些是建议值，你可以随时调整)
PLAYER_PANEL_RECT = pygame.Rect(50, 450, 500, 250)
ENEMY_PANEL_RECT = pygame.Rect(SCREEN_WIDTH - 550, 50, 500, 250)
BATTLE_LOG_RECT = pygame.Rect(50, 50, SCREEN_WIDTH - 650, 350)


# --- 物品品质颜色 ---
RARITY_COLORS = {
    "common":    (255, 255, 255),  # 白色
    "uncommon":  (30, 255, 30),    # 绿色
    "rare":      (0, 150, 255),   # 蓝色
    "epic":      (180, 50, 255),   # 紫色
    "legendary": (255, 150, 0),    # 橙色
    "mythic":    (255, 50, 50),    # 红色
}