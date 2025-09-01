
# Character.py (已更新)
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
from damage import DamagePacket, DamageType
from settings import RARITY_COLORS # <-- 导入品质颜色

# --- 新增：定义重复装备转化成的金币数量 ---
RARITY_GOLD_VALUE = {
    "common": 10,
    "uncommon": 25,
    "rare": 60,
    "epic": 150,
    "legendary": 400,
    "mythic": 1000,
}

class Character:
    # ... (__init__ 和大部分方法保持不变) ...
    DEFAULT_SLOT_CAPACITY = {"weapon": 1, "offhand": 1, "helmet": 1, "armor": 1, "pants": 1, "accessory": 4}
    def __init__(self, name, hp, defense, magic_resist, attack, attack_speed,
                 equipment=None, talents=None):
        self.name = name; self.level = 1; self.gold = 0
        self.exp, self.exp_to_next_level, self.backpack = 0, 100, []
        self.SLOT_CAPACITY = self.DEFAULT_SLOT_CAPACITY.copy()
        self.talents = talents or []
        for t in self.talents: t.on_init(self)
        self.slots = {slot: [] for slot in self.SLOT_CAPACITY}
        self._innate_max_hp, self._innate_defense, self._innate_attack, self._innate_attack_speed = hp, defense, attack, attack_speed
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
        self.max_hp, self.hp, self.defense, self.attack, self.attack_speed = self.base_max_hp, self.base_max_hp, self.base_defense, self.base_attack, self.base_attack_speed
        self.attack_interval = 6.0 / self.attack_speed
        self.shield, self._cd, self.crit_chance, self.crit_multiplier = 0, 0.0, 0.0, 1.5
        self.last_damage, self.last_hits, self.buffs, self.damage_resistance = 0, collections.deque(maxlen=5), [], 0.0
        for eq in (equipment or []): self.equip(eq)

    # --- 新增：一个专门用来加钱并显示信息的方法 ---
    def add_gold(self, amount, source=""):
        if amount <= 0: return
        self.gold += amount
        source_text = f" ({source})" if source else ""
        print(f"[金币] 获得了 {amount} G！{source_text} (当前: {self.gold} G)")

    # --- 核心修改：重写 pickup_item 方法 ---
    def pickup_item(self, item_to_pickup):
        """拾取一件物品。如果已有同名装备，则根据品质转化为金币。"""
        
        # 检查背包和身上是否已有同名装备
        item_name = getattr(item_to_pickup, 'display_name', item_to_pickup.__class__.__name__)
        
        all_current_items = self.backpack + self.all_equipment
        is_duplicate = any(getattr(item, 'display_name', item.__class__.__name__) == item_name for item in all_current_items)

        if is_duplicate:
            # --- 如果是重复装备 ---
            rarity = getattr(item_to_pickup, 'rarity', 'common')
            gold_value = RARITY_GOLD_VALUE.get(rarity, 5) # 获取转化价值
            
            # 使用 rich 库打印带颜色的信息
            color_str = str(RARITY_COLORS.get(rarity, (255,255,255))).replace(" ", "")
            console.print(f"   [grey70]获得了重复装备 [bold color=rgb{color_str}]{item_name}[/bold color=rgb{color_str}]，自动转化为 [yellow]{gold_value} G[/yellow]。[/grey70]")
            
            self.add_gold(gold_value, source=f"转化装备({item_name})")

        else:
            # --- 如果是新装备 ---
            self.backpack.append(item_to_pickup)
            console.print(f"   [grey70]物品 [bold]{item_name}[/bold] 已放入你的背包。[/grey70]")

    # ... (后续所有其他方法都保持不变，这里省略以节省篇幅) ...
    # ... (on_enter_combat, update, take_damage, try_attack, etc.) ...
    def on_enter_combat(self):
        self.buffs.clear(); self.hp = self.max_hp; self.shield = 0; self._cd = 0.0
        print(f"{self.name} 已进入战斗准备状态！")
    def update(self, dt) -> list[str]:
        texts = []
        for buff in list(self.buffs):
            if hasattr(buff, "on_tick"):
                res = buff.on_tick(self, dt)
                if isinstance(res, str) and res:
                    texts.append(res)
        return texts
    def take_damage(self, packet: DamagePacket):
        final_packet = packet.copy()
        for eq in self.all_equipment:
            if hasattr(eq, "before_take_damage"): eq.before_take_damage(self, final_packet)
        for buff in list(self.buffs):
            if hasattr(buff, "before_take_damage"): buff.before_take_damage(self, final_packet)
        mitigated_amount = final_packet.amount
        if not final_packet.ignores_armor and final_packet.damage_type != DamageType.TRUE:
            if final_packet.damage_type == DamageType.PHYSICAL: mitigated_amount -= self.defense
            elif final_packet.damage_type == DamageType.MAGIC: mitigated_amount -= self.magic_resist
        mitigated_amount *= (1.0 - self.damage_resistance)
        mitigated_amount = max(0, mitigated_amount)
        if self.shield > 0:
            shield_absorbed = min(self.shield, mitigated_amount)
            self.shield -= shield_absorbed; mitigated_amount -= shield_absorbed
        if mitigated_amount > 0:
            self.hp = max(0, self.hp - mitigated_amount)
            timestamp = pygame.time.get_ticks() if "pygame" in sys.modules else int(time.time() * 1000)
            self.last_hits.append((int(mitigated_amount), timestamp))
        for eq in self.all_equipment:
            if hasattr(eq, "after_take_damage"): eq.after_take_damage(self, final_packet, mitigated_amount)
        for buff in list(self.buffs):
            if hasattr(buff, "on_attacked"): buff.on_attacked(self, final_packet.source, mitigated_amount)
        if self.hp <= 0:
            to_remove = []
            for buff in list(self.buffs):
                if hasattr(buff, "on_fatal") and buff.on_fatal(self): to_remove.append(buff)
            for buff in to_remove: self.remove_buff(buff)
    def try_attack(self, target, dt):
        if any(getattr(b, "disable_attack", False) for b in self.buffs): return None
        self._cd += dt
        if self._cd < self.attack_interval or self.hp <= 0: return None
        is_crit = (random.random() < self.crit_chance)
        damage = self.attack * self.crit_multiplier if is_crit else self.attack
        packet = DamagePacket(amount=damage, damage_type=DamageType.PHYSICAL, source=self, is_critical=is_crit)
        for eq in self.all_equipment:
            if hasattr(eq, "before_attack"): eq.before_attack(self, target, packet)
        pre_total = target.shield + target.hp; target.take_damage(packet); post_total = target.shield + target.hp
        actual_dmg = pre_total - post_total
        for eq in self.all_equipment:
            if hasattr(eq, "after_attack"): eq.after_attack(self, target, actual_dmg)
        if is_crit:
            for eq in self.all_equipment:
                if hasattr(eq, "on_critical"): eq.on_critical(self, target, actual_dmg)
        else:
            for eq in self.all_equipment:
                if hasattr(eq, "on_non_critical"): eq.on_non_critical(self, target, actual_dmg)
        extra_texts = []
        for t in self.talents:
            if hasattr(t, "on_attack"):
                out = t.on_attack(self, target, actual_dmg)
                if out: extra_texts.extend(out)
        self._cd -= self.attack_interval
        text = f"{self.name} → {target.name} 造成 {int(actual_dmg)} 点伤害"
        if is_crit: text += " (暴击!)"
        return text, extra_texts
    def perform_extra_attack(self, target):
        print(f"[{self.name}] 正在执行额外攻击！")
        is_crit = (random.random() < self.crit_chance)
        damage = self.attack * self.crit_multiplier if is_crit else self.attack
        packet = DamagePacket(amount=damage, damage_type=DamageType.PHYSICAL, source=self, is_critical=is_crit)
        for eq in self.all_equipment:
            if hasattr(eq, "before_attack"): eq.before_attack(self, target, packet)
        pre_total = target.shield + target.hp; target.take_damage(packet); post_total = target.shield + target.hp
        actual_dmg = pre_total - post_total
        for eq in self.all_equipment:
            if hasattr(eq, "after_attack"): eq.after_attack(self, target, actual_dmg)
        if is_crit:
            for eq in self.all_equipment:
                if hasattr(eq, "on_critical"): eq.on_critical(self, target, actual_dmg)
        else:
            for eq in self.all_equipment:
                if hasattr(eq, "on_non_critical"): eq.on_non_critical(self, target, actual_dmg)
        text = f"{self.name} (额外攻击) → {target.name} 造成 {int(actual_dmg)} 点伤害"
        if is_crit: text += " (暴击!)"
        return text
    def recalculate_stats(self):
        all_eq = self.all_equipment
        self._eq_hp_bonus = sum(getattr(eq, "hp_bonus", 0) for eq in all_eq)
        self._eq_def_bonus = sum(getattr(eq, "def_bonus", 0) for eq in all_eq)
        self._eq_atk_bonus = sum(getattr(eq, "atk_bonus", 0) for eq in all_eq)
        self._eq_as_bonus = sum(getattr(eq, "as_bonus", 0) for eq in all_eq)
        self.base_max_hp = self._innate_max_hp + self._eq_hp_bonus
        self.base_defense = self._innate_defense + self._eq_def_bonus
        self.base_attack = self._innate_attack + self._eq_atk_bonus
        self.base_attack_speed = self._innate_attack_speed + self._eq_as_bonus
        hp_percent = self.hp / self.max_hp if self.max_hp > 0 else 1
        self.max_hp = self.base_max_hp
        self.hp = self.max_hp * hp_percent
        self.defense = self.base_defense; self.attack = self.base_attack; self.attack_speed = self.base_attack_speed
        self.attack_interval = 6.0 / self.attack_speed
        print("角色属性已更新！")
    @property
    def all_equipment(self):
        eqs = [];
        for eq_list in self.slots.values(): eqs.extend(eq_list)
        return eqs
    def equip(self, eq_to_equip):
        slot = eq_to_equip.slot
        if slot not in self.SLOT_CAPACITY: raise ValueError(f"未知插槽：{slot}")
        unequipped_item = None
        if len(self.slots[slot]) >= self.SLOT_CAPACITY[slot]:
            if self.SLOT_CAPACITY[slot] == 1:
                unequipped_item = self.slots[slot][0]; self.slots[slot][0] = eq_to_equip
            else: print(f"警告: {slot} 插槽已满"); return eq_to_equip
        else: self.slots[slot].append(eq_to_equip)
        self.recalculate_stats(); return unequipped_item
    def unequip(self, eq_to_unequip):
        slot = eq_to_unequip.slot
        if eq_to_unequip in self.slots[slot]:
            self.slots[slot].remove(eq_to_unequip); self.recalculate_stats(); return eq_to_unequip
        return None
    def heal(self, amount: float) -> float:
        healed = min(self.max_hp - self.hp, amount)
        if healed <= 0: return 0.0
        self.hp += healed
        for buff in list(self.buffs):
            if hasattr(buff, "on_healed"): buff.on_healed(self, healed)
        return healed
    def add_status(self, status: Buffs.Buff, *, source: "Character" = None):
        final_buff = None; added_stacks = status.stacks
        for b in self.buffs:
            if isinstance(b, status.__class__):
                if b.max_stacks == 1: b.remaining = b.duration
                else: b.stacks = min(b.stacks + status.stacks, b.max_stacks)
                final_buff = b; break
        if final_buff is None:
            final_buff = status; self.buffs.append(status); status.on_apply(self)
        if source is not None and source is not self and getattr(final_buff, "is_debuff", False):
            for t in source.talents:
                if hasattr(t, "on_inflict_debuff"): t.on_inflict_debuff(source, self, final_buff, added_stacks)
        if getattr(final_buff, "dispellable", False) and getattr(final_buff, "is_debuff", False):
            for t in self.talents:
                if hasattr(t, "on_debuff_applied"): t.on_debuff_applied(self, final_buff)
    add_buff = add_status
    add_debuff = add_status
    def remove_buff(self, buff): self.buffs.remove(buff); buff.on_remove(self)
    def add_exp(self, amount):
        if self.hp <= 0: return []
        self.exp += amount; messages = [f"获得了 {amount} 点经验！ (当前: {self.exp}/{self.exp_to_next_level})"]
        if self.exp >= self.exp_to_next_level: messages.extend(self.level_up())
        return messages
    def level_up(self):
        level_up_messages = []
        while self.exp >= self.exp_to_next_level:
            self.level += 1; self.exp -= self.exp_to_next_level
            self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
            self._innate_max_hp += 10; self._innate_attack += 2; self._innate_defense += 1
            self.recalculate_stats()
            level_up_messages.append(f"🎉 等级提升！现在是 {self.level} 级！")
            level_up_messages.append("   生命+10，攻击+2，防御+1")
        return level_up_messages