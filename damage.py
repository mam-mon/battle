# damage.py
from enum import Enum, auto

class DamageType(Enum):
    PHYSICAL = auto()      # 普通物理伤害
    MAGIC = auto()         # 魔法伤害
    TRUE = auto()          # 真实伤害
    POISON = auto()        # 毒系伤害
    DRAGON_SOURCE = auto() # 龙源伤害

class DamagePacket:
    """一个用来封装所有伤害信息的数据结构"""
    def __init__(self, amount, damage_type, source=None,
                 is_critical=False, is_dot=False, 
                 is_sourceless=False, ignores_armor=False):
        
        self.amount = amount               # 基础伤害数值
        self.damage_type = damage_type     # 伤害类型 (物理, 魔法, 真实...)
        self.source = source               # 伤害来源 (哪个角色)
        
        # --- 各种标志 (Flags) ---
        self.is_critical = is_critical         # 是否暴击
        self.is_dot = is_dot                   # 是否为持续伤害(DOT)
        self.is_sourceless = is_sourceless     # 是否为无来源伤害 (如环境、反伤)
        self.ignores_armor = ignores_armor     # 是否穿甲 (无视防御)

    def copy(self):
        """创建一个副本，方便在计算过程中修改而不影响原始包"""
        return DamagePacket(
            self.amount, self.damage_type, self.source,
            self.is_critical, self.is_dot, self.is_sourceless, self.ignores_armor
        )