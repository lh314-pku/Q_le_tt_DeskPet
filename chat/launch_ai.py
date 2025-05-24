import sys

from PyQt6 import QtGui
from PyQt6.QtWidgets import QApplication, QMainWindow
from .chat_ui import Ui_MainWindow
from .ai_assistant import AIChat

class ChatWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.font_size = 12  # 字体大小
        self.pic_size = 20 # 头像大小
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
        # self.inputEdit.textChanged.connect(self.adjust_input_height)  # 文本变化时自动调整输入框高度
        self.clearButton.clicked.connect(self.clear_chat)  # 绑定清空聊天按钮事件
        self.stopButton.clicked.connect(self.stop_ai_response)
        self.chatHistory.setReadOnly(True)
        self.setWindowTitle("AI Chat Assistant")
        self.setWindowIcon(QtGui.QIcon("./chat/imgs/app_ico.ico"))

    def adjust_input_height(self):
        """根据文本内容动态调整输入框高度"""
        document_height = self.inputEdit.document().size().height()
        self.inputEdit.setMinimumHeight(max(40, int(document_height + 10)))

    def clear_chat(self):
        """清空聊天记录"""
        # 清空聊天窗口
        self.chatHistory.clear()
        # 清空聊天历史记录
        from .ai_assistant import clear_history
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
        if not self.is_ai_responding:
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
        cursor = self.chatHistory.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        # 创建表格（1行2列）
        table_format = QtGui.QTextTableFormat()
        table_format.setCellPadding(5)
        table = cursor.insertTable(1, 2, table_format)
        # 设置头像单元格
        avatar_cell = table.cellAt(0, 0)
        avatar_cursor = avatar_cell.firstCursorPosition()
        avatar_path = "./chat/imgs/user.svg" if sender == "You" else "./chat/imgs/ai.svg"
        avatar_cursor.insertHtml(f'<img src="{avatar_path}" width="{self.pic_size}" height="{self.pic_size}"/>')
        # 设置内容单元格格式
        content_format = QtGui.QTextTableCellFormat()
        content_format.setLeftPadding(10)  # 强制左侧间距
        content_cell = table.cellAt(0, 1)
        content_cell.setFormat(content_format)
        # 插入消息内容
        content_cursor = content_cell.firstCursorPosition()
        message = message.replace('\n', '<br>')
        sender = "StickMan" if sender == "AI" else sender
        content_cursor.insertHtml(f"<b>{sender}</b><br>{message}")
        # 添加消息间距
        cursor.insertHtml("<br>")
        self.chatHistory.verticalScrollBar().setValue(
            self.chatHistory.verticalScrollBar().maximum()
        )

    def handle_response(self, content, is_complete):
        """处理AI回复"""
        if is_complete:
            self.is_ai_responding = False
            self.current_ai_cursor = None
            # 在最后添加换行
            cursor = self.chatHistory.textCursor()
            cursor.insertHtml("<br>")
        else:
            cursor = self.chatHistory.textCursor()
            if not self.is_ai_responding:
                # 初始化表格结构
                self.is_ai_responding = True
                cursor.movePosition(cursor.MoveOperation.End)

                # 创建表格格式
                table_format = QtGui.QTextTableFormat()
                table_format.setCellPadding(5)

                # 插入1行2列的表格
                self.current_table = cursor.insertTable(1, 2, table_format)

                # 设置头像单元格
                cell_cursor = self.current_table.cellAt(0, 0).firstCursorPosition()
                cell_cursor.insertHtml(f'<img src="./chat/imgs/ai.svg" width="{self.pic_size}" height="{self.pic_size}"/>')

                # 设置内容单元格格式
                content_format = QtGui.QTextTableCellFormat()
                content_format.setLeftPadding(10)  # 设置左侧间距
                self.current_table.cellAt(0, 1).setFormat(content_format)

                # 初始化内容单元格光标
                self.current_ai_cursor = self.current_table.cellAt(0, 1).firstCursorPosition()
                self.current_ai_cursor.insertHtml("<b>StickMan</b><br>")
            # 插入流式内容
            if self.current_ai_cursor:
                content = content.replace('\n', '<br>')
                self.current_ai_cursor.insertHtml(content)
                self.chatHistory.ensureCursorVisible()

    def handle_error(self, error_msg):
        self._append_message("System", f"Error: {error_msg}")

    def stop_ai_response(self):
        """停止AI生成"""
        if self.ai and self.is_ai_responding:
            self.ai.stop()
            cursor = self.chatHistory.textCursor()
            cursor.insertHtml("<br>")
            self.is_ai_responding = False
            self.current_ai_cursor = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatWindow()
    window.show()
    sys.exit(app.exec())
