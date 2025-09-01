import Buffs
import Talents
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
    display_name    = "木盾"

    def __init__(self):
        self.type = "armor"
        self.def_bonus    = 2
        self.shield_bonus = 10

    def on_battle_start(self, wearer):
        # 防御是永久属性，由Character.__init__处理
        wearer.shield  += self.shield_bonus

class WoodenSword(Equipment):
    """木剑：武器插槽；+3 攻击；每普攻 3 次，第 4 次普攻造成双倍伤害"""
    slot = "weapon"
    display_name    = "木剑"

    def __init__(self):
        self.type = "weapon"
        self.rarity = "common"
        self.atk_bonus = 3
        self._count    = 0
    
    # on_battle_start 已被移除，因为攻击是永久属性

    def before_attack(self, wearer, target, packet: DamagePacket):
        # 效果现在修改的是伤害包的数值
        if self._count >= 3:
            packet.amount *= 2
            self._count = 0

    def after_attack(self, wearer, target, actual_dmg):
        # 这里的dmg是造成伤害后的最终数值，可以直接使用
        if actual_dmg <= wearer.base_attack:
            self._count += 1

class WoodenArmor(Equipment):
    """木铠甲：护甲插槽；+2 防御；50% 概率额外减免 2 点物理伤害"""
    slot = "armor"
    display_name    = "木铠甲"

    def __init__(self):
        self.type = "armor"
        self.rarity = "common"
        self.def_bonus = 2

    # on_battle_start 已被移除，因为防御是永久属性

    def before_take_damage(self, wearer, packet: DamagePacket):
        # 效果现在只对物理伤害生效
        if packet.damage_type == DamageType.PHYSICAL and random.random() < 0.5:
            packet.amount = max(0, packet.amount - 2)

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


class VampiresFang(Equipment):
    """吸血鬼之牙：饰品槽；攻击造成10%生命偷取，生命低于50%时效果翻倍。"""
    slot = "accessory"
    display_name = "吸血鬼之牙"
    def __init__(self):
        self.rarity, self.type = "rare", "misc"
        self.lifesteal_ratio = 0.10

    # after_attack 现在接收的是最终伤害数值
    def after_attack(self, wearer, target, actual_dmg):
        ratio = self.lifesteal_ratio
        if wearer.hp / wearer.max_hp < 0.5:
            ratio *= 2
        
        healed_amount = actual_dmg * ratio
        if healed_amount > 0:
            wearer.heal(healed_amount)

class HourglassOfTime(Equipment):
    """时光沙漏：副手槽；暴击时有40%几率立即重置攻击冷却。"""
    slot = "offhand"
    display_name = "时光沙漏"
    def __init__(self):
        self.rarity, self.type = "uncommon", "armor" # 副手算防具
        self.proc_chance = 0.4

    def on_critical(self, wearer, target, dmg):
        if random.random() < self.proc_chance:
            print("[时光沙漏] 效果触发！")
            # 直接将攻击冷却充满
            wearer._cd = wearer.attack_interval

class Stormcaller(Equipment):
    """风暴召唤者：武器槽；+15攻击；每攻击4次，为敌人附加一层【风暴】印记。"""
    slot = "weapon"
    display_name = "风暴召唤者"
    def __init__(self):
        self.rarity, self.type = "legendary", "weapon"
        self.atk_bonus = 15
        self._attack_count = 0

    def after_attack(self, wearer, target, dmg):
        self._attack_count += 1
        if self._attack_count >= 4:
            self._attack_count = 0
            print("[风暴召唤者] 附加了风暴印记！")
            target.add_debuff(Buffs.StormDebuff(), source=wearer)

# 在 Equips.py 文件末尾添加

# --- 白色 (Common) 品质新装备 ---

class LeatherGloves(Equipment):
    """皮手套：副手槽；+0.3 攻击速度。"""
    slot = "offhand"
    display_name = "皮手套"
    def __init__(self):
        self.rarity, self.type = "common", "armor"
        self.atk_speed_bonus = 0.3

class RustyHelmet(Equipment):
    """生锈的头盔：头盔槽；+30 最大生命值。"""
    slot = "helmet"
    display_name = "生锈的头盔"
    def __init__(self):
        self.rarity, self.type = "common", "armor"
        self.hp_bonus = 30

# --- 绿色 (Uncommon) 品质新装备 ---

class BarbedAxe(Equipment):
    """倒钩斧：武器槽；+5攻击；攻击时有30%几率使敌人【流血】5秒。"""
    slot = "weapon"
    display_name = "倒钩斧"
    def __init__(self):
        self.rarity, self.type = "uncommon", "weapon"
        self.atk_bonus = 5
        self.bleed_chance = 0.3
    def after_attack(self, wearer, target, dmg):
        if random.random() < self.bleed_chance:
            target.add_debuff(Buffs.BleedDebuff(stacks=1), source=wearer)

# 在 Equips.py 文件中，找到并替换 TowerShield 类

class TowerShield(Equipment):
    """塔盾：副手槽；+3防御；战斗开始时，获得3层【格挡】。"""
    slot = "offhand"
    display_name = "塔盾"
    def __init__(self):
        self.rarity, self.type = "uncommon", "armor"
        self.def_bonus = 3
        self.block_stacks = 3

    def on_battle_start(self, wearer):
        wearer.add_buff(Buffs.BlockBuff(stacks=self.block_stacks))
    

# --- 蓝色 (Rare) 品质新装备 ---

class AdventurersPouch(Equipment):
    """冒险家的钱袋：饰品槽；每拥有20金币，就为你提供+1攻击力。（战斗开始时结算）"""
    slot = "accessory"
    display_name = "冒险家的钱袋"
    def __init__(self):
        self.rarity, self.type = "rare", "misc"
    def on_battle_start(self, wearer):
        # 假设玩家的金币存储在 game.player 对象上
        gold = getattr(wearer, 'gold', 0)
        bonus_atk = gold // 20
        if bonus_atk > 0:
            print(f"[冒险家的钱袋] 你获得了 {bonus_atk} 点额外攻击力！")
            wearer.attack += bonus_atk