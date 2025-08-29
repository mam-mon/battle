import Buffs
import Talents
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

class Equipment:
    slot = None  # 子类必须 override

    def on_battle_start(self, wearer):
        pass

    def before_attack(self, wearer, target, dmg):
        return dmg

    def after_attack(self, wearer, target, dmg):
        pass

    def before_take_damage(self, wearer, dmg):
        return dmg

    def on_critical(self, wearer, target, dmg):
        pass

    def on_non_critical(self, wearer, target, dmg):
        pass


class WoodenShield(Equipment):
    """木盾：副手插槽；+2 防御；战斗开始时获得 10 护盾"""
    slot = "offhand"
    display_name    = "木盾"

    def __init__(self):
        self.def_bonus    = 2
        self.shield_bonus = 10

    def on_battle_start(self, wearer):
        wearer.defense += self.def_bonus
        wearer.shield  += self.shield_bonus


class WoodenSword(Equipment):
    """木剑：武器插槽；+3 攻击；每普攻 3 次，第 4 次普攻造成双倍伤害"""
    slot = "weapon"
    display_name    = "木剑"

    def __init__(self):
        self.atk_bonus = 3
        self._count    = 0

    def on_battle_start(self, wearer):
        wearer.attack += self.atk_bonus

    def before_attack(self, wearer, target, dmg):
        dmg += self.atk_bonus
        if self._count >= 3:
            dmg *= 2
            self._count = 0
        return dmg

    def after_attack(self, wearer, target, dmg):
        base = wearer.attack
        if dmg <= base:
            self._count += 1


class WoodenArmor(Equipment):
    """木铠甲：护甲插槽；+2 防御；50% 概率额外减免 2 点伤害"""
    slot = "armor"
    display_name    = "木铠甲"

    def __init__(self):
        self.def_bonus = 2

    def on_battle_start(self, wearer):
        wearer.defense += self.def_bonus

    def before_take_damage(self, wearer, dmg):
        if random.random() < 0.5:
            dmg = max(0, dmg - 2)
        return dmg


class IronSword(Equipment):
    """铁剑：武器插槽；+5 攻击；基础 +5% 暴击率；  
       未暴击时，下一次普攻暴击率 +5%，最多 8 层；暴击后清除自身叠加"""
    slot = "weapon"
    display_name    = "铁剑"

    def __init__(self):
        self.atk_bonus        = 5
        self.base_crit_bonus  = 0.05
        self.max_stacks       = 8
        self._stacks          = 0

    def on_battle_start(self, wearer):
        wearer.attack      += self.atk_bonus
        wearer.crit_chance += self.base_crit_bonus

    def before_attack(self, wearer, target, dmg):
        return dmg

    def after_attack(self, wearer, target, dmg):
        pass

    def on_critical(self, wearer, target, dmg):
        # 暴击后清除自身叠加部分
        wearer.crit_chance -= self._stacks * self.base_crit_bonus
        self._stacks = 0

    def on_non_critical(self, wearer, target, dmg):
        if self._stacks < self.max_stacks:
            self._stacks += 1
            wearer.crit_chance += self.base_crit_bonus


class IronRing(Equipment):
    """铁戒指：饰品槽；+5% 暴击；+10% 爆伤；赠送两层“刚毅”Buff"""
    slot = "accessory"
    display_name    = "贴戒指"

    def __init__(self):
        self.crit_bonus     = 0.05
        self.crit_dmg_bonus = 0.10

    def on_battle_start(self, wearer):
        # 1) 增加暴击率和爆伤
        wearer.crit_chance     += self.crit_bonus
        wearer.crit_multiplier += self.crit_dmg_bonus
        # 2) 注入两层刚毅 Buff
        wearer.add_status(Buffs.SteelHeartBuff(uses=2))


class IronHammer(Equipment):
    """铁锤：武器槽；+8 攻击；+5% 暴击；20% 概率眩晕敌人 2 秒"""
    slot = "weapon"
    display_name    = "铁锤"

    def __init__(self):
        self.atk_bonus          = 8
        self.crit_chance_bonus  = 0.05
        self.stun_chance        = 0.20
        self.stun_duration      = 2.0

    def on_battle_start(self, wearer):
        # 基础属性加成
        wearer.attack      += self.atk_bonus
        wearer.crit_chance += self.crit_chance_bonus

    def after_attack(self, wearer, target, dmg):
        # 20% 概率眩晕
        if random.random() < self.stun_chance:
            # 刷新或添加 StunDebuff
            target.add_status(Buffs.StunDebuff(self.stun_duration), source=wearer)


class NaturalNecklace(Equipment):
    """自然项链：饰品槽；最大 HP +20；提供 2 层“再生”Buff"""
    slot = "accessory"
    display_name    = "自然项链"

    def __init__(self):
        self.hp_bonus = 20

    def on_battle_start(self, wearer):
        wearer.max_hp += self.hp_bonus
        wearer.hp     += self.hp_bonus
        wearer.add_status(Buffs.RegenerationBuff(stacks=2))  # ✅ 每次新建



class ThornsRing(Equipment):
    """荆棘环：饰品槽；+0.2 攻速；+10% 爆伤；战斗开始时提供 3 层 荆棘"""
    slot = "accessory"
    display_name    = "荆棘环"

    def __init__(self):
        self.atk_speed_bonus   = 0.2   # +0.2 次/s
        self.crit_damage_bonus = 0.10  # +10% 爆伤
        self.thorns_stacks     = 3

    def on_battle_start(self, wearer):
        # 1) 攻速加成
        base_as = 3.0 / wearer.attack_interval
        wearer.attack_interval = 6.0 / (base_as + self.atk_speed_bonus)
        # 2) 爆伤加成
        wearer.crit_multiplier += self.crit_damage_bonus
        # 3) 添加荆棘 Buff
        wearer.add_status(Buffs.ThornsBuff(stacks=self.thorns_stacks))

class PhoenixCrown(Equipment):
    """紫金冠：头盔槽；无基础属性；附加“不灭”效果"""
    slot = "helmet"
    display_name    = "紫金冠"

    def on_battle_start(self, wearer):
        # 战斗开始时给自己挂“不灭” Buff
        wearer.add_buff(Buffs.PhoenixCrownStage1Buff())

# In Equips.py

class SlimeSword(Equipment):
    """史莱姆之剑：武器；+2 攻击；攻击时有15%概率使敌人中毒1层"""
    slot = "weapon"
    display_name = "史莱姆之剑"

    def __init__(self):
        self.atk_bonus = 4
        self.poison_chance = 0.15

    def on_battle_start(self, wearer):
        wearer.attack += self.atk_bonus

    def after_attack(self, wearer, target, dmg):
        if random.random() < self.poison_chance:
            target.add_debuff(Buffs.PoisonDebuff(stacks=1), source=wearer)




# 你可以同样为头盔、护腿、饰品定义 slot="helmet"/"pants"/"accessory" 的类

