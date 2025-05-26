from PyQt6.QtGui import QAction, QCursor, QTransform
from PyQt6.QtCore import QTimer, QPoint, Qt
from PyQt6.QtWidgets import QMenu, QColorDialog, QSystemTrayIcon, QApplication
from Settings import SettingsManager  # 引入新的设置管理器

class ActionManager:
    def __init__(self, window):
        """
        初始化动作管理器
        :param window: 传入主窗口实例，用于操作主窗口的方法
        """
        self.window = window
        self.tray_icon = None  # 初始化托盘图标变量
        self.direction = QPoint(1, 0)  # 初始方向
        self.move_timer = QTimer()  # 移动计时器
        self.action_timer = QTimer()  # 用于设置限时动作的定时器
        self.action_timer.setSingleShot(True)  # 设置为单次模式
        self.is_in_action = False  # 标记是否当前处于动作中

        # 移动速度设置
        self.walk_speed = QPoint(2, 0)  # Walk 时的移动速度
        self.run_speed = QPoint(6, 0)  # Run 时的移动速度
        self.current_speed = self.walk_speed  # 默认速度是 Walk 的速度

        # 封装动作与 GIF 的映射关系以及动画时长
        self.actions_config = { # 这些动作会显示在右键菜单
            "Walk": {"gif": "./src/walk.gif", "duration": 5000},
            "Run": {"gif": "./src/run.gif", "duration": 5000},
        }
        self.no_menu_actions_config = { # 这些动作不会显示在右键菜单
            "Hit": {"gif": "./src/hit.gif", "duration": 500},
            "Drag": {"gif": "./src/drag.gif", "duration": 0}, # duration设为0表示动作一直持续到下一个动作发生
            "Drag_over": {"gif": "./src/drag_over.gif", "duration": 1000} # 拖动结束的跌落动作。
            # 注意，这个动作不能依赖【gif循环播放】，因此duration需要根据实际gif时长设置。
        }

        self.default_gif_path = "./src/default.gif"  # 默认待机动画路径
        self.talk_gif_path = "./src/talk.gif"  # Talk 动画路径

        # 初始化设置窗口
        self.settings_window = SettingsManager(self.window)
        # 初始化右键菜单
        self.init_context_menu()
        # 初始化托盘图标
        self.init_tray_icon()


    def init_context_menu(self):
        """初始化右键菜单"""
        self.context_menu = QMenu(self.window)
        # 创建 "Action" 子菜单
        self.action_menu = QMenu("Action", self.context_menu)  # Action 菜单
        # 添加动作到 Action 子菜单
        for action_name in self.actions_config.keys():
            action = QAction(action_name, self.window)
            action.triggered.connect(lambda _, act=action_name: self.perform_action(act))
            self.action_menu.addAction(action)
        # 其它菜单选项
        self.talk_action = QAction("Talk", self.window)  # 保持 Talk 独立
        self.minimize_to_tray_action = QAction("Minimize to Tray", self.window)
        self.exit_action = QAction("Exit", self.window)
        self.settings_action = QAction("Settings", self.window)
        # 与槽函数关联
        self.talk_action.triggered.connect(self.show_talk_text)
        self.minimize_to_tray_action.triggered.connect(self.minimize_to_tray)
        self.exit_action.triggered.connect(self.window.close)
        self.settings_action.triggered.connect(self.open_settings_window)  # 设置打开窗口的行为
        # 添加到右键菜单
        self.context_menu.addMenu(self.action_menu)  # 添加 Action 菜单
        self.context_menu.addAction(self.settings_action)
        self.context_menu.addAction(self.talk_action)
        self.context_menu.addAction(self.minimize_to_tray_action)
        self.context_menu.addAction(self.exit_action)
        self.context_menu.addSeparator()

    def open_settings_window(self):
        """打开设置窗口"""
        self.settings_window.show()  # 显示设置窗口
        self.settings_window.raise_()  # 将窗口置于最前方

    def perform_action(self, action_name):
        """执行菜单动作"""
        self.end_action() # 立即停止当前动作

        # 获取动画配置
        config = self.actions_config[action_name]

        # 根据动作类型设置不同的移动速度
        if action_name == "Walk":
            self.current_speed = self.walk_speed
        elif action_name == "Run":
            self.current_speed = self.run_speed

        self.is_in_action = True
        self.window.update_gif(config["gif"])
        self.start_moving_window()

        # 限时恢复
        self.action_timer.timeout.connect(self.end_action)
        self.action_timer.start(config["duration"])  # 启动计时

    def perform_no_menu_action(self, action_name):
        """执行非菜单动作"""
        self.end_action() # 立即停止当前动作
        
        config = self.no_menu_actions_config[action_name]
        self.is_in_action = True
        
        self.window.update_gif(config["gif"])

        if config["duration"] > 0: # duration设为0表示动作一直持续到下一个动作发生
            # 限时恢复
            self.action_timer.timeout.connect(self.end_action)
            self.action_timer.start(config["duration"])

