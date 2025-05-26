import sys
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer
from PyQt6.QtGui import QMovie, QColor, QIcon
from PyQt6.QtWidgets import QApplication, QMainWindow, QLabel, QGraphicsColorizeEffect
from Action import ActionManager
from chat.launch_ai import ChatWindow

class MyMainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MyMainWindow, self).__init__(parent)
        self.initUI()
        self.setWindowIcon(QIcon("./src/icon.png"))
        self.setWindowTitle("My Application")  # 设置窗口标题
        self.action_manager = ActionManager(self)  # 引入动作管理器
        self.action_manager.switch_to_default_gif()  # 默认设置待机动画
        
        # 添加点击计数器和点击间隔时间控制器（lrq, 5.26）
        self.drag_threshold = 1  # 拖动判断阈值（像素）
        self.press_pos = QPoint()  # 记录按下时的坐标
        self.is_dragging = False   # 拖动状态标记


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

        # 可拖动窗口
        self.offset = None

    def update_gif(self, gif_path, gif_speed = 100):
        """更新显示的 GIF 动画"""
        gif = QMovie(gif_path)
        gif.setScaledSize(QSize(140, 193))
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
            current_pos = event.globalPosition().toPoint()
            move_distance = (current_pos - self.press_pos).manhattanLength()
            
            if move_distance > self.drag_threshold:
                # 超过阈值视为拖动
                if not self.is_dragging:
                    self.action_manager.perform_no_menu_action("Drag")
                self.is_dragging = True
                self.move(current_pos - self.offset)

            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.offset = None
            if not self.is_dragging:
                # 点击立即响应
                self.action_manager.perform_no_menu_action("Hit")
            else:
                self.action_manager.perform_no_menu_action("Drag_over")
            self.is_dragging = False
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
