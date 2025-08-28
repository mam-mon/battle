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

    def on_attack(self, wearer, target, dmg):
        """
        在主攻后调用，如果命中且触发了三千世界，
        就返回额外攻击的文本列表；否则返回空列表。
        """
        extra_texts = []
        if random.random() < self.chance:
            # 额外出手两次
            for _ in range(2):
                text = wearer.perform_extra_attack(target)
                extra_texts.append(text)
        return extra_texts

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