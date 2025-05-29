import os
import json
import pathlib
import re
from openai import OpenAI
from PyQt6.QtCore import QThread, pyqtSignal
from .test_api import MockAIResponse
from .prompt import PROMPT_STYLE, PROMPT_CMD
from .file_processor import FileProcessor

TEST_MODE = False# 是否处于测试状态
SHOW_CMD = False # 是否显示json指令
HISTORY_FILE = "chat_history.json" # 聊天历史文件
# 获取当前脚本文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
# 构造目标 JSON 文件路径 (上一级文件夹中的 data/config.json)
json_file_path = os.path.join(current_dir, '..', 'data', 'settings.json')

token = "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"  # API 密钥
# 打开并读取 JSON 文件
try:
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)  # 加载 JSON 数据
        print("成功读取 JSON 文件中的数据：")
        if len(data["api_key"]) != 0:
            token = data["api_key"]
        else:
            token = "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"  # API 密钥
        # print(data)
except FileNotFoundError:
    print(f"文件未找到：{json_file_path}")
except json.JSONDecodeError:
    print(f"JSON 文件解析错误：{json_file_path}")

# 配置信息
endpoint = "https://models.inference.ai.azure.com"
model_name = "gpt-4o-mini"
TEMP_RESPONSE = 0.7 # 正常回复的温度
TEMP_FEEDBACK = 0.5 # 生成执行任务反馈的温度
PROMPT = PROMPT_STYLE + PROMPT_CMD

client = OpenAI(
    base_url=endpoint,
    api_key=token,
)

conversation_history = [{
    "role": "system",
    "content": json.dumps({
        "type": "prompt",
        "content": PROMPT
    }, ensure_ascii=False)}]

if os.path.exists(HISTORY_FILE):
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            saved_history = [
                msg for msg in json.load(f)
            ]
            conversation_history.extend(saved_history)
    except:
        pass
else:
    pass


def save_history():
    try:
        filtered_history = []
        for msg in conversation_history:
            if msg["role"] == "system":
                try:
                    content_json = json.loads(msg["content"])
                    if content_json.get("type") == "prompt":
                        continue  # 跳过初始PROMPT
                except:
                    pass  # 非JSON内容或其他异常则保留
            filtered_history.append(msg)

        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(filtered_history, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"failed to save chat history: {e}")

def clear_history():
    global conversation_history
    conversation_history = [{
        "role": "system",
        "content": json.dumps({
            "type": "prompt",
            "content": PROMPT
        }, ensure_ascii=False)}]
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"failed to clear chat history: {e}")


