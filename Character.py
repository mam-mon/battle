# Character.py
import pygame
import sys
import time
import collections
import math
import random
import pygame
from rich.console import Console
console = Console()

# 导入您的游戏逻辑文件
import Buffs
import Talents
import Equips

class Character:
    # 定义插槽及其容量
    SLOT_CAPACITY = {
        "weapon":    1,
        "offhand":   1,
        "helmet":    1,
        "armor":     1,
        "pants":     1,
        "accessory": 4,
    }

    def __init__(self, name, hp, defense, magic_resist, attack, attack_speed,
                 equipment=None, talents=None):
        self.name = name
        self.level = 1
        self.exp = 0
        self.exp_to_next_level = 100 #升到下一级所需经验
        self.backpack = []

        # ———— 1) 先把“角色固有”存下来 ————
        self._innate_max_hp      = hp
        self._innate_defense     = defense
        self._innate_attack      = attack
        self._innate_attack_speed= attack_speed
        self.magic_resist        = magic_resist

        # ———— 2) 从装备里收集“基础加成” ————
        equipment = equipment or []
        self._eq_hp_bonus        = sum(getattr(eq, "hp_bonus", 0) for eq in equipment)
        self._eq_def_bonus       = sum(getattr(eq, "def_bonus", 0) for eq in equipment)
        self._eq_atk_bonus       = sum(getattr(eq, "atk_bonus", 0) for eq in equipment)
        self._eq_as_bonus        = sum(getattr(eq, "as_bonus", 0) for eq in equipment)
        # …… 如果还有其他基础属性，也同理收集

        # ———— 3) 定义“基础属性”字段，只来自 天赋/天生 + 装备 ————
        self.base_max_hp         = self._innate_max_hp + self._eq_hp_bonus
        self.base_defense        = self._innate_defense + self._eq_def_bonus
        self.base_attack         = self._innate_attack + self._eq_atk_bonus
        self.base_attack_speed   = self._innate_attack_speed + self._eq_as_bonus

        # ———— 4) 初始化“当前属性”为基础值 + 额外buff增益 ————
        self.max_hp       = self.base_max_hp
        self.hp           = self.max_hp
        self.defense      = self.base_defense
        self.attack       = self.base_attack
        self.attack_speed = self.base_attack_speed
        self.attack_interval = 6.0 / self.attack_speed
        
        self.shield = 0
        self._cd             = 0.0
        self.crit_chance     = 0.0
        self.crit_multiplier = 1.5
        self.last_damage     = 0
        self.last_hits       = collections.deque(maxlen=5)
        self.buffs           = []
        self.damage_resistance = 0.0  

        # 先挂载天赋并调用 on_init，让它们可修改 SLOT_CAPACITY
        self.talents = talents or []
        for t in self.talents:
            t.on_init(self)

        # 根据（可能已被天赋修改的）SLOT_CAPACITY 初始化插槽
        self.slots = {slot: [] for slot in self.SLOT_CAPACITY}

        # 装备挂载
        for eq in (equipment or []):
            self.equip(eq)
        
    @property
    def all_equipment(self):
        # 扁平化所有装备，方便遍历调用钩子
        eqs = []
        for eq_list in self.slots.values():
            eqs.extend(eq_list)
        return eqs

    def equip(self, eq_to_equip):
        """装备一件物品，如果插槽已满，则返回被替换的物品"""
        slot = eq_to_equip.slot
        if slot not in self.SLOT_CAPACITY:
            raise ValueError(f"未知插槽：{slot}")
        
        # 如果插槽已满
        if len(self.slots[slot]) >= self.SLOT_CAPACITY[slot]:
            # 暂时只处理单容量插槽的替换
            if self.SLOT_CAPACITY[slot] == 1:
                unequipped_item = self.slots[slot][0]
                self.slots[slot][0] = eq_to_equip
                return unequipped_item
            else:
                raise ValueError(f"{slot} 插槽已满")
        
        # 如果插槽未满
        self.slots[slot].append(eq_to_equip)
        return None # 表示没有物品被替换

    def unequip(self, eq_to_unequip):
        """从身上卸下一件指定的装备"""
        slot = eq_to_unequip.slot
        if eq_to_unequip in self.slots[slot]:
            self.slots[slot].remove(eq_to_unequip)
            return eq_to_unequip
        return None

    def recalculate_stats(self):
        """根据当前装备重新计算所有属性"""
        # (这个方法在真正的游戏中非常重要，用于更新因装备变化带来的属性增减)
        # (为简化起见，我们暂时省略具体实现，但保留这个接口)
        print("重新计算角色属性...")
    def heal(self, amount: float) -> float:
        """
        给自己回血：
        1) 计算实际生效值 healed = min(max_hp - hp, amount)
        2) hp += healed
        3) 通知所有 Buff 的 on_healed(wearer, healed)
        4) 返回 healed，用于累加
        """
        healed = min(self.max_hp - self.hp, amount)
        if healed <= 0:
            return 0.0
        self.hp += healed
        # 通知 Buff
        for buff in list(self.buffs):
            if hasattr(buff, "on_healed"):
                buff.on_healed(self, healed)
        return healed
                         
    def add_status(self, status: Buffs.Buff, *, source: "Character" = None):
        """
        添加任意状态（Buff 或 Debuff）：
         - 按 max_stacks 合并或刷新同类 Buff
         - 触发 on_apply（仅新增时）
         - 通知施加者的天赋 on_inflict_debuff
         - 通知自身的天赋 on_debuff_applied
        """
        final_buff = None
        
        added_stacks = status.stacks
        # —— 尝试合并或刷新 —— #
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
    
        # ✅ on_inflict_debuff（如竹叶青）
        if source is not None and source is not self and getattr(final_buff, "is_debuff", False):
            for t in source.talents:
                if hasattr(t, "on_inflict_debuff"):
                    t.on_inflict_debuff(source, self, final_buff, added_stacks)
    
        # ✅ on_debuff_applied（如自然之心）
        if getattr(final_buff, "dispellable", False) and getattr(final_buff, "is_debuff", False):
            for t in self.talents:
                if hasattr(t, "on_debuff_applied"):
                    t.on_debuff_applied(self, final_buff)
    

    add_buff   = add_status
    add_debuff = add_status

    def remove_buff(self, buff):
        """移除一个 Buff，并触发 on_remove"""
        self.buffs.remove(buff)
        buff.on_remove(self)            

    def update(self, dt) -> list[str]:
        """
        每帧调用，触发 Buff.on_tick。
        收集所有 on_tick 返回的文本，返回一个字符串列表。
        """
        texts = []
        for buff in list(self.buffs):
            if hasattr(buff, "on_tick"):
                res = buff.on_tick(self, dt)
                if isinstance(res, str) and res:
                    texts.append(res)
        return texts
    
    def take_damage(self, dmg, attacker=None):
        if attacker is not None:
        #    print(f"[警告] take_damage 缺失 attacker，dmg={dmg}, self={self.name}")
        #else:
            # ✅ 仅记录真实攻击者（如普攻），排除系统伤害
            self._last_real_attacker = attacker
        
        # 1) 装备的 before_take_damage
        for eq in self.all_equipment:
            dmg = eq.before_take_damage(self, dmg)
    
        # 2) Buff 的 before_take_damage
        for buff in list(self.buffs):
            dmg = buff.before_take_damage(self, dmg)
            if hasattr(buff, "on_attacked"):
                buff.on_attacked(self, attacker, dmg)
    
        # 3) 全伤害抗性减免（隐藏，0.0–1.0）
        if self.damage_resistance:
            dmg = dmg * (1.0 - self.damage_resistance)
    
        # 4) 扣 shield
        if self.shield > 0:
            used = min(self.shield, dmg)
            self.shield -= used
            dmg -= used
    
        # 5) 扣 HP
        if dmg > 0:
            self.hp = max(0, self.hp - dmg)
            timestamp = pygame.time.get_ticks() if "pygame" in sys.modules else int(time.time() * 1000)
            self.last_hits.append((int(dmg), timestamp))
    
        # ✅ 6) 通知 Buff：我被攻击了（传入攻击者）
        for buff in list(self.buffs):
            if hasattr(buff, "on_attacked"):
                buff.on_attacked(self, attacker, dmg)
    
        # 7) 检查是否“致命”（hp 回到 0）
        if self.hp <= 0:
            to_remove = []
            for buff in list(self.buffs):
                if hasattr(buff, "on_fatal"):
                    remove = buff.on_fatal(self)
                    if remove:
                        to_remove.append(buff)
            # 移除所有标记的 Buff
            for buff in to_remove:
                self.remove_buff(buff)


    def try_attack(self, target, dt):
        """
        返回主攻的文本，额外攻击由 on_attack + perform_extra_attack 负责，
        也会单独产生命中飘字。
        """
        if any(getattr(b, "disable_attack", False) for b in self.buffs):
            return None
        
        # 1) CD/存活 检查
        self._cd += dt
        if self._cd < self.attack_interval or self.hp <= 0:
            return None
    
        # 2) 单次暴击判定
        is_crit = (random.random() < self.crit_chance)
        if is_crit:
            base_dmg = max(0, self.attack * self.crit_multiplier - target.defense)
        else:
            base_dmg = max(0, self.attack - target.defense)
    
        # 3) 装备/天赋 before_attack 钩子
        dmg = base_dmg
        for eq in self.all_equipment:
            dmg = eq.before_attack(self, target, dmg)
    
        # —— 只对主攻做一次快照 —— #
        pre_total  = target.shield + target.hp
        target.take_damage(dmg, attacker=self)
        post_total = target.shield + target.hp
        actual     = pre_total - post_total
        if actual > 0:
            # 只把主攻的实际掉血记录到飘字队列
            target.last_hits.append((int(actual), is_crit))
    
        # 4) 装备 after_attack 钩子
        for eq in self.all_equipment:
            eq.after_attack(self, target, dmg)
    
        # 5) 暴击/非暴击事件分发
        if is_crit:
            for eq in self.all_equipment:
                eq.on_critical(self, target, dmg)
        else:
            for eq in self.all_equipment:
                eq.on_non_critical(self, target, dmg)
    
        # 6) 天赋 on_attack (返回额外攻击文本列表)
        extra_texts = []
        for t in self.talents:
            out = t.on_attack(self, target, dmg)
            if out:
                extra_texts.extend(out)
    
        # 7) 刷新 CD
        self._cd -= self.attack_interval
    
        # 8) 构造主攻文本
        text = f"{self.name} → {target.name} 造成 {int(actual)} 点伤害"
        if is_crit:
            text += " (暴击!)"
    
        # 把 on_attack 里额外攻击的文本也返回给调用者
        return text, extra_texts

    
    def perform_extra_attack(self, target):
        """
        立刻对 target 发起一次额外普攻，不改变自身 _cd。
        返回本次攻击的文本描述，供展示用。
        """
        # 暴击判定
        is_crit = (random.random() < self.crit_chance)
        if is_crit:
            dmg = max(0, self.attack * self.crit_multiplier - target.defense)
        else:
            dmg = max(0, self.attack - target.defense)

        # 装备 before_attack 钩子
        for eq in self.all_equipment:
            dmg = eq.before_attack(self, target, dmg)

        # 应用伤害
        target.take_damage(dmg, attacker=self)

        # 装备 after_attack 钩子
        for eq in self.all_equipment:
            eq.after_attack(self, target, dmg)

        # 分发暴击 / 非暴击 事件
        if is_crit:
            for eq in self.all_equipment:
                eq.on_critical(self, target, dmg)
        else:
            for eq in self.all_equipment:
                eq.on_non_critical(self, target, dmg)

        # 记录用于飘字和面板
        text = f"{self.name} → {target.name} 造成 {int(dmg)} 点伤害"
        if is_crit:
            text += " (暴击!)"
        target.last_damage = int(dmg)
        target.last_hits.append((int(dmg), is_crit))

        return text
    
    def add_exp(self, amount):
        if self.hp <= 0: return [] # 死亡时不能获得经验
        
        self.exp += amount
        messages = [f"获得了 {amount} 点经验！ (当前: {self.exp}/{self.exp_to_next_level})"]
        
        if self.exp >= self.exp_to_next_level:
            level_up_messages = self.level_up()
            messages.extend(level_up_messages) # 将升级信息合并进来
        
        return messages

    def level_up(self):
        level_up_messages = []
        while self.exp >= self.exp_to_next_level:
            self.level += 1
            self.exp -= self.exp_to_next_level
            self.exp_to_next_level = int(self.exp_to_next_level * 1.5)

            self._innate_max_hp += 10
            self._innate_attack += 2
            self._innate_defense += 1
            
            self.base_max_hp = self._innate_max_hp + self._eq_hp_bonus
            self.base_attack = self._innate_attack + self._eq_atk_bonus
            self.base_defense = self._innate_defense + self._eq_def_bonus

            self.max_hp = self.base_max_hp
            self.attack = self.base_attack
            self.defense = self.base_defense
            self.hp = self.max_hp

            # 生成升级消息
            level_up_messages.append(f"🎉 等级提升！现在是 {self.level} 级！")
            level_up_messages.append("   生命+10，攻击+2，防御+1")
        
        return level_up_messages

    def pickup_item(self, item):
        """将物品拾取到背包中"""
        self.backpack.append(item)
        console.print(f"   [grey70]物品 [bold]{getattr(item, 'display_name', item.__class__.__name__)}[/bold] 已放入你的背包。[/grey70]")

        level_up_messages = []
        while self.exp >= self.exp_to_next_level:
            self.level += 1
            self.exp -= self.exp_to_next_level
            self.exp_to_next_level = int(self.exp_to_next_level * 1.5)
            self._innate_max_hp += 10
            self._innate_attack += 2
            self._innate_defense += 1
            self.base_max_hp = self._innate_max_hp + self._eq_hp_bonus
            self.base_attack = self._innate_attack + self._eq_atk_bonus
            self.base_defense = self._innate_defense + self._eq_def_bonus
            self.max_hp = self.base_max_hp
            self.attack = self.base_attack
            self.defense = self