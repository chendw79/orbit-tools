"""
Orbit Tools — 文本智能处理工具集

功能：统计 / JSON / Base64 / Diff / 敏感词检测
"""

import re
import json
import base64
import hashlib
from typing import Dict, List, Optional, Any


def word_count(text: str) -> Dict[str, Any]:
    """文本统计信息"""
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    english_words = len(re.findall(r'[a-zA-Z]+', text))
    total_chars = len(text)
    paragraphs = len([p for p in text.split('\n') if p.strip()])
    punctuation = len(re.findall(r'[，。！？、；：""''（）【】《》—.,!?;:\'"()\[\]-]', text))
    numbers = len(re.findall(r'\d+', text))

    return {
        'chinese_chars': chinese_chars,
        'english_words': english_words,
        'total_chars': total_chars,
        'paragraphs': max(paragraphs, 1),
        'punctuation': punctuation,
        'numbers': numbers,
        'estimated_reading_time': max(1, round(total_chars / 300)),
        'text_hash': hashlib.md5(text.encode()).hexdigest()[:8],
    }


# ─── 敏感词检测 ─────────────────────────────────

_PATTERNS = [
    (r'(密码|password)\s*[=:：]\s*\S+', '凭证泄露'),
    (r'银行卡\s*\d{16,19}', '银行卡号'),
    (r'手机号\s*1[3-9]\d{9}', '手机号'),
    (r'身份证\s*\d{17}[\dXx]', '身份证号'),
]


def check_sensitive(text: str) -> Dict[str, Any]:
    """检测文本中的敏感信息"""
    findings: List[Dict[str, str]] = []
    for pattern, label in _PATTERNS:
        matches = re.findall(pattern, text)
        for m in matches:
            findings.append({
                'type': label,
                'match': (str(m)[:20] + '...') if len(str(m)) > 20 else str(m),
            })

    return {
        'has_sensitive': len(findings) > 0,
        'findings': findings,
        'safe': len(findings) == 0,
    }


# ─── 文本差异对比 ─────────────────────────────────

def text_diff(text1: str, text2: str) -> Dict[str, Any]:
    """简单的行级文本对比"""
    lines1, lines2 = text1.split('\n'), text2.split('\n')
    max_lines = max(len(lines1), len(lines2))
    same_lines = 0
    diff_lines: List[Dict[str, Any]] = []

    for i in range(max_lines):
        l1 = lines1[i] if i < len(lines1) else ''
        l2 = lines2[i] if i < len(lines2) else ''
        if l1 == l2:
            same_lines += 1
        else:
            diff_lines.append({
                'line': i + 1,
                'before': (l1[:100] + '...') if len(l1) > 100 else l1,
                'after': (l2[:100] + '...') if len(l2) > 100 else l2,
            })

    return {
        'total_lines': max_lines,
        'same_lines': same_lines,
        'changed_lines': len(diff_lines),
        'added_lines': max(0, len(lines2) - len(lines1)),
        'removed_lines': max(0, len(lines1) - len(lines2)),
        'similarity': round(same_lines / max(max_lines, 1) * 100, 1),
        'changes': diff_lines[:20],
    }


# ─── JSON 格式化 ─────────────────────────────────

def format_json(text: str) -> Dict[str, Any]:
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


# ─── Base64 ──────────────────────────────────────

def base64_encode(text: str) -> Dict[str, Any]:
    """Base64 编码"""
    encoded = base64.b64encode(text.encode()).decode()
    return {'success': True, 'result': encoded, 'type': 'encode'}


def base64_decode(text: str) -> Dict[str, Any]:
    """Base64 解码"""
    try:
        decoded = base64.b64decode(text.encode()).decode()
        return {'success': True, 'result': decoded, 'type': 'decode'}
    except Exception as e:
        return {'success': False, 'error': f'无效的 Base64 编码: {str(e)}', 'type': 'decode'}
