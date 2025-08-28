# main.py
from game import Game

if __name__ == "__main__":
    # 确保所有逻辑文件（Buffs, Talents, Equips, Character）都可被导入
    # 确保所有数据文件 (.json) 都在场
    g = Game()
    g.run()