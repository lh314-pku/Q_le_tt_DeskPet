from PyQt6.QtWidgets import QMenu, QColorDialog, QWidget,QVBoxLayout,QPushButton,QLabel
from PyQt6.QtGui import QColor


class SettingsManager(QWidget):  # 改成继承 QWidget
    def __init__(self, window):
        """
        设置管理器窗口
        :param window: 传入主窗口实例，用于更新主窗口状态
        """
        super().__init__()
        self.window = window

        # 设置窗口标题和大小
        self.setWindowTitle("Settings")
        self.setFixedSize(300, 200)

        # 创建布局
        self.layout = QVBoxLayout(self)

        # 添加更改颜色按钮
        self.color_button = QPushButton("Change Gif Color", self)
        self.color_button.clicked.connect(self.open_color_picker)
        self.layout.addWidget(self.color_button)

        # 添加一个示例标签，可以显示当前颜色 (Optional)
        self.color_label = QLabel("No Color Selected", self)
        self.layout.addWidget(self.color_label)

        # 其他设置按钮 (根据需求添加更多设置内容)
        self.reset_button = QPushButton("Reset to Default", self)
        self.reset_button.clicked.connect(self.reset_to_default)
        self.layout.addWidget(self.reset_button)

    def open_color_picker(self):
        """弹出颜色选择器并设置 GIF 的颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            selected_color = color.name()  # 获取颜色代码 (如 "#RRGGBB")
            self.color_label.setText(f"Selected Color: {selected_color}")
            self.window.set_gif_color(selected_color)  # 假设主窗口有修改颜色的方法

    def reset_to_default(self):
        """重置 GIF 或窗口状态为默认值"""
        self.color_label.setText("No Color Selected")
        self.window.set_gif_color("#FFFFFF")  # 假设重置为白色 (根据你需求定制)
