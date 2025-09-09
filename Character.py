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
from settings import CRYSTALS_PER_RARITY, RARITY_COLORS, UPGRADE_COST_PER_RARITY
from ui import format_damage_log

RARITY_GOLD_VALUE = {"common": 10, "uncommon": 25, "rare": 60, "epic": 150, "legendary": 400, "mythic": 1000}

class Character:
    DEFAULT_SLOT_CAPACITY = {"weapon": 1, "offhand": 1, "helmet": 1, "armor": 1, "pants": 1, "accessory": 4}

    def __init__(self, name, hp, defense, magic_resist, attack, attack_speed,
                equipment=None, talents=None, id=None):

        self.id = id or name
        self.name, self.level, self.gold = name, 1, 0
        self.exp, self.exp_to_next_level = 0, self._calculate_exp_for_level(1)
        self.backpack = []
        self.SLOT_CAPACITY = self.DEFAULT_SLOT_CAPACITY.copy()
        self.refinement_crystals = 0 # <-- 新增：淬炼结晶

        self.strength = 5
        self.vitality = 5
        self.dexterity = 5
        self.toughness = 5
        self.attribute_points = 0 # 可用属性点

        self.base_max_hp, self.base_defense, self.base_magic_resist, self.base_attack, self.base_attack_speed = 0, 0, 0, 0, 0
        self.base_crit_chance = 0.0
        self.base_crit_multiplier = 1.5

        self.max_talent_slots = 3
        self.learned_talents = talents or []
        self.equipped_talents = [None] * self.max_talent_slots
        self.buffs = []
        self.shield = 0
        self._cd = 0.0
        self.damage_resistance = 0.0

        # --- 修改：innate (固有的) 属性现在代表角色的绝对基础值 ---
        self._innate_max_hp, self._innate_defense, self._innate_magic_resist, self._innate_attack, self._innate_attack_speed = hp, defense, magic_resist, attack, attack_speed

        self.slots = { slot: [None] * capacity for slot, capacity in self.SLOT_CAPACITY.items() }

        for eq in (equipment or []):
            if getattr(eq, 'slot', None) is not None: self.equip(eq)
            else: self.backpack.append(eq)

        initial_talents_to_equip = self.learned_talents[:]
        self.learned_talents = [] 

        for talent in initial_talents_to_equip:
            self.learn_talent(talent)
            self.equip_talent(talent)

        self.recalculate_stats()
        self.hp = self.max_hp
        
    def add_gold(self, amount, source=""):
        if amount <= 0: return None
        self.gold += amount
        source_text = f" ({source})" if source else ""
        return f"获得了 {amount} G！{source_text} (当前: {self.gold} G)"

    def pickup_item(self, item_to_pickup):
        """拾取物品，包含更完善的重复判定和调试信息。"""
        from Equips import UPGRADE_MAP
        item_name = getattr(item_to_pickup, 'display_name', item_to_pickup.__class__.__name__)
        all_current_items = self.backpack + self.all_equipment
        is_duplicate_by_name = any(getattr(item, 'display_name', '') == item_name for item in all_current_items)
        is_inferior_version = False
        item_class = item_to_pickup.__class__
        if item_class in UPGRADE_MAP:
            upgraded_class = UPGRADE_MAP[item_class]
            if any(isinstance(item, upgraded_class) for item in all_current_items):
                is_inferior_version = True
        
        is_duplicate = is_duplicate_by_name or is_inferior_version

        if is_duplicate:
            rarity = getattr(item_to_pickup, 'rarity', 'common')
            gold_value = RARITY_GOLD_VALUE.get(rarity, 5)
            self.add_gold(gold_value) # 仍然获得金币
            
            # --- 核心修改：根据品质增加淬炼结晶 ---
            crystal_value = CRYSTALS_PER_RARITY.get(rarity, 0)
            self.refinement_crystals += crystal_value
            
            # 返回包含两种资源的新消息
            return f"转化({item_name}): 获得了 {gold_value} G 和 {crystal_value} 淬炼结晶。"
        else:
            self.backpack.append(item_to_pickup)
            return f"物品「{item_name}」已放入你的背包。"
        
    def learn_talent(self, talent_to_learn):
        if not any(isinstance(t, talent_to_learn.__class__) for t in self.learned_talents):
            self.learned_talents.append(talent_to_learn)
            print(f"学会了新天赋: {talent_to_learn.display_name}")
            return True
        return False

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

    def unequip_talent(self, talent_to_unequip):
        if talent_to_unequip not in self.equipped_talents:
            return
        # Find the talent and replace it with None, instead of removing it
        index = self.equipped_talents.index(talent_to_unequip)
        self.equipped_talents[index] = None
        self.recalculate_stats()
        print(f"已卸下天赋: {talent_to_unequip.display_name}")
        
    def on_enter_combat(self):
        self.buffs.clear(); self.shield = 0; self._cd = 0.0;

        # 新增逻辑：重置装备的战斗内状态
        for eq in self.all_equipment:
            if isinstance(eq, Equips.AdventurersPouch):
                eq.atk_bonus = 0 # 战斗准备时，将钱袋的加成清零

        # 重置完后再重算一次属性，确保一个干净的状态
        self.recalculate_stats() 
        print(f"{self.name} 已进入战斗准备状态！")

