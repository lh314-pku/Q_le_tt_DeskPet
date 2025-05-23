import os
import sys
import filetype
import pdfplumber
from docx import Document
from contextlib import redirect_stderr

MAX_FILE_LEN = 5000

class FileProcessor:
    @staticmethod
    def detect_file_type(path):
        """Enhanced file type detection"""
        kind = filetype.guess(path)
        if kind:
            return kind.extension.lower()
        return os.path.splitext(path)[1].lower()[1:] or 'unknown'

    @staticmethod
    def process_file(path):
        """Process file and return raw content with status"""
        try:
            file_type = FileProcessor.detect_file_type(path)

            processors = {
                'pdf': FileProcessor._process_pdf,
                'txt': FileProcessor._process_text,
                'docx': FileProcessor._process_docx
            }

            if processor := processors.get(file_type):
                success, content = processor(path)
                return {
                    'status': 'success' if success else 'partial',
                    'file_type': file_type,
                    'content': content
                }

            return {
                'status': 'error',
                'error': f'Unsupported file type: {file_type}'
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': f'Processing failed: {str(e)}'
            }

    @staticmethod
    def _process_pdf(path):
        try:
            text = []
            with open(os.devnull, 'w') as devnull:
                with redirect_stderr(devnull):  # 临时屏蔽标准错误输出
                    with pdfplumber.open(path) as pdf:
                        for page in pdf.pages:
                            text.append(page.extract_text() or "")
            return True, "\n".join(text)[:MAX_FILE_LEN]
        except Exception as e:
            return False, f"Failed to extract PDF content: {str(e)}"

    @staticmethod
    def _process_text(path):
        encodings = ['utf-8', 'gbk', 'gb2312', 'big5']
        for encoding in encodings:
            try:
                with open(path, 'r', encoding=encoding) as f:
                    return True, f.read(MAX_FILE_LEN)
            except UnicodeDecodeError:
                continue
        return False, "Failed to decode text content"

    @staticmethod
    def _process_docx(path):
        """处理Word文档"""
        try:
            doc = Document(path)
            return True, "\n".join([p.text for p in doc.paragraphs])[:MAX_FILE_LEN]
        except Exception as e:
            return False, f"Failed to read DOCX: {str(e)}"