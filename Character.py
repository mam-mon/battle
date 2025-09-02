# Character.py (最终完整版)
import pygame
import sys
import time
import collections
import math
import random
# from rich.console import Console  <- No longer needed
# console = Console()

import Buffs
import Talents
import Equips
from damage import DamagePacket, DamageType
from settings import RARITY_COLORS

RARITY_GOLD_VALUE = {"common": 10, "uncommon": 25, "rare": 60, "epic": 150, "legendary": 400, "mythic": 1000}

class Character:
    DEFAULT_SLOT_CAPACITY = {"weapon": 1, "offhand": 1, "helmet": 1, "armor": 1, "pants": 1, "accessory": 4}

    def __init__(self, name, hp, defense, magic_resist, attack, attack_speed,
                 equipment=None, talents=None, id=None): # <-- 1. 在这里增加 id=None

        self.id = id or name # <-- 2. 增加这一行，如果提供了id就用id，否则用名字
        self.name, self.level, self.gold = name, 1, 0
        self.exp, self.exp_to_next_level, self.backpack = 0, 100, []
        self.SLOT_CAPACITY = self.DEFAULT_SLOT_CAPACITY.copy()
        self.max_talent_slots = 3 
        self.learned_talents = talents or []
        self.equipped_talents = []
        self._innate_max_hp, self._innate_defense, self._innate_attack, self._innate_attack_speed = hp, defense, attack, attack_speed
        self.magic_resist = magic_resist
        self.slots = {
            slot: [None] * capacity for slot, capacity in self.SLOT_CAPACITY.items()
        }
        for eq in (equipment or []): self.equip(eq)
        self.base_max_hp, self.base_defense, self.base_attack, self.base_attack_speed = 0, 0, 0, 0
        self.recalculate_stats(); self.hp = self.max_hp
        initial_talents_to_equip = self.learned_talents[:]
        self.learned_talents = []
        for talent in initial_talents_to_equip: self.learn_talent(talent); self.equip_talent(talent)
        self.shield, self._cd, self.crit_chance, self.crit_multiplier = 0, 0.0, 0.0, 1.5
        self.last_damage, self.last_hits, self.buffs, self.damage_resistance = 0, collections.deque(maxlen=5), [], 0.0

    def add_gold(self, amount, source=""):
        if amount <= 0: return None
        self.gold += amount
        source_text = f" ({source})" if source else ""
        return f"获得了 {amount} G！{source_text} (当前: {self.gold} G)"

    def pickup_item(self, item_to_pickup):
        item_name = getattr(item_to_pickup, 'display_name', item_to_pickup.__class__.__name__)
        all_current_items = self.backpack + self.all_equipment
        is_duplicate = any(getattr(item, 'display_name', item.__class__.__name__) == item_name for item in all_current_items)
        if is_duplicate:
            rarity = getattr(item_to_pickup, 'rarity', 'common')
            gold_value = RARITY_GOLD_VALUE.get(rarity, 5)
            return self.add_gold(gold_value, source=f"转化({item_name})")
        else:
            self.backpack.append(item_to_pickup)
            return f"物品「{item_name}」已放入你的背包。"
    
    # ... (其他所有方法都保持不变)
    def learn_talent(self, talent_to_learn):
        if not any(isinstance(t, talent_to_learn.__class__) for t in self.learned_talents):
            self.learned_talents.append(talent_to_learn)
            print(f"学会了新天赋: {talent_to_learn.display_name}")
            return True
        return False
    def equip_talent(self, talent_to_equip):
        if len(self.equipped_talents) >= self.max_talent_slots: print("天赋槽已满！"); return False
        if talent_to_equip not in self.learned_talents: print("尚未学会该天赋！"); return False
        if talent_to_equip in self.equipped_talents: print("该天赋已被装备。"); return False
        self.equipped_talents.append(talent_to_equip); self.recalculate_stats(); print(f"已装备天赋: {talent_to_equip.display_name}"); return True
    def unequip_talent(self, talent_to_unequip):
        if talent_to_unequip not in self.equipped_talents: return
        self.equipped_talents.remove(talent_to_unequip); self.recalculate_stats(); print(f"已卸下天赋: {talent_to_unequip.display_name}")
    # 文件: Character.py

    def on_enter_combat(self):
        self.buffs.clear(); self.hp = self.max_hp; self.shield = 0; self._cd = 0.0;

        # 新增逻辑：重置装备的战斗内状态
        for eq in self.all_equipment:
            if isinstance(eq, Equips.AdventurersPouch):
                eq.atk_bonus = 0 # 战斗准备时，将钱袋的加成清零

        # 重置完后再重算一次属性，确保一个干净的状态
        self.recalculate_stats() 
        print(f"{self.name} 已进入战斗准备状态！")
    def update(self, dt) -> list[str]:
        texts = []
        for buff in list(self.buffs):
            if hasattr(buff, "on_tick"): res = buff.on_tick(self, dt);
            if isinstance(res, str) and res: texts.append(res)
        for eq in self.all_equipment:
            if hasattr(eq, "on_tick"): res = eq.on_tick(self, dt);
            if isinstance(res, str) and res: texts.append(res)
        return texts
    # 在 Character.py 文件中，找到并替换 recalculate_stats 方法

    # Replace the entire recalculate_stats method with this new version
    def recalculate_stats(self):
        """重新计算所有来自装备和天赋的属性加成"""
        # 1. 保存当前血量百分比
        hp_percent = self.hp / self.max_hp if hasattr(self, 'max_hp') and self.max_hp > 0 else 1

        # 2. 重置为纯粹的“固有”属性
        self.base_max_hp = self._innate_max_hp
        self.base_defense = self._innate_defense
        self.base_attack = self._innate_attack
        self.base_attack_speed = self._innate_attack_speed

        # 3. 加上所有来自“装备”的属性
        all_eq = self.all_equipment
        self.base_max_hp += sum(getattr(eq, "hp_bonus", 0) for eq in all_eq)
        self.base_defense += sum(getattr(eq, "def_bonus", 0) for eq in all_eq)
        self.base_attack += sum(getattr(eq, "atk_bonus", 0) for eq in all_eq)
        self.base_attack_speed += sum(getattr(eq, "as_bonus", 0) for eq in all_eq)

        # 4. 将“当前属性”先重置为“基础属性”
        self.max_hp = self.base_max_hp
        self.defense = self.base_defense
        self.attack = self.base_attack
        self.attack_speed = self.base_attack_speed
        self.crit_chance = 0.0 
        self.magic_resist = 3 
        self.damage_resistance = 0.0

        # --- 核心修复在这里 ---
        # 5. 在应用天赋之前，先重置 SLOT_CAPACITY 为默认值
        #    这可以防止天赋效果（如二刀流）在卸下后依然残留
        self.SLOT_CAPACITY = self.DEFAULT_SLOT_CAPACITY.copy()

        # 6. 应用所有来自“已装备天赋”的修改（这可能会改变 SLOT_CAPACITY）
        for talent in self.equipped_talents:
            if hasattr(talent, 'on_init'):
                talent.on_init(self)

        # 7. 新增：同步装备槽容量
        #    在天赋修改完 SLOT_CAPACITY 规则后，我们在这里确保 self.slots 的实际大小与规则匹配
        for slot, required_capacity in self.SLOT_CAPACITY.items():
            current_slots = self.slots.get(slot, [])
            current_capacity = len(current_slots)

            if current_capacity < required_capacity:
                # 如果实际槽位比需要的少，就用 None 补上
                current_slots.extend([None] * (required_capacity - current_capacity))
            elif current_capacity > required_capacity:
                # 如果实际槽位比需要的多（例如卸下了二刀流天赋）
                # 我们需要处理多余的装备，这里简单地将它们放回背包
                extra_items = current_slots[required_capacity:]
                for item in extra_items:
                    if item:
                        self.backpack.append(item)
                # 然后截断列表
                self.slots[slot] = current_slots[:required_capacity]
        # --- 修复结束 ---

        # 8. 最后，应用其他装备效果（比如暴击率）
        self.magic_resist += sum(getattr(eq, "magic_resist_bonus", 0) for eq in all_eq)
        self.crit_chance += sum(getattr(eq, "crit_bonus", 0) for eq in all_eq)

        # 9. 恢复血量百分比并最终计算
        self.hp = min(self.max_hp, self.max_hp * hp_percent)
        self.attack_interval = 6.0 / self.attack_speed
        print("角色属性已更新！")
    
    @property
    def all_equipment(self):
        eqs = []
        for eq_list in self.slots.values():
            # 筛选出不是 None 的真实装备
            eqs.extend([item for item in eq_list if item is not None])
        return eqs

