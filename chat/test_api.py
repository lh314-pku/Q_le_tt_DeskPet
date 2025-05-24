import time
from types import SimpleNamespace


class MockAIResponse:
    def __init__(self, mode):
        self.mode = mode

    def _create_chunk(self, content):
        """创建符合OpenAI响应结构的对象"""
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    delta=SimpleNamespace(
                        content=content
                    )
                )
            ]
        )

    def generate_stream(self):
        # markdown文本与非指令json
        if self.mode == "0":
            chunks = [
                'This is a ** Markdown ** message!\n',
                '```json\n',
                '{\n"name": "Alice",\n',
                '"hobbies": ["reading", "traveling", "gaming"]\n}',
                '```',
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 长文本流式输出
        if self.mode == "1":
            text = """在软件开发领域，流式输出测试是非常重要的环节。通过分块传输数据，我们可以：||
1. 减少用户等待的焦虑感||
2. 实现更实时的交互体验||
3. 降低服务器内存压力||
4. 支持超长内容的传输||
现在让我们详细说明：流式传输的核心原理是将大数据分割成多个小块（chunks），通过事件循环机制逐步发送。||这种技术广泛应用于视频直播、实时聊天等场景。||在AI对话系统中，它能有效提升响应感知速度，即使后台仍在生成后续内容，用户也能立即看到部分结果。||"""
            for p in text.split("||"):
                yield self._create_chunk(p)
                time.sleep(0.1)

        # 打开网页
        if self.mode == "2":
            chunks = [
                '{\n  "action": "open_browser",',
                '\n  "url": "https://www.bing.com"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 打开文件
        if self.mode == "3":
            chunks = [
                '{\n  "action": "open_file",',
                '\n  "path": "D:/Files/Project/API call/test files/test_txt.txt"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 查找文件
        if self.mode == "4.1":
            chunks = [
                '{\n  "action": "find_file",',
                '\n  "filename": "test_file_114514",',
                '\n  "search_scope": "D:/Files/Project"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 查找文件，但路径写错了
        if self.mode == "4.2":
            chunks = [
                '{\n  "action": "find_file",',
                '\n  "filename": "test_file_114514",',
                '\n  "search_scope": "D:/Filess/Project"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 读取文件
        if self.mode == "5.1":
            chunks = [
                '{\n  "action": "read_file",',
                '\n  "path": "D:/Files/Project/API call/test files/test_txt.txt"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 读取pdf
        if self.mode == "5.2":
            chunks = [
                '{\n  "action": "read_file",',
                '\n  "path": "D:/Files/Project/API call/test files/test_pdf.pdf"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 读取word
        if self.mode == "5.3":
            chunks = [
                '{\n  "action": "read_file",',
                '\n  "path": "D:/Files/Project/API call/test files/test_doc.docx"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 文本+JSON混合
        if self.mode == "6.1":
            chunks = [
                "系统正在处理您的请求，请稍候...\n",
                '{\n  "action": "open_file",',
                '\n  "path": "D:/Files/Project/API call/test files/test_txt.txt"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

        # 多个JSON指令
        if self.mode == "6.2":
            chunks = [
                '{\n  "action": "open_file",',
                '\n  "path": "D:/Files/Project/API call/test files/test_txt.txt"\n}',
                '{\n  "action": "open_file",',
                '\n  "path": "D:/Files/Project/API call/test files/test_pdf.pdf"\n}'
            ]
            for chunk in chunks:
                yield self._create_chunk(chunk)
                time.sleep(0.1)

    def generate_feedback(self, feedback):
        """直接返回结构化的反馈"""
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=feedback
                    )
                )
            ]
        )