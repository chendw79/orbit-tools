"""
Orbit Tools — 文本智能处理工具集

功能：
- AI 润色 (polish)
- AI 翻译 (translate)
- AI 摘要 (summarize)
- AI 改写 (rewrite)
- 字数统计 (word count)
- 敏感词检测 (sensitive words)
"""

import re
import json
import hashlib
from typing import Optional

# ─── 基础文本统计 ─────────────────────────────────

def word_count(text: str) -> dict:
    """文本统计信息"""
    # 中文字数
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    # 英文单词数
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    # 总字符数
    total_chars = len(text)
    # 段落数
    paragraphs = len([p for p in text.split('\n') if p.strip()])
    # 标点数
    punctuation = len(re.findall(r'[，。！？、；：""''（）【】《》—.,!?;:\'"()\[\]-]', text))
    # 数字数
    numbers = len(re.findall(r'\d+', text))
    
    return {
        'chinese_chars': chinese_chars,
        'english_words': english_words,
        'total_chars': total_chars,
        'paragraphs': max(paragraphs, 1),
        'punctuation': punctuation,
        'numbers': numbers,
        'estimated_reading_time': max(1, round(total_chars / 300)),  # 分钟（中文阅读速度）
        'text_hash': hashlib.md5(text.encode()).hexdigest()[:8],
    }


# ─── 敏感词检测 ─────────────────────────────────

# 常见敏感词（演示版）
_SENSITIVE_WORDS = [
    # 这里放一些演示用的模式
    r'(密码|password)\s*[=:：]\s*\S+',
    r'银行卡\s*\d{16,19}',
    r'手机号\s*1[3-9]\d{9}',
    r'身份证\s*\d{17}[\dXx]',
]


def check_sensitive(text: str) -> dict:
    """检测文本中的敏感信息"""
    findings = []
    for i, pattern in enumerate(_SENSITIVE_WORDS):
        matches = re.findall(pattern, text)
        for m in matches:
            findings.append({
                'pattern': pattern,
                'match': m[:20] + '...' if len(str(m)) > 20 else m,
                'type': ['凭证泄露', '银行卡号', '手机号', '身份证号'][i],
            })
    
    return {
        'has_sensitive': len(findings) > 0,
        'findings': findings,
        'safe': len(findings) == 0,
    }


# ─── 文本差异对比 ─────────────────────────────────

def text_diff(text1: str, text2: str) -> dict:
    """简单的文本对比"""
    lines1, lines2 = text1.split('\n'), text2.split('\n')
    
    same_lines = 0
    diff_lines = []
    
    max_lines = max(len(lines1), len(lines2))
    for i in range(max_lines):
        l1 = lines1[i] if i < len(lines1) else ''
        l2 = lines2[i] if i < len(lines2) else ''
        if l1 == l2:
            same_lines += 1
        else:
            diff_lines.append({
                'line': i + 1,
                'before': l1[:100] + '...' if len(l1) > 100 else l1,
                'after': l2[:100] + '...' if len(l2) > 100 else l2,
            })
    
    return {
        'total_lines': max_lines,
        'same_lines': same_lines,
        'changed_lines': len(diff_lines),
        'added_lines': max(0, len(lines2) - len(lines1)),
        'removed_lines': max(0, len(lines1) - len(lines2)),
        'similarity': round(same_lines / max(max_lines, 1) * 100, 1),
        'changes': diff_lines[:20],  # 只返回前20处
    }


# ─── 文本格式化 ─────────────────────────────────

def format_json(text: str) -> dict:
    """格式化/校验 JSON"""
    text = text.strip()
    try:
        parsed = json.loads(text)
        formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
        return {
            'success': True,
            'formatted': formatted,
            'error': None,
            'data_type': type(parsed).__name__,
            'keys': list(parsed.keys()) if isinstance(parsed, dict) else None,
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'formatted': text,
            'error': str(e),
            'error_position': e.pos,
            'error_line': e.lineno,
            'error_col': e.colno,
        }


# ─── Base64 编解码 ──────────────────────────────

import base64


def base64_encode(text: str) -> dict:
    """Base64编码"""
    encoded = base64.b64encode(text.encode()).decode()
    return {'success': True, 'result': encoded, 'type': 'encode'}


def base64_decode(text: str) -> dict:
    """Base64解码"""
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return {'success': True, 'result': decoded, 'type': 'decode'}
    except Exception as e:
        return {'success': False, 'error': str(e), 'type': 'decode'}


if __name__ == '__main__':
    # 测试
    test = "今天天气真好，我们来测试一下文本统计功能。Hello World! 12345"
    print(word_count(test))
    
    json_text = '{"name": "Orbit", "tools": ["ppt", "image"]}'
    print(format_json(json_text)['formatted'])
