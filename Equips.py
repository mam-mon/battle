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
from rich.progress import BarColumn
import math
from collections import Counter
import sys

class Equipment:
    slot = None
    def on_battle_start(self, wearer): pass
    def before_attack(self, wearer, target, dmg): return dmg
    def after_attack(self, wearer, target, dmg): pass
    def before_take_damage(self, wearer, dmg): return dmg
    def on_critical(self, wearer, target, dmg): pass
    def on_non_critical(self, wearer, target, dmg): pass

class WoodenShield(Equipment):
    """木盾：副手插槽；+2 防御；战斗开始时获得 10 护盾"""
    slot = "offhand"
    display_name = "木盾"
    def __init__(self):
        self.rarity = "common"
        self.type = "armor" # 添加类型
        self.def_bonus = 2
        self.shield_bonus = 10
    def on_battle_start(self, wearer):
        # 防御是永久属性，由Character.__init__处理
        # 只保留战斗开始时的效果
        wearer.shield += self.shield_bonus

class WoodenSword(Equipment):
    """木剑：武器插槽；+3 攻击；每普攻 3 次，第 4 次普攻造成双倍伤害"""
    slot = "weapon"
    display_name = "木剑"
    def __init__(self):
        self.rarity = "common"
        self.type = "weapon"
        self.atk_bonus = 3
        self._count = 0
    def on_battle_start(self, wearer):
        # 攻击是永久属性，已在Character.__init__中计算
        pass # 因此这里什么都不用做
    def before_attack(self, wearer, target, dmg):
        # 注意：这里的伤害加成逻辑也需要调整，否则会重复计算
        # 我们让伤害直接基于角色的攻击力，而不是装备临时加
        if self._count >= 3:
            dmg *= 2
            self._count = 0
        return dmg
    def after_attack(self, wearer, target, dmg):
        # 判定条件也应该基于角色的基础攻击
        if dmg <= wearer.base_attack:
            self._count += 1

class WoodenArmor(Equipment):
    """木铠甲：护甲插槽；+2 防御；50% 概率额外减免 2 点伤害"""
    slot = "armor"
    display_name = "木铠甲"
    def __init__(self):
        self.rarity = "common"
        self.type = "armor" # 添加类型
        self.def_bonus = 2
    def on_battle_start(self, wearer):
        # 防御是永久属性
        pass
    def before_take_damage(self, wearer, dmg):
        if random.random() < 0.5:
            dmg = max(0, dmg - 2)
        return dmg

class IronSword(Equipment):
    """铁剑：武器插槽；+5 攻击；基础 +5% 暴击率；未暴击时，下次普攻暴击率 +5%，最多 8 层；暴击后清除"""
    slot = "weapon"
    display_name = "铁剑"
    def __init__(self):
        self.rarity = "common"
        self.type = "weapon"
        self.atk_bonus = 5
        self.base_crit_bonus = 0.05
        self.max_stacks = 8
        self._stacks = 0
    def on_battle_start(self, wearer):
        # 攻击和暴击都是永久属性
        # 但暴击率需要在战斗中动态变化，所以我们需要在战前设置初始值
        wearer.crit_chance += self.base_crit_bonus
    def on_critical(self, wearer, target, dmg):
        wearer.crit_chance -= self._stacks * self.base_crit_bonus
        self._stacks = 0
    def on_non_critical(self, wearer, target, dmg):
        if self._stacks < self.max_stacks:
            self._stacks += 1
            wearer.crit_chance += self.base_crit_bonus

class IronRing(Equipment):
    """铁戒指：饰品槽；+5% 暴击；+10% 爆伤；赠送两层“刚毅”Buff"""
    slot = "accessory"
    display_name = "铁戒指"
    def __init__(self):
        self.rarity = "common"
        self.type = "misc" # 添加类型
        self.crit_bonus = 0.05
        self.crit_dmg_bonus = 0.10
    def on_battle_start(self, wearer):
        # 暴击和爆伤是永久属性
        # 只保留战斗开始时的效果
        wearer.add_status(Buffs.SteelHeartBuff(uses=2))

class IronHammer(Equipment):
    """铁锤：武器槽；+8 攻击；+5% 暴击；20% 概率眩晕敌人 2 秒"""
    slot = "weapon"
    display_name = "铁锤"
    def __init__(self):
        self.rarity = "uncommon"
        self.type = "weapon"
        self.atk_bonus = 8
        self.crit_chance_bonus = 0.05
        self.stun_chance = 0.20
        self.stun_duration = 2.0
    def on_battle_start(self, wearer):
        # 攻击和暴击是永久属性
        pass
    def after_attack(self, wearer, target, dmg):
        if random.random() < self.stun_chance:
            target.add_status(Buffs.StunDebuff(self.stun_duration), source=wearer)

class NaturalNecklace(Equipment):
    """自然项链：饰品槽；最大 HP +20；提供 2 层“再生”Buff"""
    slot = "accessory"
    display_name = "自然项链"
    def __init__(self):
        self.rarity = "uncommon"
        self.type = "misc" # 添加类型
        self.hp_bonus = 20
    def on_battle_start(self, wearer):
        # HP是永久属性
        # 只保留战斗开始时的效果
        wearer.add_status(Buffs.RegenerationBuff(stacks=2))

class ThornsRing(Equipment):
    """荆棘环：饰品槽；+0.2 攻速；+10% 爆伤；战斗开始时提供 3 层 荆棘"""
    slot = "accessory"
    display_name = "荆棘环"
    def __init__(self):
        self.rarity = "uncommon"
        self.type = "misc" # 添加类型
        self.atk_speed_bonus = 0.2
        self.crit_damage_bonus = 0.10
        self.thorns_stacks = 3
    def on_battle_start(self, wearer):
        # 攻速和爆伤是永久属性
        # 只保留战斗开始时的效果
        wearer.add_status(Buffs.ThornsBuff(stacks=self.thorns_stacks))

class PhoenixCrown(Equipment):
    """紫金冠：头盔槽；无基础属性；附加“不灭”效果"""
    slot = "helmet"
    display_name = "紫金冠"
    def __init__(self):
        self.rarity = "legendary"
        self.type = "armor" # 添加类型
    def on_battle_start(self, wearer):
        # 这个设计是完美的，只添加Buff
        wearer.add_buff(Buffs.PhoenixCrownStage1Buff())

class SlimeSword(Equipment):
    """史莱姆之剑：武器；+6 攻击；攻击时有15%概率使敌人中毒1层"""
    slot = "weapon"
    display_name = "史莱姆之剑"
    def __init__(self):
        self.rarity = "common"
        self.type = "weapon"
        self.atk_bonus = 6
        self.poison_chance = 0.15
    def on_battle_start(self, wearer):
        # 攻击是永久属性
        pass
    def after_attack(self, wearer, target, dmg):
        if random.random() < self.poison_chance:
            target.add_debuff(Buffs.PoisonDebuff(stacks=1), source=wearer)