# states/base.py
class BaseState:
    def __init__(self, game):
        self.game = game

    def handle_event(self, event):
        """处理该状态下的单个事件"""
        pass

    def update(self):
        """更新该状态下的逻辑（非事件驱动）"""
        pass

    def draw(self, surface):
        """绘制该状态的画面"""
        pass