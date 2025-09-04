import Buffs
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
from rich.console import Console

from damage import DamagePacket, DamageType
from battle_logger import battle_logger
from settings import TEXT_COLOR, DAMAGE_TYPE_COLORS
from ui import format_damage_log

class Talent:
    """天赋基类，之后可扩展更多钩子"""
    display_name = None
    def on_init(self, wearer):
        """角色创建/战前初始化时触发，用于修改槽位之类的属性"""
        pass
    def on_attack(self, wearer, target, dmg):
        """攻击后触发"""
        pass
    def on_debuff_applied(self, wearer, buff):
        """当一个 Debuff 被加到 wearer 上时触发"""
        pass
        
class PoisonousTalent(Talent):
    display_name = "毒物"
    def __init__(self, chance: float = 0.5):
        self.chance = chance

    def on_attack(self, wearer, target, dmg):
        if random.random() < self.chance:
            target.add_debuff(Buffs.PoisonDebuff(stacks=1), source=wearer)

class DualWieldTalent(Talent):
    """二刀流：武器槽提升到 2"""
    display_name = "二刀流"
    def on_init(self, wearer):
        cur = wearer.SLOT_CAPACITY.get("weapon", 1)
        if cur < 2:
            wearer.SLOT_CAPACITY["weapon"] = 2

class TripleWieldTalent(Talent):
    """三刀流：武器槽提升到 3"""
    display_name = "三刀流"
    def on_init(self, wearer):
        cur = wearer.SLOT_CAPACITY.get("weapon", 1)
        if cur < 3:
            wearer.SLOT_CAPACITY["weapon"] = 3

class ThousandWorldTalent(Talent):
    """三千世界：普攻时有 chance 概率立即额外连续普攻 2 次"""
    display_name = "三千世界"

    def __init__(self, chance: float = 0.33):
        self.chance = chance

    # 文件: Talents.py (在 ThousandWorldTalent 类中，替换 on_attack 方法)

    def on_attack(self, wearer, target, dmg):
        """
        额外攻击现在会自己处理日志，所以这里不再需要返回任何东西。
        """
        if random.random() < self.chance:
            # 额外出手两次
            for _ in range(2):
                wearer.perform_extra_attack(target)
        # 不再需要返回 extra_texts

class HeartOfHealingTalent(Talent):
    """治愈之心：被施加可驱散的 Debuff 时，30% 概率驱散此层，并获得 1 层 再生"""
    display_name = "治愈之心"

    def __init__(self, chance: float = 0.3):
        self.chance = chance

    def on_debuff_applied(self, wearer, buff):
        if random.random() < self.chance:
            # 驱散一层
            if hasattr(buff, "stacks"):
                buff.stacks -= 1
                if buff.stacks <= 0:
                    wearer.remove_buff(buff)
            else:
                wearer.remove_buff(buff)
            # 获得 1 层“再生”
            wearer.add_buff(Buffs.RegenerationBuff(stacks=1))

class BambooLeafTalent(Talent):
    display_name = "竹叶青"

    def __init__(self, chance: float = 1.0):
        self.chance = chance
        self._bamboo_atk_bonus = 0  # 上一次总加成
        self._bamboo_spd_bonus = 0

    def on_inflict_debuff(self, wearer, target, buff, added_stacks):
        # 只有是 PoisonDebuff 且概率命中才触发
        if not isinstance(buff, Buffs.PoisonDebuff) or random.random() >= self.chance:
            return

        # ① 给自己加这次相同的层数
        own = next((b for b in wearer.buffs if isinstance(b, Buffs.PoisonDebuff)), None)
        if own:
            own.stacks = min(own.stacks + added_stacks, own.max_stacks)
        else:
            wearer.add_buff(Buffs.PoisonDebuff(stacks=added_stacks))

        # ② 统计当前毒总层数
        total_stacks = next((b.stacks for b in wearer.buffs if isinstance(b, Buffs.PoisonDebuff)), 0)

        # ③ 撤销旧加成
        wearer.attack -= self._bamboo_atk_bonus
        current_as = 6.0 / wearer.attack_interval
        base_as = current_as - self._bamboo_spd_bonus

        # ④ 重新计算加成（基于总毒层数）
        atk_bonus = total_stacks * 1
        spd_bonus = total_stacks * 0.1

        wearer.attack += atk_bonus
        wearer.attack_interval = 6.0 / (base_as + spd_bonus)

        # ⑤ 记录新的加成值
        self._bamboo_atk_bonus = atk_bonus
        self._bamboo_spd_bonus = spd_bonus

class GlassCannon(Talent):
    """【天赋】玻璃大炮：造成的伤害提升50%，受到的伤害也提升30%。"""
    display_name = "玻璃大炮"
    def on_init(self, wearer):
        wearer.attack *= 1.5
        wearer.damage_resistance -= 0.3