###########################################################
    def show_talk_text(self):
        """显示对话功能"""
        self.end_action()
        self.is_in_action = True
        self.window.update_gif(self.talk_gif_path, 80)
        self.window.show_text_box("Hello!")
        self.action_timer.timeout.connect(self.end_action)
        self.action_timer.start(3000)

        self.window.ai_window.show()
###########################################################

    # def end_talk_action(self): # 已与end_action合并，可以这段代码删掉了
    #     """结束对话功能"""
    #     self.window.hide_text_box()
    #     self.switch_to_default_gif()
    #     self.is_in_action = False

    def end_action(self):
        """结束当前动作"""
        if not self.is_in_action:
            return
        
        self.window.hide_text_box()

        # 取消前一个定时器
        if self.action_timer and self.action_timer.isActive():
            print("计时停止")
            self.action_timer.stop()

        # 强制重置动画（优化播放流畅度）
        if self.window.label.movie():
            self.window.label.movie().stop()

        self.stop_moving_window()
        self.switch_to_default_gif()
        self.is_in_action = False

    def switch_to_default_gif(self):
        """切换为默认待机动画"""

        self.window.update_gif(self.default_gif_path, 50)

    def start_moving_window(self):
        """启动窗口移动"""
        self.move_timer.timeout.connect(self.move_window)
        self.move_timer.start(25)  # 保持定时器更新频率一致，速度差异由 self.current_speed 控制

    def stop_moving_window(self):
        """停止窗口移动"""
        self.move_timer.stop()

    def move_window(self):
        """实现窗口的移动逻辑，使得窗口到达右边界时从左边界重新出现"""
        # 检查窗口和速度对象的完整性
        if not hasattr(self, 'window') or self.window is None:
            raise AttributeError("The 'window' object is not initialized.")
        if not hasattr(self, 'current_speed') or self.current_speed is None:
            raise AttributeError("The 'current_speed' vector is not initialized.")

        current_pos = self.window.pos()
        new_x = current_pos.x() + self.current_speed.x()
        new_y = current_pos.y() + self.current_speed.y()
        screen = self.window.screen().availableGeometry()

        # 水平方向：如果到达右边界，从左边界重新出现
        if new_x >= screen.right():
        # if new_x + self.window.width() >= screen.right():
            new_x = screen.left()

        # 垂直边界逻辑（如果需要）
        if new_y <= screen.top() or new_y + self.window.height() >= screen.bottom():
            self.current_speed.setY(-self.current_speed.y())  # 反向 Y 轴方向

        # 移动窗口到新的位置
        self.window.move(QPoint(new_x, new_y))

    def flip_gif(self, horizontal=False, vertical=False):
        """
        替换后的 `flip_gif` 函数不再进行翻转操作，仅保留占位。
        """
        pass  # 由于要求不再翻转 GIF，此处留空

    def init_tray_icon(self):
        """初始化托盘图标"""
        self.tray_icon = QSystemTrayIcon(self.window)
        self.tray_icon.setIcon(self.window.windowIcon())
        self.tray_menu = QMenu()
        restore_action = QAction("Restore", self.window)
        restore_action.triggered.connect(self.window.show)
        exit_action = QAction("Exit", self.window)
        exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(restore_action)
        self.tray_menu.addAction(exit_action)
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)

    def on_tray_icon_activated(self, reason):
        """托盘图标被激活时恢复窗口"""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.window.show()

    def minimize_to_tray(self):
        """最小化到托盘"""
        self.tray_icon.show()
        self.window.hide()

    def open_color_picker(self):
        """弹出颜色选择器并设置 GIF 的颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.window.set_gif_color(color.name())

    def show_context_menu(self, position):
        """显示右键菜单"""
        self.context_menu.exec(position)
