# game.py

import pygame
import pickle
import os
import time
import json
from settings import *
from ui import init_fonts
from Character import Character
import Equips
import sys

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("我的游戏")
        self.clock = pygame.time.Clock()
        self.running = True
        self.fonts = init_fonts()
        self.state_stack = []

        self.player = None
        self.current_stage = "1"
        self.loaded_dialogue_index = 0 # Used to pass loaded index to StoryScreen

        # Load data
        self.story_data = self._load_json("story.json")
        self.enemy_data = self._load_json("enemies.json")
        self.loot_data = self._load_json("loot_tables.json")

    def run(self):
        # Import the initial state class here to avoid circular imports
        from states.title import TitleScreen
        self.state_stack.append(TitleScreen(self))

        while self.running and len(self.state_stack) > 0:
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
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            
            # Let the current state handle the event
            self.state_stack[-1].handle_event(event)

    def update(self):
        self.state_stack[-1].update()

    def draw(self):
        self.state_stack[-1].draw(self.screen)
        pygame.display.flip()

    def _load_json(self, filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f: return json.load(f)
        except Exception as e:
            print(f"ERROR: Could not load {filename}: {e}")
            return None

    def get_save_filename(self, slot_number):
        return f"save_slot_{slot_number}.dat"

    def save_to_slot(self, slot_number):
        filename = self.get_save_filename(slot_number)
        try:
            dialogue_index = 0
            from states.story import StoryScreen
            # Find the story state in the stack to get its progress
            for state in reversed(self.state_stack):
                if isinstance(state, StoryScreen):
                    dialogue_index = state.dialogue_index
                    break

            data_to_save = {
                "player": self.player,
                "current_stage": self.current_stage,
                "dialogue_index": dialogue_index,
                "timestamp": time.time()
            }
            with open(filename, "wb") as f: pickle.dump(data_to_save, f)
            print(f"Game saved to slot {slot_number}")
            return f"成功保存到槽位 {slot_number}！"
        except Exception as e:
            print(f"Save failed: {e}")
            return "存档失败！"

    def load_from_slot(self, slot_number):
        filename = self.get_save_filename(slot_number)
        if not os.path.exists(filename): return None
        try:
            with open(filename, "rb") as f:
                data = pickle.load(f)
                self.player = data["player"]
                self.current_stage = data["current_stage"]
                self.loaded_dialogue_index = data.get("dialogue_index", 0)
                return data
        except Exception as e:
            print(f"Load failed: {e}")
            return None
            
    def start_new_game(self):
        player_eq = [Equips.WoodenSword(), Equips.WoodenArmor()]
        self.player = Character("玩家", hp=100, defense=5, magic_resist=3, attack=10, attack_speed=1.2, equipment=player_eq)
        self.current_stage = "1"
        self.loaded_dialogue_index = 0