import random
import math
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

class MouseThrower():
    def __init__(self):
        super().__init__()
        self.initAnimation()

    def initAnimation(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.updatePosition)
        self.vx = 0
        self.vy = 0
        self.current_x = QCursor.pos().x()
        self.current_y = QCursor.pos().y()
        
        # 动画参数
        self.initial_speed = 60     # 初始速度（像素/帧）
        self.deceleration = 0.92    # 速度衰减系数
        self.bounce_factor = 0.7    # 反弹能量保留率
        self.min_speed = 0.5        # 最小停止速度
        self.interval = 10          # 刷新间隔（毫秒）

    def startThrow(self):
        """启动抛出效果"""
        # 获取当前光标位置并初始化速度
        self.current_x, self.current_y = QCursor.pos().x(), QCursor.pos().y()
        direction = random.uniform(0, 2 * math.pi)
        self.vx = self.initial_speed * math.cos(direction)
        self.vy = self.initial_speed * math.sin(direction)
        self.timer.start(self.interval)

    def updatePosition(self):
        """更新鼠标位置（带边缘检测）"""
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        screen_right = screen.width()
        screen_bottom = screen.height()

        # 计算理论新位置
        new_x = self.current_x + self.vx
        new_y = self.current_y + self.vy

        # 边界碰撞检测与响应
        # X轴边界
        if new_x < 0:
            new_x = 0
            self.vx = -self.vx * self.bounce_factor
        elif new_x > screen_right:
            new_x = screen_right
            self.vx = -self.vx * self.bounce_factor

        # Y轴边界
        if new_y < 0:
            new_y = 0
            self.vy = -self.vy * self.bounce_factor
        elif new_y > screen_bottom:
            new_y = screen_bottom
            self.vy = -self.vy * self.bounce_factor

        # 更新实际位置
        QCursor.setPos(int(new_x), int(new_y))
        self.current_x, self.current_y = new_x, new_y

        # 应用速度衰减
        self.vx *= self.deceleration
        self.vy *= self.deceleration

        # 检测停止条件
        velocity = math.hypot(self.vx, self.vy)
        if velocity < self.min_speed:
            self.timer.stop()