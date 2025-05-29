import os
import json

from PyQt6 import QtGui
from PyQt6.QtWidgets import (
    QMenu, QColorDialog, QWidget, QFrame, QSizePolicy, QComboBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QCheckBox
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
from chat.prompt import PROMPT_STYLE

class SettingsManager(QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window

        # 定义配置文件路径和初始化默认数据
        self.config_file = "settings.json"
        self.settings_data = {
            "api_key": "",
            "prompt_text": "",
            "gif_color": "#FFFFFF",
            "can_bounce": True,
            "auto_move": True,  # 新增配置项：随机游走开关
            "min_interval": 3000,  # 新增配置项：最小间隔
            "max_interval": 8000  # 新增配置项：最大间隔
        }

        self.load_settings()
        self.initialize_ui_from_settings() # 加载并初始化配置
        self.default_prompts = PROMPT_STYLE
        self.font = QFont("Microsoft YaHei", 15)

        # 窗口设置
        self.setWindowTitle("Settings")
        self.setFixedSize(800, 600)
        self.setWindowIcon(QtGui.QIcon("./src/settings.ico"))

        # 主布局
        self.layout = QHBoxLayout(self)
        self.left_widget = QWidget()
        self.left_layout = QVBoxLayout(self.left_widget)
        self.left_widget.setMaximumWidth(230)
        self.left_widget.setMinimumWidth(230)
        self.left_widget.setStyleSheet("""
            QPushButton {font-size: 14px; 
                        padding: 8px 12px; /* 调整内部间距以让按钮稍微大气些 */
                        border-radius: 2px; /* 改为略微圆角（2px），更清爽 */
                        border: 1px solid #a9a9a9; /* 改为单色边框，显得干净简洁 */
                        color: #333333; /* 按钮文字颜色设为深灰，适合清爽风格 */
                        background-color: #f7f7f7; /* 默认浅灰底色，使按钮看起来干净 */}
            QPushButton:hover {background-color: #c5c5c5; }
            QPushButton:pressed {background-color: #c5c5c5; }
        """)

        self.right_widget = QWidget()
        self.right_layout = QVBoxLayout(self.right_widget)
        self.right_widget.setMinimumWidth(500)
        # 在 SettingsManager 的初始化方法中调整右侧布局（self.right_layout）的 spacing 和内容的字体、间距。
        self.right_layout.setSpacing(15)  # 增大控件之间的间距
        self.right_widget.setStyleSheet("""
            QLabel {
                font-size: 18px;              /* 更大字体 */
                color: #444444;              /* 深灰字体颜色 */
                margin-bottom: 6px;         /* 每个标签底部的额外间距 */
            }
            QPushButton {
                font-size: 18px;             /* 调整按钮的字体大小 */
                padding: 10px 18px;          /* 增加按钮的内部填充以显得更大气 */
                margin: 8px 0;               /* 按钮上下增加空隙间距 */
                border-radius: 6px;          /* 圆角按钮，更现代的外观 */
                border: 1px solid #8c8c8c;   /* 边框颜色 */
                background-color: #e6e6e6;   /* 背景色 */
                color: #333333;              /* 字体颜色 */
            }
            QPushButton:hover {background-color: #d6d6d6; }
            QPushButton:pressed {background-color: #cccccc; }
            QTextEdit {font-size: 16px; }
            QCheckBox {font-size: 14px; }
            QComboBox {font-size: 16px; padding: 8px; }
            QFrame {margin: 12px 0; }
        """)

        # 初始化内容
        self.right_layout.addWidget(QLabel("Please select an option from the left."))

        # 左侧按钮
        self.color_button = QPushButton("Change Gif Color", self)
        self.color_button.clicked.connect(lambda: self.update_right_content("color"))
        self.left_layout.addWidget(self.color_button)

        self.API_button = QPushButton("Setting API", self)
        self.API_button.clicked.connect(lambda: self.update_right_content("api"))
        self.left_layout.addWidget(self.API_button)

        self.prompt_button = QPushButton("Setting Your Prompt", self)
        self.prompt_button.clicked.connect(lambda: self.update_right_content("prompt"))
        self.left_layout.addWidget(self.prompt_button)

        self.others_button = QPushButton("Other Settings", self)
        self.others_button.clicked.connect(lambda: self.update_right_content("other"))
        self.left_layout.addWidget(self.others_button)

        self.reset_button = QPushButton("Reset to Default", self)
        self.reset_button.clicked.connect(lambda: self.update_right_content("reset"))
        self.left_layout.addWidget(self.reset_button)

        # 垂直分割线
        self.line = QFrame()
        self.line.setFrameShape(QFrame.Shape.VLine)  # 垂直分割线
        self.line.setStyleSheet("background-color: black; width: 2px;")

        # 布局绑定
        self.layout.addWidget(self.left_widget, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.line)
        self.layout.addWidget(self.right_widget, alignment=Qt.AlignmentFlag.AlignTop)

    def update_right_content(self, option):
        # 清空右侧布局
        def clear_layout(layout):
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    sub_layout = item.layout()
                    if sub_layout is not None:
                        clear_layout(sub_layout)
                        sub_layout.deleteLater()

        clear_layout(self.right_layout)  # 调用清除函数

        if option == "color":
            # QColorDialog 动态显示颜色选择器
            self.color_dialog = QColorDialog(self)
            self.color_dialog.setOptions(QColorDialog.ColorDialogOption.NoButtons)
            self.color_dialog.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            initial_color = QColor(self.settings_data["gif_color"])
            self.color_dialog.setCurrentColor(initial_color)
            self.color_dialog.currentColorChanged.connect(self.update_gif_color)
            self.right_layout.addWidget(self.color_dialog)

        elif option == "reset":
            label = QLabel("Do you want to reset all settings to default?")
            label.setFont(self.font)
            reset_confirm_button = QPushButton("Confirm Reset", self)
            reset_confirm_button.clicked.connect(self.reset_to_default)
            self.right_layout.addWidget(label)
            self.right_layout.addWidget(reset_confirm_button)

        elif option == "api":
            label = QLabel("Update your API settings below:")
            label.setFont(self.font)
            api_text_edit = QTextEdit(self)
            api_text_edit.setPlaceholderText("Enter your API key here...")
            api_text_edit.setPlainText(self.settings_data["api_key"])
            api_text_edit.setFont(self.font)
            save_api_button = QPushButton("Save API Key", self)
            save_api_button.clicked.connect(lambda: self.set_API(api_text_edit.toPlainText()))
            self.right_layout.addWidget(label)
            self.right_layout.addWidget(api_text_edit)
            self.right_layout.addWidget(save_api_button)

        elif option == "prompt":
            label = QLabel("Customize your own AI prompt:")
            label.setFont(self.font)
            prompt_text_edit = QTextEdit(self)
            prompt_text_edit.setPlaceholderText(PROMPT_STYLE)
            prompt_text_edit.setMinimumHeight(450)
            prompt_text_edit.setFont(self.font)

            # 保存按钮
            save_prompt_button = QPushButton("Save Prompt", self)
            save_prompt_button.clicked.connect(lambda: self.set_prompt(prompt_text_edit.toPlainText()))
            self.right_layout.addWidget(label)
            self.right_layout.addWidget(prompt_text_edit)
            self.right_layout.addWidget(save_prompt_button)

        elif option == "other":
            label = QLabel("Other Settings")
            label.setFont(self.font)

            bounce_checkbox = QCheckBox("Enable Bounce")
            bounce_checkbox.setChecked(self.settings_data.get("can_bounce", True))
            bounce_checkbox.setFont(self.font)
            bounce_checkbox.toggled.connect(self.set_bounce)
            self.right_layout.addWidget(label)
            self.right_layout.addWidget(bounce_checkbox)

            # 新增随机游走设置部分 ▼
            line1 = QFrame()
            line1.setFrameShape(QFrame.Shape.HLine)
            line1.setStyleSheet("margin:15px 0;")
            # 启用复选框
            auto_move_check = QCheckBox("Enable Random Walking")
            auto_move_check.setChecked(self.settings_data.get("auto_move", True))
            auto_move_check.toggled.connect(self.set_auto_move)

            # 时间间隔设置
            interval_label = QLabel("Move Interval (ms):")
            min_input = QTextEdit(str(self.settings_data.get("min_interval", 3000)))
            min_input.setMaximumHeight(45)
            max_input = QTextEdit(str(self.settings_data.get("max_interval", 8000)))
            max_input.setMaximumHeight(45)

            # 保存按钮
            save_btn = QPushButton("Save Intervals")
            save_btn.clicked.connect(lambda: self.set_interval(
                min_input.toPlainText(),
                max_input.toPlainText()
            ))
            # 布局管理
            interval_layout = QHBoxLayout()
            interval_layout.addWidget(QLabel("Min:"))
            interval_layout.addWidget(min_input)
            interval_layout.addWidget(QLabel("Max:"))
            interval_layout.addWidget(max_input)
            interval_layout.addWidget(save_btn)
            # 组合控件添加到主界面
            self.right_layout.addWidget(line1)
            self.right_layout.addWidget(auto_move_check)
            self.right_layout.addWidget(interval_label)
            self.right_layout.addLayout(interval_layout)

    def update_gif_color(self, color=None):
        if isinstance(color, QColor):
            color = color.name()
        elif color is None:
            color = "#FFFFFF"
        self.settings_data["gif_color"] = color
        self.save_settings()
        self.window.set_gif_color(color)

    def reset_to_default(self):
        self.settings_data = {
            "api_key": "",
            "prompt_text": "",
            "gif_color": "#FFFFFF",
            "can_bounce": True,
            "auto_move": True,  # 新增配置项：随机游走开关
            "min_interval": 3000,  # 新增配置项：最小间隔
            "max_interval": 8000  # 新增配置项：最大间隔
        }
        self.update_gif_color("#FFFFFF")
        self.save_settings()
        print("Settings reset to default.")

    def set_API(self, api_key):
        if api_key.strip():
            self.settings_data["api_key"] = api_key
            self.save_settings()
            print(f"API Key saved: {api_key}")

    def set_prompt(self, prompt_text):
        if prompt_text.strip():
            self.settings_data["prompt_text"] = prompt_text
            self.save_settings()
            print(f"Prompt saved: {prompt_text}")

    def get_prompt(self):
        prompt = self.settings_data.get("prompt_text", "").strip()
        return prompt if prompt else PROMPT_STYLE

    def set_bounce(self, value):
        self.settings_data["can_bounce"] = value
        self.save_settings()
        self.window.action_manager.can_bounce = value

    def save_settings(self):
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings_data, f, indent=4)
                print("Settings saved successfully.")
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.settings_data = json.load(f)
                    print("Settings loaded successfully.")
            except Exception as e:
                print(f"Error loading settings: {e}")
        else:
            print("Settings file not found. Using default values.")

    def initialize_ui_from_settings(self):
        # 根据加载的设置初始化各种 UI 控件

        # 初始化颜色选择器
        if "gif_color" in self.settings_data:
            gif_color = self.settings_data["gif_color"]
            initial_color = QColor(gif_color)
            if hasattr(self, "color_dialog"):
                self.color_dialog.setCurrentColor(initial_color)
            self.window.set_gif_color(gif_color)

        # 初始化 API 设置
        if hasattr(self, "right_layout"):
            self.update_right_content("api")  # 自动切换到 API 配置页面

            # 更新 API 文本输入框
            api_key = self.settings_data.get("api_key", "")
            for i in range(self.right_layout.count()):
                widget = self.right_layout.itemAt(i).widget()
                if isinstance(widget, QTextEdit):  # 检测到 API 的输入框
                    widget.setText(api_key)

        # 初始化 Prompt
        if hasattr(self, "right_layout"):
            self.update_right_content("prompt")  # 自动切换到 Prompt 页面
            for i in range(self.right_layout.count()):
                widget = self.right_layout.itemAt(i).widget()
                if isinstance(widget, QTextEdit):  # 检测到 Prompt 的输入框
                    widget.setText(self.get_prompt())

        print("UI initialized with settings.")

    # 在SettingsManager中修改保存方法
    def set_auto_move(self, enable):
        """处理启用/禁用随机游走"""
        self.settings_data["auto_move"] = enable
        self.save_settings()
        # ✔️ 通过安全访问防止空指针，并添加默认值保护
        if hasattr(self.window, 'action_manager'):
            self.window.action_manager.auto_move_enabled = enable

    def set_interval(self, min_val, max_val):
        """处理时间间隔修改"""
        try:
            min_int = int(min_val) if min_val else 3000
            max_int = int(max_val) if max_val else 8000
            if 1000 <= min_int <= max_int:
                self.settings_data["min_interval"] = min_int
                self.settings_data["max_interval"] = max_int
                self.save_settings()
                # ✔️ 添加安全校验
                if hasattr(self.window, 'action_manager'):
                    if hasattr(self.window.action_manager, 'schedule_auto_move'):
                        self.window.action_manager.min_interval = min_int
                        self.window.action_manager.max_interval = max_int
                        self.window.action_manager.schedule_auto_move()
        except ValueError:
            print("Invalid interval value")
