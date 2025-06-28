import sys
from PyQt6.QtCore import Qt, QSize, QPoint, QPointF, QTimer, QDateTime
from PyQt6.QtGui import QMovie, QColor, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QGraphicsColorizeEffect
from Action import ActionManager
from chat.launch_ai import ChatWindow
from throw_mouse import MouseThrower
import os

def resource_path(relative_path):
    """ 解决打包后资源路径问题 """
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 使用示例（加载UI文件）
# ui_path = resource_path("MainWin.ui")
# uic.loadUi(ui_path, self)

# 使用示例（加载GIF）
# gif_path = resource_path("src/walk_left.gif")

class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.initUI()
        self.setWindowIcon(QIcon(resource_path("./src/stickpet.ico")))
        self.setWindowTitle("My Application")  # 设置窗口标题

        self.velocity_history = []  # 存储鼠标移动速度历史记录（时间戳，位置）
        self.speed_sample_duration = 50  # 速度采样时间区间长度（毫秒），可调整
        self.throw_threshold = 1000  # 抛出速度阈值（像素/秒）
        self.gravity = 980  # 重力加速度（像素/秒²）

        self.action_manager = ActionManager(self)  # 引入动作管理器
        self.action_manager.switch_to_default_gif()  # 默认设置待机动画

        self.drag_threshold = 1  # 拖动判断阈值（像素）
        self.press_pos = QPoint()  # 记录按下时的坐标
        self.is_dragging = False   # 拖动状态标记

        self.angry_value = 0

    
    def initUI(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.resize(QSize(150, 193))

        # 显示 GIF 动画
        self.label = QLabel(self)
        self.label.setFixedSize(QSize(150, 193))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 添加颜色效果
        self.color_effect = QGraphicsColorizeEffect(self)
        self.color_effect.setColor(QColor(QColor(255, 255, 255))) ## 这是默认颜色为白色（因为我的IDE是黑的，黑人容易看不到）
        self.color_effect.setEnabled(True)  # 启用颜色效果
        self.label.setGraphicsEffect(self.color_effect)

        # 创建一个文本框，用于显示文字
        self.text_box = QLabel(self)
        self.text_box.setStyleSheet("""
            background-color: rgba(0, 0, 0, 128);  /* 半透明背景 */
            color: white;
            border-radius: 10px;
            padding: 10px;
        """)
        self.text_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_box.setVisible(False)  # 初始隐藏
        self.text_box.resize(80, 50)  # 设置大小

        self.mouse_thrower = MouseThrower()

        # 可拖动窗口
        self.offset = None

    def update_gif(self, gif_path, gif_speed = 100):
        """更新显示的 GIF 动画"""
        gif = QMovie(gif_path)
        gif.setScaledSize(QSize(150, 193))
        gif.setSpeed(gif_speed)
        gif.start()
        self.label.setMovie(gif)

    def show_text_box(self, text):
        """显示文字文本框"""
        self.text_box.setText(text)
        self.text_box.move((self.width() - self.text_box.width()) // 2, self.height() // 2)  # 居中
        self.text_box.setVisible(True)

    def hide_text_box(self):
        """隐藏文字文本框"""
        self.text_box.setVisible(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # 记录按下时的全局坐标
            self.press_pos = event.globalPosition().toPoint()
            # 初始化拖动相关参数
            self.offset = self.press_pos - self.pos()
            # 重置状态
            self.is_dragging = False
            event.accept()


    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self.offset is not None:
            # 计算移动距离
            current_time = QDateTime.currentDateTime().toMSecsSinceEpoch()
            current_pos = event.globalPosition().toPoint()
            
            # 添加新数据点
            self.velocity_history.append( (current_time, current_pos) )
        
            # 动态清理旧数据：只保留最近 [speed_sample_duration] 毫秒的数据
            cutoff_time = current_time - self.speed_sample_duration
            self.velocity_history = [v for v in self.velocity_history if v[0] > cutoff_time]
        
            move_distance = (current_pos - self.press_pos).manhattanLength()

            # 超过阈值且不在下落状态视为拖动
            if move_distance > self.drag_threshold and not self.action_manager.is_falling:
                if not self.is_dragging:
                    self.action_manager.perform_no_menu_action("Drag")
                self.is_dragging = True
                self.move(current_pos - self.offset)

            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = None
            if not self.is_dragging:
                # 点击立即响应，坠落过程中点击不响应/特殊响应
                if not self.action_manager.is_falling:
                    if self.angry_value >= 5:
                        self.action_manager.perform_no_menu_action("Throw_mouse")
                    else:
                        self.action_manager.perform_no_menu_action("Hit")
                else:
                    pass # 坠落过程中点击的反应
            else:
                if len(self.velocity_history) >= 2:
                    sample_data = [v for v in self.velocity_history if v[0] >= (QDateTime.currentDateTime().toMSecsSinceEpoch() - self.speed_sample_duration)]
                
                    if len(sample_data) >= 2:
                        start_time, start_pos = sample_data[0]
                        end_time, end_pos = sample_data[-1]

                        time_diff = (end_time - start_time) / 1000  # 转换为秒

                        if time_diff > 0:
                            displacement = end_pos - start_pos
                            avg_velocity = QPointF(displacement.x()/time_diff, # 计算平均速度
                                                displacement.y()/time_diff)

                            # 如果速度超过阈值则触发抛出
                            if avg_velocity.manhattanLength() > self.throw_threshold:
                                self.action_manager.handle_throw(avg_velocity)
                                return  # 直接返回，不执行Drag_over动作

                self.action_manager.perform_no_menu_action("Drag_over") # 如果速度没超过阈值，执行drag_over

            self.is_dragging = False
            self.velocity_history.clear()  # 清空历史记录
            event.accept()

    def contextMenuEvent(self, event):
        """右键菜单事件"""
        self.action_manager.show_context_menu(event.globalPos())

    def set_gif_color(self, color=None):
        """设置 GIF 的颜色"""
        if color is None:
            self.color_effect.setEnabled(False)  # 禁用颜色效果
        else:
            self.color_effect.setColor(QColor(color))
            self.color_effect.setEnabled(True)  # 启用颜色效果

    def launch_ai(self):
        self.ai_window = ChatWindow()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    main_window = MyMainWindow()
    main_window.launch_ai()
    main_window.show()
    sys.exit(app.exec())