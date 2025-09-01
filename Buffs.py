from damage import DamagePacket, DamageType
from abc import ABC
import collections
from collections import defaultdict
from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import time
import random
from rich.text import Text
from rich.progress import BarColumn  # 可选：也可以直接用 Text
import math
from collections import Counter
#import pygame
import sys

class Buff(ABC):
    """通用 Buff/DeBuff 基类，所有状态继承此类。"""
    display_name     = None      # 界面显示名
    max_stacks       = 1         # 最大叠层数；1 表示不可叠加
    dispellable      = False     # 是否可被驱散
    duration         = None      # 持续秒数；None 或 0 表示无限
    hidden           = False     # 是否在界面隐藏
    is_debuff        = False     # 是否为负面状态
    priority         = 0         # 执行顺序，越大越先执行
    disable_attack   = False     # 是否禁止攻击（如眩晕、不灭二阶段）

    def __init__(self, stacks: int = 1, duration_override: float = None):
        self.stacks = min(stacks, self.max_stacks)
        self.remaining = duration_override if duration_override is not None else self.duration
        self._accum = 0.0

    def on_apply(self, wearer):
        """Buff 被添加到角色时触发"""
        pass

    def on_remove(self, wearer):
        """Buff 被移除时触发"""
        pass

    def on_tick(self, wearer, dt):
        """
        每帧或定时触发，用于持续性效果。
        返回字符串则表示有飘字。
        """
        return None

    def before_take_damage(self, wearer, dmg):
        """受到伤害前触发，可修改 dmg"""
        return dmg

    def on_attacked(self, wearer, attacker, dmg):
        """每次被攻击后触发"""
        pass

    def on_fatal(self, wearer):
        """
        临界（hp<=0）时触发一次，自救或其他
        返回 True 则移除自身 Buff
        """
        return False


class SteelHeartBuff(Buff):
    """刚毅：受到致命伤时自救一次，可叠加"""
    display_name = "刚毅"
    dispellable  = False
    max_stacks   = 99  # ✅ 允许叠加

    def __init__(self, uses: int = 1):
        super().__init__(stacks=uses)

    def on_fatal(self, wearer):
        if self.stacks > 0:
            self.stacks -= 1
            wearer.hp = 1
            wearer.shield += int(wearer.max_hp * 0.3)
            return self.stacks == 0  # 最后1次后移除
        return False


class RegenerationBuff(Buff):
    """
    再生：每层每秒回复 1 点 HP，持续存在（无限）。
    """
    display_name = "再生"
    dispellable  = True
    max_stacks   = 99
    is_debuff    = False

    def __init__(self, stacks: int = 1):
        super().__init__(stacks=stacks)
        self._timer = 0.0  # 新增：秒计时器

    def on_tick(self, wearer, dt):
        self._timer += dt  # 累加每帧的时间
        
        # 当计时器超过或等于1秒时，执行回血
        while self._timer >= 1.0:
            amount = self.stacks  # 每秒回复量 = 层数
            wearer.heal(amount)
            self._timer -= 1.0  # 计时器减去1秒，准备下一次计时
        return None


class PoisonDebuff(Buff):
    """
    毒：每层每秒对角色造成 1 点毒系伤害；优先消耗护盾
    """
    display_name = "毒"
    dispellable  = True
    max_stacks   = 99
    is_debuff    = True

    def __init__(self, stacks: int = 1):
        super().__init__(stacks=stacks)
        self._timer = 0.0

    def on_tick(self, wearer, dt):
        self._timer += dt
        while self._timer >= 1.0:
            dmg = self.stacks
            # <-- 核心修改：创建并发送一个伤害信息包 -->
            packet = DamagePacket(
                amount=dmg, 
                damage_type=DamageType.POISON, # 类型是毒
                is_dot=True,                   # 标记为持续伤害
                is_sourceless=True             # 标记为无来源伤害
            )
            wearer.take_damage(packet)
            self._timer -= 1.0
        return None


class AttackDisabledBuff(Buff):
    """通用：禁止角色普攻"""
    display_name    = "无法攻击"
    dispellable     = False
    is_debuff       = True
    hidden          = True
    disable_attack  = True

    def __init__(self, duration: float):
        super().__init__(stacks=1)
        self.remaining = duration

    def on_tick(self, wearer, dt):
        if self.remaining is None:
            return None
        self.remaining -= dt
        if self.remaining <= 0:
            wearer.remove_buff(self)
        return None

class StunDebuff(Buff):
    """
    眩晕：禁止普攻，不可叠加，不可驱散
    """
    display_name    = "眩晕"
    max_stacks      = 1
    dispellable     = False
    is_debuff       = True
    disable_attack  = True
    duration        = 2.0

    def __init__(self, duration=2.0):
        super().__init__(duration_override=duration)

    def on_apply(self, wearer):
        for b in wearer.buffs:
            if b is not self and isinstance(b, StunDebuff):
                b.remaining = max(b.remaining, self.remaining)
                wearer.remove_buff(self)
                return

    def on_tick(self, wearer, dt):
        self.remaining -= dt
        if self.remaining <= 0:
            wearer.remove_buff(self)
        return None


# 替换 Buffs.py 中的 ThornsBuff 类
class ThornsBuff(Buff):
    """荆棘：被攻击时反弹当前层数的真实伤害给攻击者"""
    display_name  = "荆棘"
    dispellable   = True
    is_debuff     = False
    max_stacks    = 99

    def on_attacked(self, wearer, attacker, dmg):
        if attacker is not None and self.stacks > 0 and attacker.hp > 0:
            # 创建一个真实伤害、无来源的伤害包进行反伤
            thorns_packet = DamagePacket(
                amount=self.stacks,
                damage_type=DamageType.TRUE,
                source=wearer,
                is_sourceless=True
            )
            attacker.take_damage(thorns_packet)

