# main.py
from game import Game
import Equips
print(f"DEBUG: 正在从这个路径加载 Equips.py -> {Equips.__file__}")


if __name__ == "__main__":
    g = Game()
    g.run()