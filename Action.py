from PyQt6.QtGui import QAction, QCursor, QTransform
from PyQt6.QtCore import QTimer, QPoint, QPointF, Qt
from PyQt6.QtWidgets import QMenu, QColorDialog, QSystemTrayIcon, QApplication
from Settings import SettingsManager  # 引入新的设置管理器
import random

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
        self.is_falling = False # 是否被扔出去了

        # 移动速度设置
        self.walk_speed = 1  # Walk 时的移动速度
        self.run_speed = 5  # Run 时的移动速度
        self.climb_speed = 2 # 爬的速度
        self.current_speed = None

        # 待机时随机移动
        self.possible_actions = ["Walk_left", "Walk_right", "Climb_up", "Climb_down"]
        self.auto_move_timer = QTimer()
        self.auto_move_timer.timeout.connect(self.trigger_auto_move)
        self.auto_move_timer.setSingleShot(True)
        self.schedule_auto_move()

        # 封装动作与 GIF 的映射关系以及动画时长
        self.actions_config = { # 这些动作会显示在右键菜单
            "Walk_right": {"gif": "./src/walk_right.gif", "duration": 5000},
            "Walk_left": {"gif": "./src/walk_left.gif", "duration": 5000},
            "Run": {"gif": "./src/run.gif", "duration": 5000},
            "Climb_up": {"gif": "./src/climb_up.gif", "duration": 5000},
            "Climb_down": {"gif": "./src/climb_down.gif", "duration": 5000},
        }
        self.no_menu_actions_config = { # 这些动作不会显示在右键菜单
            "Hit": {"gif": "./src/hit.gif", "duration": 500},
            "Drag": {"gif": "./src/drag.gif", "duration": 0}, # duration设为0表示动作一直持续到下一个动作发生
            "Drag_over": {"gif": "./src/drag_over.gif", "duration": 1000}, # 拖动结束的跌落动作。注意，这个动作不能依赖【gif循环播放】，因此duration需要根据实际gif时长设置。
            "Thrown": {"gif": "./src/thrown.gif", "duration": 0},
            "Throw_mouse": {"gif": "./src/throw.gif", "duration": 500} # 需要动作😊😊
        }

        self.default_gif_path = "./src/default.gif"  # 默认待机动画路径
        self.talk_gif_path = "./src/talk.gif"  # Talk 动画路径

        self.throw_speed = QPointF(0, 0)  # 当前抛出速度
        self.gravity = self.window.gravity
        self.throw_timer = QTimer()  # 抛出运动定时器
        self.throw_timer.timeout.connect(self.update_throw_motion)
 
        # 初始化设置窗口
        self.settings_window = SettingsManager(self.window)

        ########################################
        self.bounce = None # 是否反弹（和设置绑定）
        ########################################

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

    def perform_action(self, action_name, duration = None):
        """执行菜单动作"""
        self.end_action() # 立即停止当前动作

        # 获取动画配置
        config = self.actions_config[action_name]

        # 根据动作类型设置不同的移动速度
        if action_name == "Walk_right":
            self.current_speed = QPoint(self.walk_speed, 0)
        elif action_name == "Walk_left":
            self.current_speed = QPoint(-self.walk_speed, 0)
        elif action_name == "Run":
            self.current_speed = QPoint(self.run_speed, 0)
        elif action_name == "Climb_up":
            self.current_speed = QPoint(0, -self.climb_speed)
        elif action_name == "Climb_down":
            self.current_speed = QPoint(0, self.climb_speed)

        self.is_in_action = True
        self.window.update_gif(config["gif"])
        self.start_moving_window()

        # 限时恢复
        self.action_timer.timeout.connect(self.end_action)
        if duration:
            self.action_timer.start(duration)  # 启动计时
        else:
            self.action_timer.start(config["duration"])  # 启动计时

    def perform_no_menu_action(self, action_name):
        """执行非菜单动作"""
        self.end_action() # 立即停止当前动作
        
        config = self.no_menu_actions_config[action_name]
        self.is_in_action = True
        
        self.window.update_gif(config["gif"])

        if action_name == "Throw_mouse":
            self.window.mouse_thrower.startThrow()
            self.window.angry_value = max(0, self.window.angry_value - 2)
        elif action_name == "Hit":
            self.window.angry_value = min(10, self.window.angry_value + 1)
        elif action_name == "Drag_over":
            self.window.angry_value = max(0, self.window.angry_value - 1)
        elif action_name == "Thrown":
            self.window.angry_value = min(10, self.window.angry_value + 2)

        # print("Angry Value:", self.window.angry_value)

        if config["duration"] > 0: # duration设为0表示动作一直持续到下一个动作发生
            # 限时恢复
            self.action_timer.timeout.connect(self.end_action)
            self.action_timer.start(config["duration"])

    def schedule_auto_move(self):
        """调度下一次自动移动"""
        interval = random.randint(2000, 5000)  # 随机间隔
        self.auto_move_timer.start(interval)

    def trigger_auto_move(self):
        """完全随机触发移动"""
        if not self.is_in_action and not self.is_falling:
            # 从所有可能动作中随机选择
            selected = random.choice(self.possible_actions)
            duration = random.randint(2000, 4000)
            self.perform_action(selected, duration)

        self.schedule_auto_move()

    def show_talk_text(self):
        """显示对话功能"""
        self.end_action()
        self.is_in_action = True
        self.window.update_gif(self.talk_gif_path, 80)
        self.window.show_text_box("Hello!")
        self.action_timer.timeout.connect(self.end_action)
        self.action_timer.start(3000)

        self.window.ai_window.show()

    def end_action(self):
        """结束当前动作"""
        if not self.is_in_action:
            return
        
        self.window.hide_text_box()

        # 取消前一个定时器
        if self.action_timer and self.action_timer.isActive():
            self.action_timer.stop()

        # 强制重置动画（优化播放流畅度）
        if self.window.label.movie():
            self.window.label.movie().stop()

        self.stop_moving_window()
        self.switch_to_default_gif()
        self.is_in_action = False
        self.schedule_auto_move()

    def handle_throw(self, initial_velocity):
        """处理抛出动作"""
        self.end_action()
        # 播放抛出动画
        self.is_falling = True
        self.perform_no_menu_action("Thrown")
        # 设置初速度
        self.throw_speed = initial_velocity
        # 启动抛体运动定时器
        self.throw_timer.start(16)  # ~60fps

    def update_throw_motion(self):
        """更新抛体运动位置"""
        # 应用重力加速度
        self.throw_speed.setY(self.throw_speed.y() + self.gravity * 0.016)  # delta_time=0.016s
        
        # 计算新位置
        current_pos = self.window.pos()
        new_x = current_pos.x() + self.throw_speed.x() * 0.016
        new_y = current_pos.y() + self.throw_speed.y() * 0.016
        
        # 边界检测
        screen = self.window.screen().availableGeometry()
        if self.bounce:
            if (new_x < screen.left() and  current_pos.x() >= screen.left()) or (new_x > screen.right() - self.window.width() and current_pos.x() <= screen.right() - self.window.width()):
                self.throw_speed.setX(-self.throw_speed.x()) # 左右边界完全弹性
            if new_y < screen.top() and current_pos.y() >= screen.top():
                self.throw_speed.setY(-self.throw_speed.y()) # 上边界完全弹性
        if new_y > screen.bottom() - self.window.height():
            self.throw_timer.stop() # 下边界直接结束
            self.end_action()
            self.is_falling = False
            self.perform_no_menu_action("Drag_over") # 播放动作过渡
            self._come_back()
            return

        self.window.move(QPoint(int(new_x), int(new_y)))
        
    def _come_back(self):
        """被扔出屏幕后自行返回"""
        current_pos = self.window.pos()
        
        # 边界检测
        screen = self.window.screen().availableGeometry()
        if current_pos.x() < screen.left():
            self.perform_action("Walk_left")
        elif current_pos.x() > screen.right() - self.window.width():
            self.perform_action("Walk_right")

    def switch_to_default_gif(self):
        """切换为默认待机动画"""

        self.window.update_gif(self.default_gif_path, 50)

    def start_moving_window(self):
        """启动窗口移动"""
        # 先断开之前的连接，避免重复连接导致速度叠加
        try:
            self.move_timer.timeout.disconnect()
        except TypeError:
            pass  # 如果之前没有连接，忽略错误
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

        # 水平方向
        if self.current_speed.x() > 0 and new_x >= screen.right(): # 当速度向右时，如果到达右边界，从左边界重新出现
            new_x = screen.left() - self.window.width()
        elif self.current_speed.x() < 0 and new_x + self.window.width() <= screen.left(): # 当速度向左时，如果到达左边界，从右边界重新出现
            new_x = screen.right()

        # 垂直方向循环逻辑
        dy = 50
        if self.current_speed.y() < 0 and new_y <= screen.top() - self.window.height():
            new_y = screen.bottom() + dy  # 向上越界时从底部出现
        elif self.current_speed.y() > 0 and new_y >= screen.bottom() + dy:
            new_y = screen.top() - self.window.height()  # 向下越界时从顶部出现

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
