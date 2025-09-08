# 文件: battle_logger.py (新文件)

class BattleLogger:
    def __init__(self):
        self._renderer = None

    def register_renderer(self, renderer_instance):
        """战斗开始时，由战斗界面调用，用于注册日志显示器"""
        print("[BattleLogger] 日志显示器已注册。")
        self._renderer = renderer_instance

    def unregister_renderer(self):
        """战斗结束时调用，用于注销显示器"""
        print("[BattleLogger] 日志显示器已注销。")
        self._renderer = None

    # battle_logger.py (修改后)

    def log(self, parts): # <--- 改动 1：移除 color 参数
        """
        全局日志接口。
        任何地方都可以调用这个函数来发送日志。
        """
        if self._renderer:
            # 直接调用显示器的 add_message 方法
            self._renderer.add_message(parts) # <--- 改动 2：移除 color 参数
        else:
            # 如果没有注册显示器（比如非战斗状态），则在控制台打印
            if isinstance(parts, list):
                # 如果是富文本列表，拼接后打印
                print("".join([p[0] for p in parts]))
            else:
                print(parts)

# 创建一个全局唯一的播报员实例
battle_logger = BattleLogger()