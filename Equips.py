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

class WoodenSword_Star(Equipment):
    """木剑⭐：武器插槽；+6 攻击；现在每攻击 2 次，第 3 次普攻造成双倍伤害。"""
    slot = "weapon"
    display_name = "木剑⭐"
    
    def __init__(self):
        self.type = "weapon"
        self.rarity = "uncommon" # 升级后，品质也提升了
        self.atk_bonus = 6       # 基础攻击更高
        self._count = 0

    def before_attack(self, wearer, target, packet: DamagePacket):
        # 效果增强：从3次触发改为2次触发
        if self._count >= 2:
            packet.amount *= 2
            self._count = 0

    def after_attack(self, wearer, target, actual_dmg):
        # 这里的dmg是造成伤害后的最终数值，可以直接使用
        self._count += 1

class WoodenArmor(Equipment):
    """木铠甲：护甲插槽；+2 防御；30% 概率额外减免 30% 点物理伤害"""
    slot = "armor"
    display_name    = "木铠甲"

    def __init__(self):
        self.type = "armor"
        self.rarity = "common"
        self.def_bonus = 2

    # on_battle_start 已被移除，因为防御是永久属性

    def before_take_damage(self, wearer, packet: DamagePacket):
        # 效果现在只对物理伤害生效
        if packet.damage_type == DamageType.PHYSICAL and random.random() < 0.3:
            packet.amount = max(0, packet.amount * 0.7)

class WoodenArmor_Star(Equipment):
    """木铠甲⭐：护甲插槽；+5 防御；50% 概率额外减免 50% 点物理伤害"""
    slot = "armor"
    display_name = "木铠甲⭐"

    def __init__(self):
        self.type = "armor"
        self.rarity = "uncommon"
        self.def_bonus = 5 # 基础防御更高

    def before_take_damage(self, wearer, packet: DamagePacket):
        # 效果现在只对物理伤害生效
        if packet.damage_type == DamageType.PHYSICAL and random.random() < 0.5:
            packet.amount = max(0, packet.amount * 0.5)

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
        self.atk_bonus = 0 # 初始攻击力加成为0

    def on_battle_start(self, wearer):
        # 在战斗开始时，只计算应该加多少攻击力，并存到自己的属性里
        gold = getattr(wearer, 'gold', 0)
        self.atk_bonus = gold // 20
        if self.atk_bonus > 0:
            print(f"[冒险家的钱袋] 你获得了 {self.atk_bonus} 点额外攻击力！")
            # 重新计算一次总属性，让这个新的atk_bonus生效
            wearer.recalculate_stats()

class ShadowCloak(Equipment):
    """暗影斗篷：护甲槽；+5防御；受到暴击伤害时，有30%概率免疫该次伤害。"""
    slot = "armor"
    display_name = "暗影斗篷"
    def __init__(self):
        self.rarity, self.type = "rare", "armor"
        self.def_bonus = 5
        self.crit_immunity_chance = 0.3
    def before_take_damage(self, wearer, packet: DamagePacket):
        if packet.damage_type == DamageType.PHYSICAL and packet.is_critical:
            if random.random() < self.crit_immunity_chance:
                print("[暗影斗篷] 免疫了暴击伤害！")
                packet.amount = 0

# 在 Equips.py 文件末尾添加

# --- “烙印”体系示例 ---

class SunScorchedBlade(Equipment):
    """日灼之刃 [武器-稀有]：攻击速度+0.5；命中时附加一层【日之烙印】。"""
    slot, display_name = "weapon", "日灼之刃"
    def __init__(self):
        self.rarity, self.type = "rare", "weapon"
        self.atk_speed_bonus = 0.5
    def after_attack(self, wearer, target, actual_dmg):
        target.add_debuff(Buffs.SunstoneBrandDebuff(stacks=1), source=wearer)

class Avalanche(Equipment):
    """山崩 [武器-史诗]：攻击力+20；暴击时引爆目标所有【日之烙印】，每层造成20额外真实伤害。"""
    slot, display_name = "weapon", "山崩"
    def __init__(self):
        self.rarity, self.type = "epic", "weapon"
        self.atk_bonus = 20
    def on_critical(self, wearer, target, actual_dmg):
        # 寻找目标身上的烙印
        brand_debuff = next((b for b in target.buffs if isinstance(b, Buffs.SunstoneBrandDebuff)), None)
        if brand_debuff:
            stacks = brand_debuff.stacks
            print(f"[山崩] 引爆了 {stacks} 层烙印！")
            # 造成额外伤害
            extra_dmg = stacks * 20
            packet = DamagePacket(amount=extra_dmg, damage_type=DamageType.TRUE, source=wearer)
            target.take_damage(packet)
            # 移除烙印
            target.remove_buff(brand_debuff)

# --- “龙魂”体系示例 ---

class DragonBloodChalice(Equipment):
    """龙血酒杯 [饰品-史诗]：每秒失去5点生命，但获得1层【龙魂】。"""
    slot, display_name = "accessory", "龙血酒杯"
    def __init__(self):
        self.rarity, self.type = "epic", "misc"
        self._timer = 0.0
    def on_battle_start(self, wearer):
        self._timer = 0.0 # 重置计时器
    def on_tick(self, wearer, dt): # 需要在 Character.update 中调用 on_tick
        self._timer += dt
        if self._timer >= 1.0:
            self._timer -= 1.0
            # 扣血
            packet = DamagePacket(amount=5, damage_type=DamageType.TRUE, is_sourceless=True)
            wearer.take_damage(packet)
            # 获得龙魂
            wearer.add_buff(Buffs.DragonSoulBuff(stacks=1))

class DragonscaleWard(Equipment):
    """龙鳞盾 [副手-稀有]：战斗开始时，消耗所有【龙魂】，每层提供15点护盾。"""
    slot, display_name = "offhand", "龙鳞盾"
    def __init__(self):
        self.rarity, self.type = "rare", "armor"
    def on_battle_start(self, wearer):
        soul_buff = next((b for b in wearer.buffs if isinstance(b, Buffs.DragonSoulBuff)), None)
        if soul_buff:
            stacks = soul_buff.stacks
            shield_gain = stacks * 15
            print(f"[龙鳞盾] 消耗了 {stacks} 层龙魂，获得了 {shield_gain} 点护盾！")
            wearer.shield += shield_gain
            wearer.remove_buff(soul_buff)

UPGRADE_MAP = {
    WoodenSword: WoodenSword_Star,
    WoodenArmor: WoodenArmor_Star,
    # 在这里继续为你其他的装备添加升级配方...
    # 例如:
    # IronSword: IronSword_Star, 
}