class Giant(Talent):
    """【天赋】巨人：最大生命值提升50%，但攻击速度降低20%。"""
    display_name = "巨人"
    def on_init(self, wearer):
        wearer.max_hp *= 1.5
        wearer.hp = wearer.max_hp
        wearer.attack_speed *= 0.8
        wearer.attack_interval = 6.0 / wearer.attack_speed


class Executioner(Talent):
    """【天赋】处决者：立即斩杀生命值低于20%的敌人。"""
    display_name = "处决者"
    
    def on_attack(self, wearer, target, dmg):
        # 这个效果在造成伤害后触发
        if target.hp > 0 and (target.hp / target.max_hp < 0.2):
            print(f"[处决者] 斩杀了 {target.name}！")
            kill_damage = target.hp
            packet = DamagePacket(amount=kill_damage, damage_type=DamageType.TRUE, source=wearer)
            target.take_damage(packet)

class Scavenger(Talent):
    """【天赋】清道夫：击败敌人时获得的金币提升50%。"""
    display_name = "清道夫"
    # (此天赋的逻辑需要在给予金币的地方检查)

class MagicShield(Talent):
    """【天赋】法力护盾：获得+20魔法抗性。"""
    display_name = "法力护盾"
    def on_init(self, wearer):
        wearer.magic_resist += 20

class FirstStrike(Talent):
    """【天赋】先发制人：进入战斗后的第一次攻击必定暴击。"""
    display_name = "先发制人"
    def on_init(self, wearer):
        self._used = False
    def on_attack(self, wearer, target, dmg):
        if not self._used:
            # 这个天赋最好在 before_attack 钩子中实现
            pass 
    
class LastStand(Talent):
    """【天赋】背水一战：生命值低于25%时，获得50%伤害减免。"""
    display_name = "背水一战"
    def on_init(self, wearer):
        wearer.damage_resistance_last_stand = 0.5 # 自定义一个属性
    # (此天赋的逻辑需要在 take_damage 中检查)

class AdrenalineRush(Talent):
    """【天赋】肾上腺素：每次杀死敌人，攻击速度提升10%，持续到战斗结束。"""
    display_name = "肾上腺素"
    # (此天赋逻辑复杂，需要战斗系统支持 on_kill 钩子)

class Brawler(Talent):
    """【天赋】格斗家：你无法装备副手物品，但你的基础攻击力提升30%。"""
    display_name = "格斗家"
    def on_init(self, wearer):
        # 只是修改规则和基础值，不再调用recalculate_stats
        wearer.SLOT_CAPACITY["offhand"] = 0
        wearer.base_attack *= 1.3 
        # 移除下面这两行
        # wearer.attack = wearer.base_attack
        # wearer.recalculate_stats()

class Adventurer(Talent):
    """【天赋】冒险者：获得的经验值提升50%。"""
    display_name = "冒险者"
    # (此天赋的逻辑需要在 add_exp 中检查)

class SacredRetribution(Talent):
    """【神圣报偿】: 每当你恢复生命时，对敌人造成等同于50%恢复量的真实伤害。"""
    display_name = "神圣报偿"

    def on_healed(self, wearer, healed_amount, combat_target):
        if combat_target and combat_target.hp > 0 and healed_amount > 0:
            damage = healed_amount * 0.5
            
            from damage import DamagePacket, DamageType
            packet = DamagePacket(amount=damage, damage_type=DamageType.TRUE, source=wearer)
            
            # ### 核心修改：先获取伤害报告，再用工具格式化日志 ###
            damage_details = combat_target.take_damage(packet)
            log_parts = format_damage_log(damage_details, action_name="神圣报偿")
            battle_logger.log(log_parts)

            # 不再需要返回任何东西


class Overwhelm(Talent):
    """【破势】: 对生命值高于50%的敌人，你的攻击造成200%伤害。"""
    display_name = "破势"

    def before_attack(self, wearer, target, packet: DamagePacket):
        """这是一个新的自定义钩子，会在Character.try_attack中被调用"""
        if target.hp / target.max_hp > 0.5:
            packet.amount *= 2

class SunfireAura(Talent):
    """【日炎光环】: 战斗开始时，对敌人施加【日炎灼烧】效果。"""
    display_name = "日炎光环"

    def on_battle_start(self, wearer, enemy):
        """这是一个新的自定义钩子，会在CombatScreen中被调用"""
        print(f"[{wearer.name}的日炎光环] 对 {enemy.name} 施加了灼烧！")
        enemy.add_debuff(Buffs.SunfireAuraDebuff(source_char=wearer))