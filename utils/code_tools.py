"""
Orbit Tools — 代码工具集

功能：
- JSON 格式化/校验/压缩
- 代码统计 (lines of code)
- 代码注释提取
- 多种语言代码模板
"""

import re
import json
from typing import Optional


# ─── 代码统计 ─────────────────────────────────────

def count_lines(code: str, language: str = 'python') -> dict:
    """统计代码行数"""
    lines = code.split('\n')
    total = len(lines)
    blank = 0
    comments = 0
    code_lines = 0
    
    # 注释模式
    comment_patterns = {
        'python': (r'^\s*#', r'^\s*(""".*""")|(\'\'\'.*\'\'\')$'),
        'javascript': (r'^\s*//', r'^\s*/\*.*\*/$'),
        'java': (r'^\s*//', r'^\s*/\*.*\*/$'),
        'html': (r'^\s*<!--', r'-->'),
        'css': (r'^\s*/\*', r'\*/'),
    }
    
    single_line_cmt, multi_line_cmt = comment_patterns.get(
        language, (r'^\s*#', r'^\s*"""')
    )
    
    in_multiline = False
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            blank += 1
            continue
        
        if in_multiline:
            comments += 1
            if re.search(r'"""|\'\'\'', stripped):
                in_multiline = False
            continue
        
        if re.match(single_line_cmt, stripped):
            comments += 1
            continue
        
        if re.match(multi_line_cmt, stripped) if multi_line_cmt else False:
            comments += 1
            continue
        
        if stripped.startswith('"""') or stripped.startswith("'''"):
            comments += 1
            if not (stripped.endswith('"""') or stripped.endswith("'''")) or len(stripped) > 3:
                in_multiline = True
            continue
        
        code_lines += 1
    
    return {
        'total': total,
        'code': code_lines,
        'comments': comments,
        'blank': blank,
        'language': language,
    }


# ─── 代码模板 ─────────────────────────────────────

CODE_TEMPLATES = {
    'flask_api': {
        'name': 'Flask API 基础模板',
        'desc': '快速的 RESTful API 脚手架',
        'code': '''from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/health')
def health():
    return jsonify({"status": "ok", "service": "{{name}}"})

@app.route('/api/{{endpoint}}', methods=['POST'])
def handle_request():
    data = request.get_json()
    # TODO: implement logic
    return jsonify({"success": True, "data": data})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port={{port}}, debug=True)
'''
    },
    'python_script': {
        'name': 'Python 脚本模板',
        'desc': '标准 Python 工具脚本',
        'code': '''#!/usr/bin/env python3
"""
{{description}}

Usage:
    python {{filename}} [options]
"""

import sys
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='{{description}}')
    parser.add_argument('--input', '-i', help='输入文件')
    parser.add_argument('--output', '-o', help='输出文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    return parser.parse_args()


def main():
    args = parse_args()
    print("Starting {{name}}...")
    # TODO: implement
    print("Done.")


if __name__ == '__main__':
    main()
'''
    },
    'html_page': {
        'name': 'HTML5 页面模板',
        'desc': '现代 HTML5 页面基础结构',
        'code': '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; line-height: 1.6; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{title}}</h1>
        <div id="app">
            <!-- Content here -->
        </div>
    </div>
    <script>
        // JavaScript here
    </script>
</body>
</html>
'''
    },
    'dockerfile': {
        'name': 'Dockerfile 模板',
        'desc': 'Python 应用 Docker 化',
        'code': '''FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE {{port}}

CMD ["python", "{{entrypoint}}"]
'''
    },
}


def list_templates() -> dict:
    """列出所有代码模板"""
    return {k: {'name': v['name'], 'desc': v['desc']} for k, v in CODE_TEMPLATES.items()}


def get_template(template_id: str, variables: dict = None) -> dict:
    """获取代码模板并填充变量"""
    tmpl = CODE_TEMPLATES.get(template_id)
    if not tmpl:
        return {'success': False, 'error': f'模板 {template_id} 不存在'}
    
    code = tmpl['code']
    if variables:
        import json as _json
        for key, val in (variables or {}).items():
            code = code.replace('{{' + key + '}}', str(val))
    
    return {
        'success': True,
        'name': tmpl['name'],
        'code': code,
        'language': template_id.split('_')[0] if '_' in template_id else 'text',
    }


# ─── SQL 格式化（简单版） ─────────────────────────

def format_sql(sql: str) -> dict:
    """简单 SQL 美化"""
    keywords = r'\b(SELECT|FROM|WHERE|AND|OR|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP BY|HAVING|ORDER BY|LIMIT|INSERT INTO|VALUES|UPDATE|SET|DELETE|CREATE TABLE|ALTER TABLE|DROP TABLE|INDEX|UNION|ALL|AS|IN|NOT|NULL|IS|BETWEEN|LIKE|CASE|WHEN|THEN|ELSE|END|EXISTS|DISTINCT|COUNT|SUM|AVG|MIN|MAX)\b'
    
    formatted = sql.strip()
    # 在每个关键字前换行
    formatted = re.sub(keywords, r'\n\1', formatted, flags=re.IGNORECASE)
    # 清理多余空行
    formatted = re.sub(r'\n\s*\n', '\n', formatted)
    # 缩进
    lines = formatted.split('\n')
    indented = []
    for line in lines:
        stripped = line.strip()
        if stripped.upper() in ('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE'):
            indented.append(stripped)
        elif stripped.upper() in ('FROM', 'WHERE', 'JOIN', 'LEFT', 'RIGHT', 'INNER', 
                                   'OUTER', 'GROUP BY', 'ORDER BY', 'HAVING', 'LIMIT',
                                   'ON', 'UNION', 'VALUES', 'SET'):
            indented.append(f'  {stripped}')
        elif stripped.upper() in ('AND', 'OR'):
            indented.append(f'    {stripped}')
        else:
            indented.append(stripped if stripped.startswith(' ') else f'  {stripped}')
    
    return {
        'success': True,
        'formatted': '\n'.join(indented),
    }


if __name__ == '__main__':
    # 测试
    test_code = '''#!/usr/bin/env python3
"""Sample module"""

import os
import sys

# A comment
def hello():
    """Say hello"""
    print("Hello")

if __name__ == '__main__':
    hello()
'''
    print(count_lines(test_code, 'python'))
