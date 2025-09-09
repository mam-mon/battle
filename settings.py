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
PLAYER_PANEL_RECT = pygame.Rect(50, 50, 500, 250)
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
    "hp": 50,
    "defense": 3,
    "magic_resist": 3,
    "attack": 1000,
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

# settings.py (在文件末尾添加)

# settings.py (替换文件末尾的布局常量代码块)

# --- 新的地牢界面布局常量 ---

# 房间逻辑尺寸，适配新的地牢视图
ROOM_SIZE = 700

# 左侧UI面板宽度
UI_PANEL_WIDTH = 300 

# 实际地牢游戏区域（在UI面板右侧）
DUNGEON_VIEW_X = UI_PANEL_WIDTH
DUNGEON_VIEW_Y = 0  # <-- 补全 DUNGEON_VIEW_Y
DUNGEON_VIEW_WIDTH = SCREEN_WIDTH - UI_PANEL_WIDTH
DUNGEON_VIEW_HEIGHT = SCREEN_HEIGHT

# 小地图在左侧UI面板内的位置和大小
MINIMAP_UI_X = 0
MINIMAP_UI_Y = 0
MINIMAP_UI_WIDTH = UI_PANEL_WIDTH
MINIMAP_UI_HEIGHT = int(SCREEN_HEIGHT * 0.45) # 占据左侧45%的高度

# 角色信息面板在左侧UI面板内的位置和大小
PLAYER_INFO_UI_X = 0
PLAYER_INFO_UI_Y = MINIMAP_UI_HEIGHT
PLAYER_INFO_UI_WIDTH = UI_PANEL_WIDTH
PLAYER_INFO_UI_HEIGHT = int(SCREEN_HEIGHT * 0.25) # 占据左侧25%的高度

# 快捷按钮区域在左侧UI面板内的位置和大小
BUTTON_AREA_UI_X = 0
BUTTON_AREA_UI_Y = MINIMAP_UI_HEIGHT + PLAYER_INFO_UI_HEIGHT
BUTTON_AREA_UI_WIDTH = UI_PANEL_WIDTH
BUTTON_AREA_UI_HEIGHT = SCREEN_HEIGHT - BUTTON_AREA_UI_Y
# --- 布局常量结束 ---

# settings.py (追加到文件末尾)

# --- 新增：淬炼结晶系统常量 ---

# 1. 重复装备时，根据品质获得的淬炼结晶数量
CRYSTALS_PER_RARITY = {
    "common":    1,
    "uncommon":  2,
    "rare":      5,
    "epic":      10,
    "legendary": 25,
    "mythic":    50
}

# 2. 在背包中升级装备时，根据品质消耗的淬炼结晶数量
UPGRADE_COST_PER_RARITY = {
    "common":    10,
    "uncommon":  25,
    "rare":      50,
    "epic":      100,
    "legendary": 200,
    # 神话(mythic)品质通常是最高级，所以默认无法再升级
}