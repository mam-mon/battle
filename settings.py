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
PLAYER_ACTION_PANEL_RECT = pygame.Rect(PLAYER_PANEL_RECT.right + 20, PLAYER_PANEL_RECT.top, 200, PLAYER_PANEL_RECT.height)


# --- 物品品质颜色 ---
RARITY_COLORS = {
    "common":    (255, 255, 255),  # 白色
    "uncommon":  (30, 255, 30),    # 绿色
    "rare":      (0, 150, 255),   # 蓝色
    "epic":      (180, 50, 255),   # 紫色
    "legendary": (255, 150, 0),    # 橙色
    "mythic":    (255, 50, 50),    # 红色
}

# --- 玩家角色配置 ---
PLAYER_BASE_STATS = {
    "hp": 100,
    "defense": 3,
    "magic_resist": 3,
    "attack": 10,
    "attack_speed": 1.2,
}

# 文件: settings.py (在文件末尾追加)

# --- 新增：伤害类型颜色 ---
DAMAGE_TYPE_COLORS = {
    "PHYSICAL":      (220, 220, 220), # 物理伤害 - 亮灰色
    "MAGIC":         (138, 43, 226),  # 魔法伤害 - 紫罗兰色
    "TRUE":          (255, 255, 255), # 真实伤害 - 纯白色
    "POISON":        (0, 255, 0),     # 剧毒伤害 - 绿色
    "DRAGON_SOURCE": (255, 165, 0),   # 龙源伤害 - 橙色
    "HEAL":          (144, 238, 144), # 治疗效果 - 亮绿色
}

# --- 新增：伤害类型中文名 ---
DAMAGE_TYPE_NAMES_CN = {
    "PHYSICAL":      "物理伤害",
    "MAGIC":         "魔法伤害",
    "TRUE":          "真实伤害",
    "POISON":        "毒素伤害",
    "DRAGON_SOURCE": "龙源伤害",
}
# 文件: settings.py (追加)
CRIT_COLOR = (255, 215, 0)          # 暴击文字颜色 - 金色
