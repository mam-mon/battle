import pygame
import sys
import time
import collections
import math
import random
from rich.console import Console
console = Console()

import Buffs
import Talents
import Equips

class Character:
    DEFAULT_SLOT_CAPACITY = {
        "weapon": 1, "offhand": 1, "helmet": 1,
        "armor": 1, "pants": 1, "accessory": 4,
    }

    def __init__(self, name, hp, defense, magic_resist, attack, attack_speed,
                 equipment=None, talents=None):
        self.name = name
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 100
        self.backpack = []

        self.SLOT_CAPACITY = self.DEFAULT_SLOT_CAPACITY.copy()

        self.talents = talents or []
        for t in self.talents:
            t.on_init(self)
            
        self.slots = {slot: [] for slot in self.SLOT_CAPACITY}

        self._innate_max_hp = hp
        self._innate_defense = defense
        self._innate_attack = attack
        self._innate_attack_speed= attack_speed
        self.magic_resist = magic_resist

        equipment = equipment or []
        self._eq_hp_bonus = sum(getattr(eq, "hp_bonus", 0) for eq in equipment)
        self._eq_def_bonus = sum(getattr(eq, "def_bonus", 0) for eq in equipment)
        self._eq_atk_bonus = sum(getattr(eq, "atk_bonus", 0) for eq in equipment)
        self._eq_as_bonus = sum(getattr(eq, "as_bonus", 0) for eq in equipment)
        
        self.base_max_hp = self._innate_max_hp + self._eq_hp_bonus
        self.base_defense = self._innate_defense + self._eq_def_bonus
        self.base_attack = self._innate_attack + self._eq_atk_bonus
        self.base_attack_speed = self._innate_attack_speed + self._eq_as_bonus

        self.max_hp = self.base_max_hp
        self.hp = self.max_hp
        self.defense = self.base_defense
        self.attack = self.base_attack
        self.attack_speed = self.base_attack_speed
        self.attack_interval = 6.0 / self.attack_speed
        
        self.shield = 0
        self._cd = 0.0
        self.crit_chance = 0.0
        self.crit_multiplier = 1.5
        self.last_damage = 0
        self.last_hits = collections.deque(maxlen=5)
        self.buffs = []
        self.damage_resistance = 0.0  

        for eq in (equipment or []):
            self.equip(eq)
        
    # <-- 核心修复：添加这个缺失的方法 -->
    def on_enter_combat(self):
        """在进入一场新战斗前，重置角色的临时状态。"""
        # 1. 清空所有上一场战斗留下的Buff和Debuff
        self.buffs.clear()
        
        # 2. 状态重置：恢复满生命，清空护盾和冷却
        self.hp = self.max_hp
        self.shield = 0
        self._cd = 0.0
        
        print(f"{self.name} 已进入战斗准备状态！")

    @property
    def all_equipment(self):
        eqs = []
        for eq_list in self.slots.values():
            eqs.extend(eq_list)
        return eqs

    def equip(self, eq_to_equip):
        slot = eq_to_equip.slot
        if slot not in self.SLOT_CAPACITY:
            raise ValueError(f"未知插槽：{slot}")
        
        if len(self.slots[slot]) >= self.SLOT_CAPACITY[slot]:
            if self.SLOT_CAPACITY[slot] > 1:
                print(f"警告: {slot} 插槽已满，无法装备 {eq_to_equip.display_name}")
                return eq_to_equip
            else:
                unequipped_item = self.slots[slot][0]
                self.slots[slot][0] = unequipped_item
                return unequipped_item
        
        self.slots[slot].append(eq_to_equip)
        return None

    def unequip(self, eq_to_unequip):
        slot = eq_to_unequip.slot
        if eq_to_unequip in self.slots[slot]:
            self.slots[slot].remove(eq_to_unequip)
            return eq_to_unequip
        return None

    def recalculate_stats(self): print("重新计算角色属性...")

    def heal(self, amount: float) -> float:
        healed = min(self.max_hp - self.hp, amount)
        if healed <= 0: return 0.0
        self.hp += healed
        for buff in list(self.buffs):
            if hasattr(buff, "on_healed"): buff.on_healed(self, healed)
        return healed
        
    def add_status(self, status: Buffs.Buff, *, source: "Character" = None):
        final_buff = None
        added_stacks = status.stacks
        for b in self.buffs:
            if isinstance(b, status.__class__):
                if b.max_stacks == 1: b.remaining = b.duration
                else: b.stacks = min(b.stacks + status.stacks, b.max_stacks)
                final_buff = b; break
        if final_buff is None:
            final_buff = status
            self.buffs.append(status)
            status.on_apply(self)
        if source is not None and source is not self and getattr(final_buff, "is_debuff", False):
            for t in source.talents:
                if hasattr(t, "on_inflict_debuff"): t.on_inflict_debuff(source, self, final_buff, added_stacks)
        if getattr(final_buff, "dispellable", False) and getattr(final_buff, "is_debuff", False):
            for t in self.talents:
                if hasattr(t, "on_debuff_applied"): t.on_debuff_applied(self, final_buff)
    add_buff = add_status
    add_debuff = add_status
    
    def remove_buff(self, buff):
        self.buffs.remove(buff)
        buff.on_remove(self)

    def update(self, dt) -> list[str]:
        texts = []
        for buff in list(self.buffs):
            if hasattr(buff, "on_tick"):
                res = buff.on_tick(self, dt)
                if isinstance(res, str) and res: texts.append(res)
        return texts

    def take_damage(self, dmg, attacker=None):
        if attacker is not None: self._last_real_attacker = attacker
        for eq in self.all_equipment: dmg = eq.before_take_damage(self, dmg)
        for buff in list(self.buffs):
            dmg = buff.before_take_damage(self, dmg)
            if hasattr(buff, "on_attacked"): buff.on_attacked(self, attacker, dmg)
        if self.damage_resistance: dmg = dmg * (1.0 - self.damage_resistance)
        if self.shield > 0:
            used = min(self.shield, dmg); self.shield -= used; dmg -= used
        if dmg > 0:
            self.hp = max(0, self.hp - dmg)
            timestamp = pygame.time.get_ticks() if "pygame" in sys.modules else int(time.time() * 1000)
            self.last_hits.append((int(dmg), timestamp))
        for buff in list(self.buffs):
            if hasattr(buff, "on_attacked"): buff.on_attacked(self, attacker, dmg)
        if self.hp <= 0:
            to_remove = []
            for buff in list(self.buffs):
                if hasattr(buff, "on_fatal"):
                    if buff.on_fatal(self): to_remove.append(buff)
            for buff in to_remove: self.remove_buff(buff)

    def try_attack(self, target, dt):
        if any(getattr(b, "disable_attack", False) for b in self.buffs): return None
        self._cd += dt
        if self._cd < self.attack_interval or self.hp <= 0: return None
        is_crit = (random.random() < self.crit_chance)
        base_dmg = max(0, self.attack * self.crit_multiplier - target.defense) if is_crit else max(0, self.attack - target.defense)
        dmg = base_dmg
        for eq in self.all_equipment: dmg = eq.before_attack(self, target, dmg)
        pre_total = target.shield + target.hp
        target.take_damage(dmg, attacker=self)
        post_total = target.shield + target.hp
        actual = pre_total - post_total
        if actual > 0: target.last_hits.append((int(actual), is_crit))
        for eq in self.all_equipment: eq.after_attack(self, target, dmg)
        if is_crit:
            for eq in self.all_equipment: eq.on_critical(self, target, dmg)
        else:
            for eq in self.all_equipment: eq.on_non_critical(self, target, dmg)
        extra_texts = []
        for t in self.talents:
            out = t.on_attack(self, target, dmg)
            if out: extra_texts.extend(out)
        self._cd -= self.attack_interval
        text = f"{self.name} → {target.name} 造成 {int(actual)} 点伤害"
        if is_crit: text += " (暴击!)"
        return text, extra_texts

    def perform_extra_attack(self, target):
        is_crit = (random.random() < self.crit_chance)
        dmg = max(0, self.attack * self.crit_multiplier - target.defense) if is_crit else max(0, self.attack - target.defense)
        for eq in self.all_equipment: dmg = eq.before_attack(self, target, dmg)
        target.take_damage(dmg, attacker=self)
        for eq in self.all_equipment: eq.after_attack(self, target, dmg)
        if is_crit:
            for eq in self.all_equipment: eq.on_critical(self, target, dmg)
        else:
            for eq in self.all_equipment: eq.on_non_critical(self, target, dmg)
        text = f"{self.name} → {target.name} 造成 {int(dmg)} 点伤害"
        if is_crit: text += " (暴击!)"
        target.last_damage = int(dmg); target.last_hits.append((int(dmg), is_crit)); return text

    def add_exp(self, amount):
        if self.hp <= 0: return []
        self.exp += amount
        messages = [f"获得了 {amount} 点经验！ (当前: {self.exp}/{self.exp_to_next_level})"]
        if self.exp >= self.exp_to_next_level:
            messages.extend(self.level_up())
        return messages

    def level_up(self):
        level_up_messages = []
        while self.exp >= self.exp_to_next_level:
            self.level += 1
            self.exp -= self.exp_to_next_level
            self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
            self._innate_max_hp += 10; self._innate_attack += 2; self._innate_defense += 1
            self.base_max_hp = self._innate_max_hp + self._eq_hp_bonus
            self.base_attack = self._innate_attack + self._eq_atk_bonus
            self.base_defense = self._innate_defense + self._eq_def_bonus
            self.max_hp = self.base_max_hp; self.attack = self.base_attack
            self.defense = self.base_defense; self.hp = self.max_hp
            level_up_messages.append(f"🎉 等级提升！现在是 {self.level} 级！")
            level_up_messages.append("   生命+10，攻击+2，防御+1")
        return level_up_messages
        
    def pickup_item(self, item):
        self.backpack.append(item)
        console.print(f"   [grey70]物品 [bold]{getattr(item, 'display_name', item.__class__.__name__)}[/bold] 已放入你的背包。[/grey70]")