# --- 3. 完整替换 equip 方法 ---
    def equip(self, eq_to_equip, specific_index=None):
        """装备一件物品，可以指定精确的槽位索引。"""
        slot = eq_to_equip.slot
        if slot not in self.SLOT_CAPACITY:
            raise ValueError(f"未知插槽：{slot}")

        # 如果指定了索引
        if specific_index is not None:
            if 0 <= specific_index < self.SLOT_CAPACITY[slot]:
                # 卸下目标槽位原有的物品
                unequipped_item = self.slots[slot][specific_index]
                # 穿上新物品
                self.slots[slot][specific_index] = eq_to_equip
                self.recalculate_stats()
                return unequipped_item # 返回被替换下的物品 (可能是None)
            else:
                return eq_to_equip # 索引无效，装备失败

        # 如果未指定索引，则自动寻找空位
        else:
            try:
                # 找到第一个空槽位 (值为None)
                empty_index = self.slots[slot].index(None)
                self.slots[slot][empty_index] = eq_to_equip
                self.recalculate_stats()
                return None # 成功装备到空槽，没有物品被替换
            except ValueError:
                # 如果找不到None，说明槽位已满
                # 对于单槽位，直接替换
                if self.SLOT_CAPACITY[slot] == 1:
                    unequipped_item = self.slots[slot][0]
                    self.slots[slot][0] = eq_to_equip
                    self.recalculate_stats()
                    return unequipped_item
                else: # 多槽位已满且未指定索引，则失败
                    print(f"警告: {slot} 插槽已满且未指定替换位置")
                    return eq_to_equip