class PhoenixCrownStage1Buff(Buff):
    """不灭·觉醒（Stage1）：防御→攻击+攻速"""
    display_name  = "不灭·觉醒"
    dispellable   = False
    is_debuff     = False

    def __init__(self):
        super().__init__(stacks=1)
        self._boosted = False

    def on_apply(self, wearer):
        bm = wearer.base_max_hp
        wearer.max_hp = bm * 2
        wearer.hp     = min(wearer.hp + bm, wearer.max_hp)

    def on_tick(self, wearer, dt):
        if not self._boosted:
            bd = wearer.base_defense
            ba = wearer.base_attack
            bs = wearer.base_attack_speed
            wearer.attack = ba + bd
            wearer.attack_speed = bs + bd * 0.05
            wearer.attack_interval = 6.0 / wearer.attack_speed
            wearer.defense = 0
            self._boosted = True
        if wearer.hp / wearer.max_hp <= 0.2:
            wearer.remove_buff(self)
            wearer.add_buff(PhoenixCrownStage2Buff())
        return None


class PhoenixCrownStage2Buff(Buff):
    """不灭·第二阶段：禁手+回血反击"""
    display_name    = "不灭"
    dispellable     = False
    is_debuff       = False
    disable_attack  = True

    def __init__(self):
        super().__init__(stacks=1)
        self._healed_total  = 0.0
        self._rec_atk       = None
        self._rec_def       = None
        self._rec_as        = None
        self._rec_dr        = None
        self._timer         = 0.0  # 新增：秒计时器

    def on_apply(self, wearer):
        self._rec_atk  = wearer.attack
        self._rec_def  = wearer.defense
        self._rec_as   = wearer.attack_speed
        self._rec_dr   = wearer.damage_resistance
        wearer.damage_resistance = self._rec_dr + 0.5

    def on_tick(self, wearer, dt):
        self._timer += dt
        
        # 每秒触发一次回血
        while self._timer >= 1.0:
            if wearer.hp < wearer.max_hp: # 只有没满血的时候才回
                heal_amount = wearer.max_hp * 0.1 # 每秒回复最大生命的10%
                actual_healed = min(heal_amount, wearer.max_hp - wearer.hp) # 实际回复量
                wearer.hp += actual_healed
                self._healed_total += actual_healed
            self._timer -= 1.0

        if wearer.hp >= wearer.max_hp:
            total = int(self._healed_total)
            attacker = getattr(wearer, "_last_real_attacker", None)
            text = "" # 初始化返回文本

            if attacker and attacker.hp > 0:
                attacker.take_damage(total)
                attacker.last_hits.append((total, False))
                text = f"[不灭反击] {wearer.name} → {attacker.name} 造成 {total} 点伤害"

            # 恢复原属性
            wearer.attack            = self._rec_atk
            wearer.defense           = self._rec_def
            wearer.attack_speed      = self._rec_as
            wearer.attack_interval   = 6.0 / self._rec_as
            wearer.damage_resistance = self._rec_dr
            wearer.max_hp            = wearer.base_max_hp
            wearer.hp                = min(wearer.hp, wearer.max_hp)
            wearer.remove_buff(self)
            return text

        return None
    
class StormDebuff(Buff):
    """
    风暴印记 (可驱散)
    当携带者受到下一次任意来源的伤害时，
    此印记会引爆，造成额外伤害，然后消失。
    """
    display_name = "风暴"
    dispellable  = True
    is_debuff    = True

    def before_take_damage(self, wearer, packet: DamagePacket): # <-- 接收 packet
        print("[风暴引爆!] 造成额外伤害")
        # 直接在传入的伤害包上增加伤害
        packet.amount += 50
        # 移除自己
        wearer.remove_buff(self)


class BleedDebuff(Buff):
    """
    流血 (可叠加, 可驱散)
    每层每秒对目标造成 1 点真实伤害（无视防御）。
    """
    display_name = "流血"
    dispellable  = True
    is_debuff    = True
    max_stacks   = 99

    def __init__(self, stacks: int = 1, duration: float = 5.0):
        super().__init__(stacks=stacks, duration_override=duration)
        self._timer = 0.0

    def on_tick(self, wearer, dt):
        self._timer += dt
        if self._timer >= 1.0:
            dmg = self.stacks
            # <-- 核心修改：创建并发送一个伤害信息包 -->
            packet = DamagePacket(
                amount=dmg,
                damage_type=DamageType.TRUE, # 类型是真实伤害
                is_dot=True,
                is_sourceless=True
            )
            wearer.take_damage(packet)
            self._timer -= 1.0
        
        self.remaining -= dt
        if self.remaining <= 0:
            wearer.remove_buff(self)
        return None

class BlockBuff(Buff):
    """格挡：每层可以完全抵挡一次任意来源的伤害。"""
    display_name = "格挡"
    max_stacks   = 99

    def before_take_damage(self, wearer, packet: DamagePacket): # <-- 参数改为 packet
        if self.stacks > 0 and packet.amount > 0:
            print(f"[格挡] 效果触发！抵挡了 {int(packet.amount)} 点伤害。")
            self.stacks -= 1
            if self.stacks <= 0:
                wearer.remove_buff(self)
            
            packet.amount = 0 # 将伤害包的数值清零