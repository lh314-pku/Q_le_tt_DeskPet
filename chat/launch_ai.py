import sys
from PyQt6 import QtWidgets
from PyQt6.QtWidgets import QApplication, QMainWindow
from .chat_ui import Ui_MainWindow
from .ai_assistant import AIChat

class ChatWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.font_size = 12  # 字体大小
        self.setup_ui()
        self.ai = None
        self.is_ai_responding = False
        self.current_ai_cursor = None

        self.apply_font_size(self.font_size)

        # 加载聊天历史
        from .ai_assistant import conversation_history
        for msg in conversation_history[1:]:
            if msg["role"] == "system": continue
            sender = "You" if msg["role"] == "user" else "AI"
            self._append_message(sender, msg["content"])

    def setup_ui(self):
        self.sendButton.clicked.connect(self.send_message)
        self.inputEdit.textChanged.connect(self.adjust_input_height)  # 文本变化时自动调整输入框高度
        self.clearButton.clicked.connect(self.clear_chat)  # 绑定清空聊天按钮事件
        self.chatHistory.setReadOnly(True)
        self.setWindowTitle("AI Chat Assistant")

    def adjust_input_height(self):
        """根据文本内容动态调整输入框高度"""
        document_height = self.inputEdit.document().size().height()
        self.inputEdit.setMinimumHeight(max(40, int(document_height + 10)))  # 自动调整高度

    def clear_chat(self):
        """清空聊天记录"""
        # 清空聊天窗口
        self.chatHistory.clear()
        # 清空聊天历史记录
        from ai_assistant import clear_history
        clear_history()


    def apply_font_size(self, size):
        """应用字体大小到所有文本组件"""
        style_sheet = f"""
            QTextEdit, QLineEdit {{
                font-size: {size}pt;
            }}
        """
        self.chatHistory.setStyleSheet(style_sheet)
        self.inputEdit.setStyleSheet(style_sheet)

    def closeEvent(self, event):
        """窗口关闭时自动保存聊天记录"""
        from .ai_assistant import save_history
        save_history()
        super().closeEvent(event)

    def send_message(self):
        """向AI发送消息"""
        user_input = self.inputEdit.toPlainText().strip()
        if not user_input:
            return

        # 显示用户消息
        self._append_message("You", user_input)
        self.inputEdit.clear()

        # 创建并启动工作线程
        self.ai = AIChat(user_input)
        self.ai.response_received.connect(self.handle_response)
        self.ai.error_occurred.connect(self.handle_error)
        self.ai.start()

    def _append_message(self, sender, message):
        """将消息显示到窗口"""
        message = message.replace('\n', '<br>')
        text = f"<b>{sender}</b><br>{message}<br>"
        self.chatHistory.append(text)
        self.chatHistory.verticalScrollBar().setValue(
            self.chatHistory.verticalScrollBar().maximum()
        )

    def handle_response(self, content, is_complete):
        """处理AI回复"""
        if is_complete:
            # 完成时添加换行并重置状态
            cursor = self.chatHistory.textCursor()
            if self.is_ai_responding:  # 确保在AI响应状态下才添加换行
                cursor.insertHtml("<br>")  # 添加空行分隔符
            self.is_ai_responding = False
            self.current_ai_cursor = None
        else:
            cursor = self.chatHistory.textCursor()

            if not self.is_ai_responding:
                # 新的AI响应开始
                self.is_ai_responding = True
                cursor.movePosition(cursor.MoveOperation.End)
                cursor.insertHtml('<br><b>AI</b><br>')
                self.current_ai_cursor = cursor  # 保存初始光标位置

            # 使用保存的光标位置进行插入
            if self.current_ai_cursor:
                self.current_ai_cursor.insertText(content)
                # 移动光标到新位置并更新显示
                self.current_ai_cursor.movePosition(cursor.MoveOperation.End)
                self.chatHistory.setTextCursor(self.current_ai_cursor)

            self.chatHistory.ensureCursorVisible()

    def handle_error(self, error_msg):
        self._append_message("System", f"Error: {error_msg}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
