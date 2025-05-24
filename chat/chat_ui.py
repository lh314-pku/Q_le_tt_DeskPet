from PyQt6 import QtCore, QtWidgets, QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QTextEdit

# QTextEdit 重新绑定按键事件
class CustomTextEdit(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = parent  # 保存父窗口引用，以便调用发送消息方法
    def keyPressEvent(self, event):
        # 获取按键是否是 Ctrl+Enter
        if event.key() == Qt.Key.Key_Return and (event.modifiers() & Qt.KeyboardModifier.ControlModifier):
            # Ctrl+Enter 换行
            self.insertPlainText("\n")
        elif event.key() == Qt.Key.Key_Return:
            # Enter 发送消息
            if self.parent_widget:  # 检查父窗口是否存在
                self.parent_widget.send_message()
        else:
            # 其他按键的默认行为
            super().keyPressEvent(event)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(900, 600)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        # 创建主垂直布局
        self.main_layout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建分割器
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)

        # 聊天历史区域
        self.chatHistory = QtWidgets.QTextEdit()
        self.chatHistory.setMinimumHeight(100)  # 设置最小高度
        self.chatHistory.setReadOnly(True)

        # 输入区域容器
        self.input_container = QtWidgets.QWidget()
        self.input_layout = QtWidgets.QVBoxLayout(self.input_container)
        self.input_layout.setContentsMargins(0, 0, 0, 0)

        # 创建输入框和按钮的底部布局
        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)

        # 输入框组件
        self.inputEdit = CustomTextEdit(parent=MainWindow)
        self.inputEdit.setMinimumHeight(40)  # 设置输入框的最小高度
        self.inputEdit.setPlaceholderText("[请输入文本，Ctrl+Enter换行]")

        # 创建发送按钮
        self.sendButton = QtWidgets.QPushButton()
        self.sendButton.setFixedSize(50, 40)  # 设置按钮固定大小
        self.sendButton.setIcon(QtGui.QIcon("./chat/imgs/send.svg")) # 设置图标
        self.sendButton.setToolTip("发送消息")  # 设置提示文本

        # 创建停止按钮
        self.stopButton = QtWidgets.QPushButton()
        self.stopButton.setFixedSize(50, 40)
        self.stopButton.setIcon(QtGui.QIcon("./chat/imgs/pause.svg"))
        self.stopButton.setToolTip("停止生成")

        # 创建清空按钮
        self.clearButton = QtWidgets.QPushButton()
        self.clearButton.setFixedSize(45, 35)
        self.clearButton.setIcon(QtGui.QIcon("./chat/imgs/trash.svg"))
        self.clearButton.setToolTip("清空聊天记录")
        self.clearButton.setStyleSheet(
            """
            QPushButton {
                background-color: #f1a9a9;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ef8e8e;
            }
            QPushButton:pressed {
                background-color: #cf7373;
            }
            """
        )
        # 添加到底部布局中，发送按钮左边
        self.bottom_layout.insertWidget(0, self.clearButton)  # 插入到布局的最左边

        # 添加到布局中
        self.input_layout.addWidget(self.inputEdit)  # 输入框占整行
        self.bottom_layout.addStretch()  # 添加弹性空间，保证按钮在右侧
        self.bottom_layout.addWidget(self.stopButton)
        self.bottom_layout.addWidget(self.sendButton)
        self.input_layout.addLayout(self.bottom_layout)

        # 将组件添加到分割器
        self.splitter.addWidget(self.chatHistory)
        self.splitter.addWidget(self.input_container)

        # 设置分割器拉伸系数
        self.splitter.setStretchFactor(0, 3)  # 聊天区域占3份
        self.splitter.setStretchFactor(1, 1)  # 输入区域占1份

        self.main_layout.addWidget(self.splitter)
        MainWindow.setCentralWidget(self.centralwidget)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "AI Chat Assistant"))