# --- 4. 完整替换 unequip 方法 ---
    def unequip(self, eq_to_unequip):
        """从角色身上卸下指定的装备。"""
        slot = eq_to_unequip.slot
        if eq_to_unequip in self.slots[slot]:
            # 找到物品的索引
            index = self.slots[slot].index(eq_to_unequip)
            # 将该位置设置回 None
            self.slots[slot][index] = None
            self.recalculate_stats()
            return eq_to_unequip # 返回被卸下的物品
        return None
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
        if self.shield > 0: shield_absorbed = min(self.shield, mitigated_amount); self.shield -= shield_absorbed; mitigated_amount -= shield_absorbed
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
        for t in self.equipped_talents:
            if hasattr(t, "on_attack"): out = t.on_attack(self, target, actual_dmg);
            if out: extra_texts.extend(out)
        self._cd -= self.attack_interval; text = f"{self.name} → {target.name} 造成 {int(actual_dmg)} 点伤害"
        if is_crit: text += " (暴击!)"
        return text, extra_texts
    def perform_extra_attack(self, target):
        print(f"[{self.name}] 正在执行额外攻击！")
        is_crit = (random.random() < self.crit_chance); damage = self.attack * self.crit_multiplier if is_crit else self.attack
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
        if final_buff is None: final_buff = status; self.buffs.append(status); status.on_apply(self)
        if source is not None and source is not self and getattr(final_buff, "is_debuff", False):
            for t in self.equipped_talents:
                if hasattr(t, "on_inflict_debuff"): t.on_inflict_debuff(source, self, final_buff, added_stacks)
        if getattr(final_buff, "dispellable", False) and getattr(final_buff, "is_debuff", False):
            for t in self.equipped_talents:
                if hasattr(t, "on_debuff_applied"): t.on_debuff_applied(self, final_buff)
    add_buff, add_debuff = add_status, add_status
    def remove_buff(self, buff): self.buffs.remove(buff); buff.on_remove(self)
    def add_exp(self, amount):
        if self.hp <= 0: return []
        self.exp += amount; messages = [f"获得了 {amount} 点经验！ (当前: {self.exp}/{self.exp_to_next_level})"]
        if self.exp >= self.exp_to_next_level: messages.extend(self.level_up())
        return messages
    def level_up(self):
        level_up_messages = []
        while self.exp >= self.exp_to_next_level:
            self.level += 1; self.exp -= self.exp_to_next_level; self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
            self._innate_max_hp += 10; self._innate_attack += 2; self._innate_defense += 1
            self.recalculate_stats()
            level_up_messages.append(f"🎉 等级提升！现在是 {self.level} 级！"); level_up_messages.append("   生命+10，攻击+2，防御+1")
        return level_up_messages