import os
import json
from PyQt6.QtWidgets import (
    QMenu, QColorDialog, QWidget, QFrame, QSizePolicy, QComboBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt
from chat.prompt import PROMPT_EN, PROMPT_CH

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
            "language": "简体中文",  # 默认语言为中文
        }
        self.load_settings()
        self.initialize_ui_from_settings() # 加载并初始化配置
        self.default_prompts = {"简体中文": PROMPT_CH, "English": PROMPT_EN}
        self.language_is_CH = self.settings_data.get("language", "简体中文") == "简体中文"
        self.font = QFont("Microsoft YaHei", 15)

        # 窗口设置
        self.setWindowTitle("Settings")
        self.setFixedSize(800, 600)

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
        for i in reversed(range(self.right_layout.count())):
            widget = self.right_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        if option == "color":
            label = QLabel("Here you can change GIF color:")
            label.setFont(self.font)
            # QColorDialog 动态显示颜色选择器
            self.color_dialog = QColorDialog(self)
            self.color_dialog.setOptions(QColorDialog.ColorDialogOption.NoButtons)
            self.color_dialog.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            initial_color = QColor(self.settings_data["gif_color"])
            self.color_dialog.setCurrentColor(initial_color)
            self.color_dialog.currentColorChanged.connect(self.update_gif_color)
            self.right_layout.addWidget(label)
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
            prompt_text_edit.setText(self.get_prompt())
            prompt_text_edit.setPlaceholderText("Enter your prompt here...")
            prompt_text_edit.setMinimumHeight(450)
            prompt_text_edit.setFont(self.font)

            # 创建语言切换下拉框
            language_choose = QComboBox(self)
            language_choose.addItems(["简体中文", "English"])
            current_language = self.settings_data.get("language", "简体中文")
            language_choose.setCurrentText(current_language)
            language_choose.currentTextChanged.connect(self.update_language)

            # 保存按钮
            save_prompt_button = QPushButton("Save Prompt", self)
            save_prompt_button.clicked.connect(lambda: self.set_prompt(prompt_text_edit.toPlainText()))
            self.right_layout.addWidget(label)
            self.right_layout.addWidget(prompt_text_edit)
            self.right_layout.addWidget(language_choose)
            self.right_layout.addWidget(save_prompt_button)

    def update_language(self, language):
        """更新系统语言并刷新 Prompt"""
        self.settings_data["language"] = language
        self.language_is_CH = (language == "简体中文")
        self.save_settings()  # 保存配置
        print(f"Language switched to: {language}")

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
            "language": "简体中文",
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
        default_prompt = self.default_prompts["简体中文"] if self.language_is_CH else self.default_prompts["English"]
        return prompt if prompt else default_prompt

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

        # 初始化语言切换
        default_language = self.settings_data.get("language", "简体中文")
        self.language_is_CH = (default_language == "简体中文")

        # 初始化 API 设置
        if hasattr(self, "right_layout"):
            self.update_right_content("api")  # 自动切换到 API 配置页面

            # 更新 API 文本输入框
            api_key = self.settings_data.get("api_key", "")
            for i in range(self.right_layout.count()):
                widget = self.right_layout.itemAt(i).widget()
                if isinstance(widget, QTextEdit):  # 检测到 API 的输入框
                    widget.setText(api_key)

        # 初始化 Prompt（设置语言和提示文本）
        if hasattr(self, "right_layout"):
            self.update_right_content("prompt")  # 自动切换到 Prompt 页面
            for i in range(self.right_layout.count()):
                widget = self.right_layout.itemAt(i).widget()
                if isinstance(widget, QTextEdit):  # 检测到 Prompt 的输入框
                    widget.setText(self.get_prompt())

        print("UI initialized with settings.")
