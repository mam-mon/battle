# main.py
from game import Game
import Equips
print(f"DEBUG: 正在从这个路径加载 Equips.py -> {Equips.__file__}")


if __name__ == "__main__":
    # 确保所有逻辑文件（Buffs, Talents, Equips, Character）都可被导入
    # 确保所有数据文件 (.json) 都在场
    g = Game()
    g.run()