class AIChat(QThread):
    response_received = pyqtSignal(str, bool)  # (内容, 是否完成)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_input):
        super().__init__()
        self.user_input = user_input
        self._stop_flag = False

    def run(self):
        try:
            # 添加用户消息到历史
            conversation_history.append({"role": "user", "content": self.user_input})

            # 流式请求
            if TEST_MODE:
                # 使用模拟客户端
                response_stream = MockAIResponse(self.user_input).generate_stream()
            else:
                response_stream = client.chat.completions.create(
                    messages=conversation_history,
                    model=model_name,
                    stream=True,
                    # temperature=TEMP_RESPONSE,
                )

            buffer = []
            pending_text = []  # 用于保存JSON前的文本
            is_json_response = False
            json_braces = 0
            for chunk in response_stream:
                if self._stop_flag:  # 检查停止标志
                    break
                if chunk.choices and (content := chunk.choices[0].delta.content):
                    # 收集普通文本或检测JSON开始
                    if not is_json_response:
                        # 检测到JSON开始符时切换模式
                        if '{' in content:
                            split_idx = content.index('{')
                            # 保存前面的普通文本
                            if split_idx > 0:
                                pending_text.append(content[:split_idx])
                                self.response_received.emit(content[:split_idx], False)
                            # 进入JSON处理模式
                            is_json_response = True
                            json_braces = 1
                            buffer = [content[split_idx:]]
                            continue
                        else:
                            self.response_received.emit(content, False)
                            pending_text.append(content)
                    # 处理JSON内容
                    else:
                        buffer.append(content)
                        json_braces += content.count('{') - content.count('}')

                        # 当检测到完整JSON时处理
                        if json_braces == 0:
                            full_json = ''.join(buffer)
                            if self._is_valid_command(full_json):  # 新增校验
                                # 执行命令并生成反馈
                                feedback, _ = self._execute_command(full_json)
                                natural_feedback = self._generate_feedback(feedback)
                                # 合并待处理文本和自然反馈
                                if SHOW_CMD:
                                    self.response_received.emit(f"{full_json}\n", False)
                                    full_message = ''.join(pending_text) + f"{full_json}\n" + natural_feedback
                                else:
                                    full_message = ''.join(pending_text) + natural_feedback
                                # 更新聊天记录
                                conversation_history.append({
                                    "role": "assistant",
                                    "content": full_message
                                })
                                save_history()
                                # 发送最终反馈并清空缓存
                                self.response_received.emit(natural_feedback, False)
                                self.response_received.emit("", True)
                            else:
                                # 无效指令作为普通文本处理
                                pending_text.append(full_json)
                                self.response_received.emit(full_json, False)

                            # 重置状态
                            pending_text = []
                            is_json_response = False

            # 处理中途停止的情况
            if self._stop_flag:
                self.response_received.emit("", True)
                text = ""
                for msg in pending_text:
                    text += msg
                conversation_history.append({
                    "role": "assistant",
                    "content": text
                })
                save_history()
                return

            # 处理纯文本响应（无JSON）
            if not is_json_response and pending_text:
                full_message = ''.join(pending_text)
                self.response_received.emit("", True)
                conversation_history.append({
                    "role": "assistant",
                    "content": full_message
                })
                save_history()

        except Exception as e:
            self.error_occurred.emit(str(e))

    def _is_valid_command(self, json_str):
        """验证是否为有效指令"""
        try:
            command = json.loads(json_str)
            if isinstance(command, dict):
                allowed_actions = {'open_browser', 'open_file', 'open_folder',
                                 'find_file', 'read_file'}
                return command.get('action') in allowed_actions
            return False
        except json.JSONDecodeError:
            return False

    def _execute_command(self, full_response):
        """解析并执行JSON指令, 返回 (反馈信息, 需要清除的行数)"""
        try:
            json_matches = re.findall(r'\{.*?\}(?=\s*(?:\{|\Z))', full_response, re.DOTALL)
            if not json_matches:
                return "No valid JSON command found in response", 0
            # 取最后一个有效JSON（适应多JSON指令情况）
            last_json = json_matches[-1]
            command = json.loads(last_json)

            action = command.get("action")
            path = command.get("path")
            url = command.get("url")

            if action == "open_file":
                if os.path.exists(path):
                    os.startfile(path)
                    return "file opened successfully", 1
                return f"failed to find file: {path}", 1

            elif action == "open_browser":
                if url:
                    import webbrowser
                    webbrowser.open(url)
                    return f"browser opened successfully: {url}", 1
                return "lack of valid url", 1

            elif action == "open_folder":
                if os.path.exists(path):
                    os.startfile(path)
                    return "folder opened successfully", 1
                return f"failed to find folder: {path}", 1


            elif action == "find_file":
                filename = command.get("filename", "")
                scope = command.get("search_scope", "").strip()
                # 确保文件路径存在且合法
                if scope:
                    if not os.path.exists(scope):
                        return f"Path does not exist: {scope}", 1
                    if not os.path.isdir(scope):
                        return f"Path invalid: {scope}", 1
                # 确定搜索根目录
                if scope and os.path.exists(scope):
                    search_roots = [pathlib.Path(scope)]
                else:
                    # 默认搜索所有可用磁盘
                    search_roots = [pathlib.Path(d) for d in self._get_system_drives()]
                # 执行搜索
                found_files = []
                for root in search_roots:
                    if len(found_files) >= 5: break
                    found_files.extend(self._find_files(root, filename))

                result = "Found files:\n" + "\n".join(str(p) for p in found_files[:5])
                return result if found_files else "No matching files found", 1

            elif action == "read_file":
                path = command.get("path")
                if not os.path.exists(path):
                    return f"File not found: {path}", 1

                # 调用文件处理器
                print(f"[sys] Processing file: {path}")
                file_data = FileProcessor.process_file(path)
                print(f"[sys] File processed: {file_data}")

                # 处理不同状态
                if file_data['status'] == 'error':
                    return f"File error: {file_data['error']}", 1

                # 获取原始内容
                raw_content = file_data['content']
                print(f"[sys] content: {raw_content}")

                # 更新对话历史
                conversation_history.append({
                    "role": "system",
                    "content": json.dumps({
                        "type": "file_content",
                        "path": os.path.abspath(path),
                        "content": raw_content
                    }, ensure_ascii=False)
                })

                return f"file content: {raw_content}", 1

        except Exception as e:
                return f"failed to execute command: {str(e)}", 0  # 确保返回字符串

    def _get_system_drives(self):
        """获取系统所有可用磁盘"""
        return [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]

    def _find_files(self, root_dir, pattern):
        """带深度限制的递归搜索"""
        matches = []
        try:
            for path in root_dir.glob('**/*'):
                if pattern.lower() in path.name.lower():
                    matches.append(path)
                    if len(matches) >= 5: break
                # 限制搜索深度
                if len(path.parent.parts) - len(root_dir.parts) > 5:
                    continue
        except Exception as e:
            print(f"Search error in {root_dir}: {str(e)}")
        return matches

    def _generate_feedback(self, feedback):
        """执行指令后生成自然语言反馈"""
        # 构建临时对话
        feedback_prompt = [
            {"role": "system", "content": PROMPT},
            {"role": "system",
             "content": "Use the style specified by the prompt to convey the following system message to the user."},
            {"role": "user", "content": feedback}
        ]

        try:
            if TEST_MODE:
                # 模拟反馈生成API
                feedback_response = MockAIResponse("feedback").generate_feedback(feedback)
            else:
                feedback_response = client.chat.completions.create(
                    messages=feedback_prompt,
                    model=model_name,
                    # temperature=TEMP_FEEDBACK,
                )
            natural_feedback = feedback_response.choices[0].message.content
            return natural_feedback

        except Exception as e:
            error_msg = f"Failed to generate response：{str(e)}"
            self.response_received.emit(f"\n{error_msg}", True)