# Character.py

    def update(self, dt) -> list[str]:
        texts = []
        # 这个函数只处理Buff和物品的计时效果
        for item in self.all_active_items:
            if hasattr(item, "on_tick"):
                res = item.on_tick(self, dt)
                if isinstance(res, str) and res:
                    texts.append(res)
        for buff in list(self.buffs):
            if hasattr(buff, "on_tick"):
                res = buff.on_tick(self, dt)
                if isinstance(res, str) and res:
                    texts.append(res)
        return texts
    
    def recalculate_stats(self):
        hp_percent = self.hp / self.max_hp if hasattr(self, 'max_hp') and self.max_hp > 0 else 1

        all_eq = self.all_equipment
        self.base_max_hp = sum(getattr(eq, "hp_bonus", 0) for eq in all_eq)
        self.base_defense = sum(getattr(eq, "def_bonus", 0) for eq in all_eq)
        self.base_magic_resist = sum(getattr(eq, "magic_resist_bonus", 0) for eq in all_eq)
        self.base_attack = sum(getattr(eq, "atk_bonus", 0) for eq in all_eq)
        self.base_attack_speed = sum(getattr(eq, "as_bonus", 0) for eq in all_eq)
        self.base_crit_chance = sum(getattr(eq, "crit_bonus", 0) for eq in all_eq)

        # --- 核心修复：从装备中累加暴击伤害加成 ---
        self.base_crit_multiplier = 1.5 + sum(getattr(eq, "crit_dmg_bonus", 0) for eq in all_eq)
        # --- 修复结束 ---

        self.damage_resistance = 0.0

        self.SLOT_CAPACITY = self.DEFAULT_SLOT_CAPACITY.copy()
        for talent in self.equipped_talents:
            if talent and hasattr(talent, 'on_init'):
                talent.on_init(self)

        self.max_hp = self._innate_max_hp + (self.vitality * 5) + self.base_max_hp
        self.attack = self._innate_attack + (self.strength * 2) + self.base_attack
        self.defense = self._innate_defense + (self.toughness * 1) + (self.strength // 2) + self.base_defense
        self.magic_resist = self._innate_magic_resist + (self.toughness // 2) + self.base_magic_resist
        self.attack_speed = self._innate_attack_speed + (self.dexterity * 0.01) + self.base_attack_speed
        self.crit_chance = self.base_crit_chance + (self.dexterity // 5) * 0.01

        # --- 核心修复：计算最终的暴击伤害倍率 ---
        self.crit_multiplier = self.base_crit_multiplier
        # --- 修复结束 ---

        self.defense -= sum(b.stacks for b in self.buffs if isinstance(b, Buffs.SunderDebuff))
        self.defense = max(0, self.defense)
        if any(isinstance(b, Buffs.FrenzyBuff) for b in self.buffs):
            self.attack_speed *= 2

        self.hp = min(self.max_hp, self.max_hp * hp_percent)
        self.attack_interval = 6.0 / self.attack_speed if self.attack_speed > 0 else 999
        print("角色属性已更新！")

    @property
    def all_equipment(self):
        eqs = []
        for eq_list in self.slots.values():
            eqs.extend([item for item in eq_list if item is not None])
        return eqs

    @property
    def all_active_items(self):
        """返回一个包含所有当前生效物品的列表（已装备的 + 背包中的珍贵物品）。"""
        active_items = self.all_equipment.copy() # 先获取所有已装备的物品
        # 再从背包中筛选出所有 type 为 'precious' 的物品并添加进来
        active_items.extend([item for item in self.backpack if getattr(item, 'type', None) == 'precious'])
        return active_items

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
        # --- 核心修改：使用新的“智能列表” ---
        for item in self.all_active_items: # <-- 从 all_equipment 改为 all_active_items
            if hasattr(item, 'before_take_damage'): item.before_take_damage(self, packet)
        for buff in list(self.buffs):
            if hasattr(buff, 'before_take_damage'): buff.before_take_damage(self, packet)

        initial_amount_after_hooks = packet.amount
        final_shield_absorbed = 0
        if self.shield > 0 and packet.amount > 0:
            absorbed = min(self.shield, packet.amount)
            self.shield -= absorbed
            packet.amount -= absorbed
            final_shield_absorbed = absorbed

        final_hp_deduction = 0
        if packet.amount > 0:
            reduction = 0.0
            if packet.damage_type not in [DamageType.TRUE] and not packet.ignores_armor:
                if packet.damage_type == DamageType.PHYSICAL:
                    reduction = self.defense / (self.defense + 100)
                elif packet.damage_type == DamageType.MAGIC:
                    reduction = self.magic_resist / (self.magic_resist + 100)
            final_hp_deduction = packet.amount * (1.0 - reduction)

        final_hp_deduction = max(0, int(final_hp_deduction))
        self.hp -= final_hp_deduction
        if self.hp < 0: self.hp = 0

        if packet.source:
            self.on_attacked(packet.source, final_hp_deduction)

        return {
            "source": packet.source, "target": self,
            "final_amount": final_hp_deduction, "shield_absorbed": int(final_shield_absorbed),
            "damage_type": packet.damage_type, "is_critical": packet.is_critical,
            "is_dot": packet.is_dot, "is_fatal": self.hp <= 0,
        }

    def on_attacked(self, attacker, dmg):
        """每次被攻击后触发"""
        # --- 核心修改：使用新的“智能列表” ---
        for item in self.all_active_items: # <-- 从 all_equipment 改为 all_active_items
            if hasattr(item, "on_attacked"):
                item.on_attacked(self, attacker, dmg)
        for b in self.buffs:
            if hasattr(b, "on_attacked"):
                b.on_attacked(self, attacker, dmg)

    def try_attack(self, target, dt):
        if any(getattr(b, "disable_attack", False) for b in self.buffs): return None
        self._cd += dt
        if self._cd < self.attack_interval or self.hp <= 0: return None

        is_crit = (random.random() < self.crit_chance)
        damage = self.attack * self.crit_multiplier if is_crit else self.attack
        packet = DamagePacket(amount=damage, damage_type=DamageType.PHYSICAL, source=self, is_critical=is_crit)

        for t in self.equipped_talents:
            if t and hasattr(t, "before_attack"): t.before_attack(self, target, packet)

        # --- 核心修改：使用新的“智能列表” ---
        for item in self.all_active_items: # <-- 从 all_equipment 改为 all_active_items
            if hasattr(item, "before_attack"): item.before_attack(self, target, packet)

        damage_details = target.take_damage(packet)
        actual_dmg = damage_details["final_amount"]

        extra_texts = []
        for t in self.equipped_talents:
            if t and hasattr(t, "on_attack"):
                out = t.on_attack(self, target, actual_dmg)
                if out: extra_texts.extend(out)
        self._cd -= self.attack_interval

        log_parts = format_damage_log(damage_details, action_name="普攻")

        return (log_parts, extra_texts, damage_details)

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

    def _calculate_exp_for_level(self, level: int) -> int:
        """根据等级计算升到下一级所需的总经验值。"""
        if level <= 1:
            return 10 # 1级升2级所需经验

        # 我们的新公式
        base_exp = 10   # 基础经验值
        power = 2     # 幂指数 (决定曲线陡峭程度)
        coefficient = 20 # 等级系数 (控制总体成长速度)

        required_exp = base_exp + int(coefficient * ((level - 1) ** power))

        # 将结果处理为5的倍数，看起来更整洁
        return (required_exp // 5) * 5

# Character.py (替换整个 level_up 函数)

    def level_up(self):
        level_up_messages = []
        while self.exp >= self.exp_to_next_level:
            self.level += 1
            self.exp -= self.exp_to_next_level
            self.exp_to_next_level = self._calculate_exp_for_level(self.level)

            # --- 核心修改：不再直接加属性，而是给予属性点 ---
            points_gained = 3 # 每级获得3个属性点
            self.attribute_points += points_gained

            # 升级后自动回满血
            self.hp = self.max_hp

            level_up_messages.append(f"🎉 等级提升！现在是 {self.level} 级！")
            level_up_messages.append(f"   获得了 {points_gained} 点属性点！生命已完全恢复！")
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

# Character.py (在文件末尾追加这个新函数)

    def upgrade_equipment(self, item_to_upgrade):
        """
        处理装备升级的核心逻辑。
        接收一件装备，检查条件，执行升级，并返回结果信息。
        """
        from Equips import UPGRADE_MAP
        
        # 1. 检查装备是否可升级
        item_class = item_to_upgrade.__class__
        if item_class not in UPGRADE_MAP:
            return "此物品已是最高品质，无法再升级。"
            
        # 2. 检查升级所需结晶是否足够
        rarity = getattr(item_to_upgrade, 'rarity', 'common')
        cost = UPGRADE_COST_PER_RARITY.get(rarity, 9999)
        if self.refinement_crystals < cost:
            return f"淬炼结晶不足！需要 {cost}，当前拥有 {self.refinement_crystals}。"
            
        # 3. 执行升级
        self.refinement_crystals -= cost
        upgraded_class = UPGRADE_MAP[item_class]
        upgraded_item = upgraded_class()
        
        # 4. 移除旧装备，并用新装备替换
        was_equipped = False
        # 检查是否在已装备的物品中
        for slot_type, items in self.slots.items():
            if item_to_upgrade in items:
                index = items.index(item_to_upgrade)
                self.slots[slot_type][index] = upgraded_item # 直接在原槽位替换
                was_equipped = True
                break
        
        # 如果不在装备槽里，那肯定在背包里
        if not was_equipped and item_to_upgrade in self.backpack:
            self.backpack.remove(item_to_upgrade)
            self.backpack.append(upgraded_item) # 将新物品放入背包
            
        self.recalculate_stats() # 升级后重算属性
        return f"淬炼成功！「{upgraded_item.display_name}」已升级！消耗 {cost} 结晶。"