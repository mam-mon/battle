# game.py (已更新)
import pygame
import pickle
import os
import time
import json
import sys
from settings import *
# <-- 导入 ui 模块，而不仅仅是 init_fonts
import ui
from Character import Character
import Equips
import Talents

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("我的游戏")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fonts = ui.init_fonts()
        ui.prepare_fallback_fonts(self.fonts['small']) 
        self.state_stack = []

        # <-- 核心改动：在游戏启动时加载所有Buff图标资源 -->
        #ui.load_buff_icons()

        self.player = None
        self.current_stage = "1"
        self.loaded_dialogue_index = 0

        self.story_data = self._load_json("story.json")
        self.enemy_data = self._load_json("enemies.json")
        self.loot_data = self._load_json("loot_tables.json")
        self.event_data = self._load_json("events.json")

        self.dungeon_data = {}
        dungeon_folder = 'dungeons'
        for filename in os.listdir(dungeon_folder):
            if filename.endswith('.json'):
                dungeon_id = filename.split('.')[0]
                self.dungeon_data[dungeon_id] = self._load_json(os.path.join(dungeon_folder, filename))

    def run(self):
        from states.title import TitleScreen
        self.state_stack.append(TitleScreen(self))

        while self.running and self.state_stack:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)
        
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if self.state_stack:
                self.state_stack[-1].handle_event(event)

    def update(self):
        if self.state_stack:
            self.state_stack[-1].update()

    def draw(self):
        # --- 全新的分层绘制逻辑 ---
        if not self.state_stack:
            pygame.display.flip()
            return

        # 1. 找到最底部的非弹窗界面
        base_state_index = -1
        for i in range(len(self.state_stack) - 1, -1, -1):
            if not getattr(self.state_stack[i], 'is_overlay', False):
                base_state_index = i
                break
        
        # 2. 绘制所有底层界面 (通常只有一个)
        if base_state_index != -1:
            for i in range(base_state_index + 1):
                 self.state_stack[i].draw(self.screen)

        # 3. 逐个绘制所有弹窗界面
        for i in range(base_state_index + 1, len(self.state_stack)):
            self.state_stack[i].draw(self.screen)
        
        pygame.display.flip()

    def _load_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e:
            print(f"ERROR: Could not load {filename}: {e}")
            return None

    def get_save_filename(self, slot_number):
        return f"save_slot_{slot_number}.dat"

    def peek_save_slot(self, slot_number):
        filename = self.get_save_filename(slot_number)
        if not os.path.exists(filename): return None
        try:
            with open(filename, "rb") as f: return pickle.load(f)
        except Exception: return None

    def save_to_slot(self, slot_number):
        filename = self.get_save_filename(slot_number)
        try:
            dialogue_index = 0
            from states.story import StoryScreen
            for state in reversed(self.state_stack):
                if isinstance(state, StoryScreen):
                    dialogue_index = state.dialogue_index; break
            data_to_save = {
                "player": self.player, "current_stage": self.current_stage,
                "dialogue_index": dialogue_index, "timestamp": time.time()
            }
            with open(filename, "wb") as f: pickle.dump(data_to_save, f)
            print(f"Game saved to slot {slot_number}")
            return f"成功保存到槽位 {slot_number}！"
        except Exception as e:
            print(f"Save failed: {e}"); return "存档失败！"

    def load_from_slot(self, slot_number):
        data = self.peek_save_slot(slot_number)
        if data:
            self.player = data["player"]
            self.current_stage = data["current_stage"]
            self.loaded_dialogue_index = data.get("dialogue_index", 0)
            return True
        return False
   
    # 文件: game.py (替换这个函数)

    def start_new_game(self):
        player_eq = [Equips.WoodenSword(), Equips.DragonHeart()]
        player_talents = [
            #Talents.HeartOfHealingTalent(),
            #Talents.DualWieldTalent(),
            #Talents.Adventurer()
        ]
        
        # --- 核心修改：使用从 settings.py 导入的 PLAYER_BASE_STATS ---
        # **PLAYER_BASE_STATS 是一种简便写法，它会自动把字典里的所有键值对作为参数传入
        self.player = Character(
            "玩家", 
            **PLAYER_BASE_STATS, # <-- 使用我们定义的标准属性
            equipment=player_eq,
            talents=player_talents
        )
        self.current_stage = "1"
        self.loaded_dialogue_index = 0