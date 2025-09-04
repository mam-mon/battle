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
from ui import format_damage_log

RARITY_GOLD_VALUE = {"common": 10, "uncommon": 25, "rare": 60, "epic": 150, "legendary": 400, "mythic": 1000}

class Character:
    DEFAULT_SLOT_CAPACITY = {"weapon": 1, "offhand": 1, "helmet": 1, "armor": 1, "pants": 1, "accessory": 4}

    # File: Character.py (Replace this method)
    def __init__(self, name, hp, defense, magic_resist, attack, attack_speed,
                equipment=None, talents=None, id=None):

        self.id = id or name
        self.name, self.level, self.gold = name, 1, 0
        self.exp, self.exp_to_next_level, self.backpack = 0, 100, []
        self.SLOT_CAPACITY = self.DEFAULT_SLOT_CAPACITY.copy()
        self.max_talent_slots = 3
        self.learned_talents = talents or []
        
        # --- CORE FIX: Initialize equipped_talents with None placeholders ---
        self.equipped_talents = [None] * self.max_talent_slots
        
        self.buffs = []
        self.shield = 0
        self._cd = 0.0
        self.crit_chance = 0.0
        self.crit_multiplier = 1.5
        self.last_damage = 0
        self.last_hits = collections.deque(maxlen=5)
        self.damage_resistance = 0.0

        self._innate_max_hp, self._innate_defense, self._innate_attack, self._innate_attack_speed = hp, defense, attack, attack_speed
        self.magic_resist = magic_resist
        
        self.slots = {
            slot: [None] * capacity for slot, capacity in self.SLOT_CAPACITY.items()
        }
        
        for eq in (equipment or []):
            self.equip(eq)

        self.base_max_hp, self.base_defense, self.base_attack, self.base_attack_speed = 0, 0, 0, 0
        
        # Temporarily store learned talents to equip them after stats are ready
        initial_talents_to_equip = self.learned_talents[:]
        self.learned_talents = [] # Clear and re-learn to ensure no duplicates
        
        for talent in initial_talents_to_equip:
            self.learn_talent(talent)
            self.equip_talent(talent) # This will now work correctly

        # Final stat calculation after initial equipment and talents
        self.recalculate_stats()
        self.hp = self.max_hp
            
    def add_gold(self, amount, source=""):
        if amount <= 0: return None
        self.gold += amount
        source_text = f" ({source})" if source else ""
        return f"获得了 {amount} G！{source_text} (当前: {self.gold} G)"

    # 文件: Character.py (替换这个函数)

    def pickup_item(self, item_to_pickup):
        """拾取物品，包含更完善的重复判定和调试信息。"""
        from Equips import UPGRADE_MAP
        
        item_name = getattr(item_to_pickup, 'display_name', item_to_pickup.__class__.__name__)
        print(f"\n--- 正在尝试拾取: {item_name} ---")

        all_current_items = self.backpack + self.all_equipment
        
        # 判定规则 1: 是否已存在同名物品
        is_duplicate_by_name = any(getattr(item, 'display_name', '') == item_name for item in all_current_items)
        if is_duplicate_by_name:
            print(f"调试信息: 发现同名物品 '{item_name}'，判定为重复。")

        # 判定规则 2: 是否已拥有该物品的升级版 (新功能)
        is_inferior_version = False
        item_class = item_to_pickup.__class__
        if item_class in UPGRADE_MAP:
            upgraded_class = UPGRADE_MAP[item_class]
            if any(isinstance(item, upgraded_class) for item in all_current_items):
                is_inferior_version = True
                print(f"调试信息: 已拥有 '{item_name}' 的升级版，判定为重复。")

        # 最终判定
        is_duplicate = is_duplicate_by_name or is_inferior_version
        print(f"最终判定结果: is_duplicate = {is_duplicate}")

        if is_duplicate:
            print("执行操作: 转化为金币。")
            rarity = getattr(item_to_pickup, 'rarity', 'common')
            gold_value = RARITY_GOLD_VALUE.get(rarity, 5)
            return self.add_gold(gold_value, source=f"转化({item_name})")
        else:
            print("执行操作: 放入背包。")
            self.backpack.append(item_to_pickup)
            return f"物品「{item_name}」已放入你的背包。"
        
    # ... (其他所有方法都保持不变)
    def learn_talent(self, talent_to_learn):
        if not any(isinstance(t, talent_to_learn.__class__) for t in self.learned_talents):
            self.learned_talents.append(talent_to_learn)
            print(f"学会了新天赋: {talent_to_learn.display_name}")
            return True
        return False

    # File: Character.py (Replace this method)
    def equip_talent(self, talent_to_equip, specific_index=None):
        if talent_to_equip not in self.learned_talents:
            print("尚未学会该天赋！")
            return False
        if talent_to_equip in self.equipped_talents:
            print("该天赋已被装备。")
            return False

        # If a specific slot is targeted
        if specific_index is not None:
            if 0 <= specific_index < self.max_talent_slots:
                if self.equipped_talents[specific_index] is None:
                    self.equipped_talents[specific_index] = talent_to_equip
                    self.recalculate_stats()
                    print(f"已装备天赋: {talent_to_equip.display_name} 到槽位 {specific_index}")
                    return True
                else: # Slot is occupied, this should be handled by swap logic in the UI
                    return False 
        
        # If no specific slot, find the first empty one
        else:
            try:
                empty_index = self.equipped_talents.index(None)
                self.equipped_talents[empty_index] = talent_to_equip
                self.recalculate_stats()
                print(f"已装备天赋: {talent_to_equip.display_name} 到槽位 {empty_index}")
                return True
            except ValueError:
                print("天赋槽已满！")
                return False
            
    # File: Character.py (Replace this method)
    def unequip_talent(self, talent_to_unequip):
        if talent_to_unequip not in self.equipped_talents:
            return
        # Find the talent and replace it with None, instead of removing it
        index = self.equipped_talents.index(talent_to_unequip)
        self.equipped_talents[index] = None
        self.recalculate_stats()
        print(f"已卸下天赋: {talent_to_unequip.display_name}")
        
    def on_enter_combat(self):
        self.buffs.clear(); self.hp = self.max_hp; self.shield = 0; self._cd = 0.0;

        # 新增逻辑：重置装备的战斗内状态
        for eq in self.all_equipment:
            if isinstance(eq, Equips.AdventurersPouch):
                eq.atk_bonus = 0 # 战斗准备时，将钱袋的加成清零

        # 重置完后再重算一次属性，确保一个干净的状态
        self.recalculate_stats() 
        print(f"{self.name} 已进入战斗准备状态！")

    # 文件: Character.py (请用这个新版本替换整个 update 函数)

    # 文件: Character.py (还原 update 函数)
    def update(self, dt) -> list[str]:
        texts = []
        for buff in list(self.buffs):
            if hasattr(buff, "on_tick"):
                res = buff.on_tick(self, dt)
                if isinstance(res, str) and res:
                    texts.append(res) # 恢复成只处理字符串
        for eq in self.all_equipment:
            if hasattr(eq, "on_tick"):
                res = eq.on_tick(self, dt)
                if isinstance(res, str) and res:
                    texts.append(res)
        return texts

    def recalculate_stats(self):
        hp_percent = self.hp / self.max_hp if hasattr(self, 'max_hp') and self.max_hp > 0 else 1
        self.base_max_hp = self._innate_max_hp
        self.base_defense = self._innate_defense
        self.base_attack = self._innate_attack
        self.base_attack_speed = self._innate_attack_speed
        all_eq = self.all_equipment
        self.base_max_hp += sum(getattr(eq, "hp_bonus", 0) for eq in all_eq)
        self.base_defense += sum(getattr(eq, "def_bonus", 0) for eq in all_eq)
        self.base_attack += sum(getattr(eq, "atk_bonus", 0) for eq in all_eq)
        self.base_attack_speed += sum(getattr(eq, "as_bonus", 0) for eq in all_eq)
        self.max_hp = self.base_max_hp
        self.defense = self.base_defense
        self.attack = self.base_attack
        self.attack_speed = self.base_attack_speed
        self.crit_chance = 0.0 
        self.magic_resist = 3 
        self.damage_resistance = 0.0
        self.SLOT_CAPACITY = self.DEFAULT_SLOT_CAPACITY.copy()
        for talent in self.equipped_talents:
            if hasattr(talent, 'on_init'):
                talent.on_init(self)
        for slot, required_capacity in self.SLOT_CAPACITY.items():
            current_slots = self.slots.get(slot, [])
            current_capacity = len(current_slots)
            if current_capacity < required_capacity:
                current_slots.extend([None] * (required_capacity - current_capacity))
            elif current_capacity > required_capacity:
                extra_items = current_slots[required_capacity:]
                for item in extra_items:
                    if item: self.backpack.append(item)
                self.slots[slot] = current_slots[:required_capacity]
        
        # --- 新增：处理特殊Buff和Debuff对属性的直接影响 ---
        self.defense -= sum(b.stacks for b in self.buffs if isinstance(b, Buffs.SunderDebuff))
        self.defense = max(0, self.defense) # 防御不能为负
        if any(isinstance(b, Buffs.FrenzyBuff) for b in self.buffs):
            self.attack_speed *= 2
        # --- 新增结束 ---

        self.magic_resist += sum(getattr(eq, "magic_resist_bonus", 0) for eq in all_eq)
        self.crit_chance += sum(getattr(eq, "crit_bonus", 0) for eq in all_eq)
        self.hp = min(self.max_hp, self.max_hp * hp_percent)
        self.attack_interval = 6.0 / self.attack_speed if self.attack_speed > 0 else 999
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
        """
        角色受到伤害的核心处理函数。
        增加了“记录最后攻击者”的功能。
        """
        # ### 核心修复 2：记录伤害来源 ###

        # 触发钩子：受到伤害前
        for buff in list(self.buffs):
            if hasattr(buff, 'before_take_damage'): buff.before_take_damage(self, packet)
        for eq in self.all_equipment:
            if hasattr(eq, 'before_take_damage'): eq.before_take_damage(self, packet)

        initial_amount_after_hooks = packet.amount
        final_shield_absorbed = 0

        # 1. 护盾吸收
        if self.shield > 0 and packet.amount > 0:
            absorbed = min(self.shield, packet.amount)
            self.shield -= absorbed
            packet.amount -= absorbed
            final_shield_absorbed = absorbed

        # 2. 计算伤害减免
        final_hp_deduction = 0
        if packet.amount > 0:
            reduction = 0.0
            if packet.damage_type not in [DamageType.TRUE] and not packet.ignores_armor:
                if packet.damage_type == DamageType.PHYSICAL:
                    reduction = self.defense / (self.defense + 100)
                elif packet.damage_type == DamageType.MAGIC:
                    reduction = self.magic_resist / (self.magic_resist + 100)
            final_hp_deduction = packet.amount * (1.0 - reduction)

        # 3. 最终扣血
        final_hp_deduction = max(0, int(final_hp_deduction))
        self.hp -= final_hp_deduction
        if self.hp < 0: self.hp = 0

        # 4. 触发钩子：受到伤害后
        if packet.source:
            self.on_attacked(packet.source, final_hp_deduction)

        # 5. 返回伤害报告
        return {
            "source": packet.source,
            "target": self,
            "final_amount": final_hp_deduction,
            "shield_absorbed": int(final_shield_absorbed),
            "damage_type": packet.damage_type,
            "is_critical": packet.is_critical,
            "is_dot": packet.is_dot,
            "is_fatal": self.hp <= 0,
        }

    # --- 附带修改：确保 on_attacked 也被调用 ---
    # (你的代码中缺少这个函数，请在 take_damage 函数下方添加它)
    def on_attacked(self, attacker, dmg):
        """每次被攻击后触发"""
        for b in self.buffs:
            if hasattr(b, "on_attacked"):
                b.on_attacked(self, attacker, dmg)
        for eq in self.all_equipment:
            if hasattr(eq, "on_attacked"):
                eq.on_attacked(self, attacker, dmg)

    def try_attack(self, target, dt):
        if any(getattr(b, "disable_attack", False) for b in self.buffs): return None
        self._cd += dt
        if self._cd < self.attack_interval or self.hp <= 0: return None

        # ... (准备伤害包裹和调用钩子的部分保持不变) ...
        is_crit = (random.random() < self.crit_chance)
        damage = self.attack * self.crit_multiplier if is_crit else self.attack
        packet = DamagePacket(amount=damage, damage_type=DamageType.PHYSICAL, source=self, is_critical=is_crit)
        
        for t in self.equipped_talents:
            if t and hasattr(t, "before_attack"): t.before_attack(self, target, packet)
        for eq in self.all_equipment:
            if hasattr(eq, "before_attack"): eq.before_attack(self, target, packet)

        damage_details = target.take_damage(packet)
        actual_dmg = damage_details["final_amount"]
        
        # ... (攻击后钩子逻辑保持不变) ...
        extra_texts = []
        for t in self.equipped_talents:
            if t and hasattr(t, "on_attack"):
                out = t.on_attack(self, target, actual_dmg)
                if out: extra_texts.extend(out)
        self._cd -= self.attack_interval

        log_parts = format_damage_log(damage_details, action_name="普攻")

        # 4. 返回这个富文本列表和额外信息
        return (log_parts, extra_texts)


    def perform_extra_attack(self, target):
        """
        执行一次标准化的额外攻击。
        这个方法现在会自己处理伤害计算和日志记录。
        """
        from battle_logger import battle_logger, format_damage_log
        
        # 1. 准备伤害包裹 (与 try_attack 逻辑一致)
        is_crit = (random.random() < self.crit_chance)
        damage = self.attack * self.crit_multiplier if is_crit else self.attack
        packet = DamagePacket(amount=damage, damage_type=DamageType.PHYSICAL, source=self, is_critical=is_crit)
        
        # 2. 触发攻击前钩子
        for eq in self.all_equipment:
            if hasattr(eq, "before_attack"): eq.before_attack(self, target, packet)
        
        # 3. 造成伤害并获取伤害报告
        damage_details = target.take_damage(packet)
        actual_dmg = damage_details["final_amount"]
        
        # 4. 使用标准工具格式化日志并播报
        log_parts = format_damage_log(damage_details, action_name="额外攻击")
        battle_logger.log(log_parts)
        
        # 5. 触发攻击后钩子
        for eq in self.all_equipment:
            if hasattr(eq, "after_attack"): eq.after_attack(self, target, actual_dmg)
        if is_crit:
            for eq in self.all_equipment:
                if hasattr(eq, "on_critical"): eq.on_critical(self, target, actual_dmg)
        else:
            for eq in self.all_equipment:
                if hasattr(eq, "on_non_critical"): eq.on_non_critical(self, target, actual_dmg)
                

    
    def heal(self, amount: float, combat_target=None) -> float:
        # 钩子：治疗前
        for buff in list(self.buffs):
            if hasattr(buff, 'before_healed'):
                amount = buff.before_healed(self, amount)

        healed = min(self.max_hp - self.hp, amount)
        if healed <= 0: return 0.0
        self.hp += healed

        # 钩子：治疗后
        for talent in list(self.equipped_talents):
            if talent and hasattr(talent, 'on_healed'):
                talent.on_healed(self, healed, combat_target)

        return healed
        
    def add_status(self, status: Buffs.Buff, *, source: "Character" = None):
        final_buff = None
        added_stacks = status.stacks
        for b in self.buffs:
            if isinstance(b, status.__class__):
                if b.max_stacks == 1:
                    b.remaining = b.duration
                else:
                    b.stacks = min(b.stacks + status.stacks, b.max_stacks)
                final_buff = b
                break
        if final_buff is None:
            final_buff = status
            self.buffs.append(status)
            status.on_apply(self)
        
        # --- 新增的钩子 ---
        # 触发装备的 on_buff_applied 效果
        for eq in self.all_equipment:
            if hasattr(eq, 'on_buff_applied'):
                eq.on_buff_applied(self, final_buff)
        # --- 钩子结束 ---

        if source is not None and source is not self and getattr(final_buff, "is_debuff", False):
            for t in source.equipped_talents: # 注意：这里检查的是 source 的天赋
                if hasattr(t, "on_inflict_debuff"):
                    t.on_inflict_debuff(source, self, final_buff, added_stacks)
        if getattr(final_buff, "dispellable", False) and getattr(final_buff, "is_debuff", False):
            for t in self.equipped_talents:
                if hasattr(t, "on_debuff_applied"):
                    t.on_debuff_applied(self, final_buff)
                    
    add_buff, add_debuff = add_status, add_status

    def remove_buff(self, buff): self.buffs.remove(buff); buff.on_remove(self)

    def add_exp(self, amount):
        if self.hp <= 0: return []
        
        original_amount = amount
        if any(isinstance(t, Talents.Adventurer) for t in self.equipped_talents):
            bonus_amount = int(original_amount * 0.5)
            amount += bonus_amount
            print(f"[冒险者] 天赋触发！额外获得 {bonus_amount} 点经验！")
        self.exp += amount
        messages = [f"获得了 {amount} 点经验！ (当前: {self.exp}/{self.exp_to_next_level})"]
        if self.exp >= self.exp_to_next_level:
            messages.extend(self.level_up())
        return messages

    def level_up(self):
        level_up_messages = []
        while self.exp >= self.exp_to_next_level:
            self.level += 1; self.exp -= self.exp_to_next_level; self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
            self._innate_max_hp += 10; self._innate_attack += 2; self._innate_defense += 1
            self.recalculate_stats()
            level_up_messages.append(f"🎉 等级提升！现在是 {self.level} 级！"); level_up_messages.append("   生命+10，攻击+2，防御+1")
        return level_up_messages
    
    def gain_level(self, levels=1):
        """(沙盒专用) 提升等级并增加基础属性"""
        self.level += levels
        # 按照 level_up 的标准增加固有属性
        self._innate_max_hp += 10 * levels
        self._innate_attack += 2 * levels
        self._innate_defense += 1 * levels
        self.recalculate_stats()
        self.hp = self.max_hp # 升级后回满血
        print(f"等级提升至 {self.level} 级。")

    def lose_level(self, levels=1):
        """(沙盒专用) 降低等级并减少基础属性"""
        # 防止降到1级以下
        actual_levels_lost = min(levels, self.level - 1)
        if actual_levels_lost <= 0:
            return
            
        self.level -= actual_levels_lost
        self._innate_max_hp -= 10 * actual_levels_lost
        self._innate_attack -= 2 * actual_levels_lost
        self._innate_defense -= 1 * actual_levels_lost
        self.recalculate_stats()
        self.hp = self.max_hp # 降级后也回满血
        print(f"等级降低至 {self.level} 级。")