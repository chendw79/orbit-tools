"""
Orbit Tools — AI 办公工具箱 v0.3.1

🛸 升级内容:
  - 结构化错误处理 (Fail Fast + 友好错误)
  - 输入验证 (validate_required / validate_file)
  - 类型安全 (type hints)
  - 代码结构优化 (显式公共接口)
"""

import os
import sys
import io
import json
import uuid
import base64
import time
from typing import Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, send_file

# 工具模块
from utils.ppt_generator import PPTGenerator, TEMPLATES
from utils.image_tools import remove_background, compress_image, convert_format, get_image_info
from utils.text_tools import word_count, check_sensitive, text_diff, format_json, base64_encode, base64_decode
from utils.code_tools import count_lines, list_templates, get_template, format_sql
from utils.qr_tools import generate_qr, generate_wifi_qr, generate_vcard_qr
from utils.color_tools import extract_colors, generate_palette, hex_to_rgb, rgb_to_hex, list_gradients

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.urandom(24).hex()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(UPLOAD_DIR, exist_ok=True)

ppt_gen = PPTGenerator()


# ─── 结构化错误响应 ─────────────────────────────

def ok(data: dict = None) -> dict:
    """统一成功响应"""
    return {'success': True, **(data or {})}


def fail(message: str, code: int = 400, details: Any = None) -> tuple:
    """统一失败响应"""
    resp = {'success': False, 'error': message}
    if details:
        resp['details'] = details
    return jsonify(resp), code


def validate_required(data: dict, fields: list) -> Optional[str]:
    """验证必填字段"""
    for field in fields:
        if field not in data or not data.get(field):
            return f'缺少必填字段: {field}'
    return None


def validate_file(request, field: str = 'image') -> Optional[bytes]:
    """验证并获取上传文件"""
    if field not in request.files:
        return None
    f = request.files[field]
    if not f or not f.filename:
        return None
    return f.read()


def save_output(data: bytes, prefix: str, ext: str = '') -> str:
    """保存输出文件并返回下载路径"""
    if not ext:
        if data[:4] == b'\x89PNG':
            ext = 'png'
        elif data[:3] == b'\xff\xd8\xff':
            ext = 'jpg'
        else:
            ext = 'bin'
    filename = f"{prefix}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(data)
    return f'/download/{filename}'


# ─── 首页 ─────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ─── 工具页面 ─────────────────────────────────────

@app.route('/ppt')
def ppt_page():
    return render_template('ppt_v2.html', templates=TEMPLATES)


@app.route('/image')
def image_page():
    return render_template('image_v2.html')


@app.route('/text')
def text_page():
    return render_template('text.html')


@app.route('/qrcode')
def qrcode_page():
    return render_template('qrcode.html')


@app.route('/color')
def color_page():
    return render_template('color.html')


@app.route('/code')
def code_page():
    return render_template('code.html')


# ═══════════════════════════════════════════════════
#  API: AI PPT 生成
# ═══════════════════════════════════════════════════

@app.route('/api/ppt/generate', methods=['POST'])
def api_ppt_generate():
    data = request.get_json(silent=True) or {}
    err = validate_required(data, ['topic'])
    if err:
        return fail(err)

    topic: str = data['topic'].strip()
    pages: int = min(max(int(data.get('pages', 5)), 3), 20)
    template: str = data.get('template', 'business')

    if template not in TEMPLATES:
        return fail(f'无效模板: {template}，可用: {", ".join(TEMPLATES.keys())}')

    try:
        result = ppt_gen.render_html_preview(topic, pages, template)
        filepath = save_output(result['pptx_bytes'], 'ppt', 'pptx')

        return jsonify(ok({
            'slides': result['slides'],
            'outline': result['outline'],
            'template_name': result['template_name'],
            'total_pages': result['total_pages'],
            'download_url': filepath,
            'size': len(result['pptx_bytes']),
        }))
    except ValueError as e:
        return fail(str(e))
    except Exception as e:
        return fail(f'PPT生成失败: {str(e)}', 500)


@app.route('/api/ppt/templates')
def api_ppt_templates():
    return jsonify(ok({'templates': {
        k: {'name': v['name'], 'desc': v['desc']}
        for k, v in TEMPLATES.items()
    }}))


# ═══════════════════════════════════════════════════
#  API: 图片处理
# ═══════════════════════════════════════════════════

@app.route('/api/image/info', methods=['POST'])
def api_image_info():
    image_data = validate_file(request)
    if not image_data:
        return fail('请上传图片')

    try:
        info = get_image_info(image_data)
        return jsonify(ok({'info': info}))
    except Exception as e:
        return fail(f'读取图片失败: {str(e)}')


@app.route('/api/image/remove-bg', methods=['POST'])
def api_remove_bg():
    image_data = validate_file(request)
    if not image_data:
        return fail('请上传图片')

    try:
        t0 = time.time()
        result = remove_background(image_data)
        elapsed = time.time() - t0

        filepath = save_output(result, 'nobg', 'png')
        preview_b64 = base64.b64encode(result).decode()

        return jsonify(ok({
            'download_url': filepath,
            'preview_data': f'data:image/png;base64,{preview_b64}',
            'size_before': len(image_data),
            'size_after': len(result),
            'time_ms': int(elapsed * 1000),
        }))
    except ImportError:
        return fail('背景移除模块未安装: pip install rembg[cpu]')
    except Exception as e:
        return fail(f'背景移除失败: {str(e)}')


@app.route('/api/image/compress', methods=['POST'])
def api_compress():
    image_data = validate_file(request)
    if not image_data:
        return fail('请上传图片')

    quality = min(max(int(request.form.get('quality', 70)), 10), 100)

    try:
        result = compress_image(image_data, quality=quality)
        ext = 'png' if image_data[:4] == b'\x89PNG' else 'jpg'
        filepath = save_output(result, 'compressed', ext)
        preview_b64 = base64.b64encode(result).decode()

        return jsonify(ok({
            'download_url': filepath,
            'preview_data': f'data:image/{ext};base64,{preview_b64}',
            'size_before': len(image_data),
            'size_after': len(result),
            'saved_percent': round((1 - len(result) / len(image_data)) * 100, 1),
        }))
    except Exception as e:
        return fail(f'压缩失败: {str(e)}')


@app.route('/api/image/convert', methods=['POST'])
def api_convert():
    image_data = validate_file(request)
    if not image_data:
        return fail('请上传图片')

    target_format = request.form.get('format', 'PNG').upper()
    if target_format not in ('PNG', 'JPEG', 'WEBP', 'GIF', 'BMP'):
        return fail(f'不支持的格式: {target_format}')

    try:
        result = convert_format(image_data, target_format)
        ext = target_format.lower()
        filepath = save_output(result, 'converted', ext)
        preview_b64 = base64.b64encode(result).decode()

        return jsonify(ok({
            'download_url': filepath,
            'preview_data': f'data:image/{ext};base64,{preview_b64}',
            'format': target_format,
        }))
    except Exception as e:
        return fail(f'转换失败: {str(e)}')


# ═══════════════════════════════════════════════════
#  API: 文本工具
# ═══════════════════════════════════════════════════

@app.route('/api/text/stats', methods=['POST'])
def api_text_stats():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    if not text:
        return fail('请输入文本')

    stats = word_count(text)
    sensitive = check_sensitive(text)
    return jsonify(ok({'stats': stats, 'sensitive': sensitive}))


@app.route('/api/text/json', methods=['POST'])
def api_text_json():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    action = data.get('action', 'format')

    if not text:
        return fail('请输入文本')

    result = format_json(text)

    if action == 'compress' and result['success']:
        try:
            parsed = json.loads(text)
            compressed = json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))
            result['formatted'] = compressed
        except Exception:
            pass

    if result['success']:
        return jsonify(ok(result))
    return jsonify(result), 400


@app.route('/api/text/base64', methods=['POST'])
def api_text_base64():
    data = request.get_json(silent=True) or {}
    text = data.get('text', '')
    action = data.get('action', 'encode')

    if not text:
        return fail('请输入文本')

    if action == 'encode':
        return jsonify(ok(base64_encode(text)))
    else:
        result = base64_decode(text)
        if result['success']:
            return jsonify(ok(result))
        return jsonify(result), 400


@app.route('/api/text/diff', methods=['POST'])
def api_text_diff():
    data = request.get_json(silent=True) or {}
    text1 = data.get('text1', '')
    text2 = data.get('text2', '')

    if not text1 or not text2:
        return fail('请输入两段待对比文本')

    result = text_diff(text1, text2)
    return jsonify(ok(result))


# ═══════════════════════════════════════════════════
#  API: 二维码
# ═══════════════════════════════════════════════════

@app.route('/api/qr/generate', methods=['POST'])
def api_qr_generate():
    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'text')

    fg = data.get('fg_color', '#000000')
    bg = data.get('bg_color', '#ffffff')

    try:
        if mode == 'text':
            qr_data = data.get('data', '')
            if not qr_data:
                return fail('请输入内容')
            result = generate_qr(qr_data, fill_color=fg, back_color=bg)

        elif mode == 'wifi':
            ssid = data.get('ssid', '')
            if not ssid:
                return fail('请输入Wi-Fi名称')
            result = generate_wifi_qr(
                ssid, data.get('password', ''),
                data.get('encryption', 'WPA'),
                data.get('hidden', False)
            )

        elif mode == 'vcard':
            if not data.get('name'):
                return fail('请输入姓名')
            result = generate_vcard_qr(
                name=data['name'],
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                org=data.get('org', ''),
            )
        else:
            return fail(f'无效模式: {mode}')
    except Exception as e:
        return fail(f'二维码生成失败: {str(e)}')

    if result['success']:
        return jsonify(ok(result))
    return jsonify(result), 500


# ═══════════════════════════════════════════════════
#  API: 色彩工具
# ═══════════════════════════════════════════════════

@app.route('/api/color/palette', methods=['POST'])
def api_color_palette():
    data = request.get_json(silent=True) or {}
    color = data.get('color', '#4285f4')
    scheme = data.get('scheme', 'monochromatic')

    valid_schemes = ('monochromatic', 'complementary', 'triadic', 'analogous')
    if scheme not in valid_schemes:
        return fail(f'无效方案: {scheme}，可用: {", ".join(valid_schemes)}')

    result = generate_palette(color, scheme)
    return jsonify(result)


@app.route('/api/color/extract', methods=['POST'])
def api_color_extract():
    image_data = validate_file(request)
    if not image_data:
        return fail('请上传图片')

    try:
        result = extract_colors(image_data)
        return jsonify(result)
    except Exception as e:
        return fail(f'取色失败: {str(e)}')


@app.route('/api/color/gradients')
def api_color_gradients():
    gradients = list_gradients()
    return jsonify(ok({'gradients': gradients}))


@app.route('/api/color/convert', methods=['POST'])
def api_color_convert():
    data = request.get_json(silent=True) or {}
    color_input = data.get('color', '').strip()

    if not color_input:
        return fail('请输入颜色值')

    import re
    if color_input.startswith('#'):
        result = hex_to_rgb(color_input)
        if not result['success']:
            return fail(result['error'])
        return jsonify(ok(rgb_to_hex(result['r'], result['g'], result['b'])))

    rgb_match = re.search(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_input)
    if rgb_match:
        r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
        if not (0 <= r <= 255 and 0 <= g <= 255 and 0 <= b <= 255):
            return fail('RGB值必须在0-255之间')
        return jsonify(ok(rgb_to_hex(r, g, b)))

    return fail('无法解析颜色格式，请使用 #HEX 或 rgb(r,g,b)')


# ═══════════════════════════════════════════════════
#  API: 代码工具
# ═══════════════════════════════════════════════════

@app.route('/api/code/count', methods=['POST'])
def api_code_count():
    data = request.get_json(silent=True) or {}
    code = data.get('code', '')
    if not code:
        return fail('请输入代码')

    language = data.get('language', 'python')
    counts = count_lines(code, language)
    return jsonify(ok({'counts': counts}))


@app.route('/api/code/templates')
def api_code_templates():
    return jsonify(ok({'templates': list_templates()}))


@app.route('/api/code/template', methods=['POST'])
def api_code_template():
    data = request.get_json(silent=True) or {}
    template_id = data.get('template_id', '')
    if not template_id:
        return fail('请指定模板ID')

    variables = data.get('variables', {})
    result = get_template(template_id, variables)
    if result['success']:
        return jsonify(ok(result))
    return jsonify(result), 404


@app.route('/api/code/sql', methods=['POST'])
def api_code_sql():
    data = request.get_json(silent=True) or {}
    sql = data.get('sql', '')
    if not sql:
        return fail('请输入 SQL')

    result = format_sql(sql)
    return jsonify(result)


# ═══════════════════════════════════════════════════
#  API: 系统状态 & 文件下载
# ═══════════════════════════════════════════════════

@app.route('/download/<filename>')
def download(filename: str):
    filepath = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(filepath):
        return fail('文件不存在或已过期', 404)
    return send_file(filepath, as_attachment=True, download_name=filename)


@app.route('/api/status')
def api_status():
    return jsonify(ok({
        'name': 'Orbit Tools',
        'version': '0.3.1',
        'templates': len(TEMPLATES),
        'tools': [
            'PPT生成(8模板+实时预览)',
            '背景移除',
            '图片压缩/格式转换',
            '文本统计/JSON/Base64',
            '二维码生成(Wi-Fi/名片)',
            '色彩工具(调色板/取色/渐变)',
            '开发工具包(代码统计/模板/SQL)',
        ],
    }))


# ═══════════════════════════════════════════════════
#  404 全局处理
# ═══════════════════════════════════════════════════

@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': '接口不存在'}), 404


@app.errorhandler(413)
def too_large(e):
    return jsonify({'success': False, 'error': '文件过大，最大允许16MB'}), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': '服务器内部错误'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8767))
    print(f'🚀 Orbit Tools v0.3.1')
    print(f'   ├─ 📊 AI PPT     — 8模板 + HTML预览')
    print(f'   ├─ 🖼️  图片      — 移除背景/压缩/格式转换')
    print(f'   ├─ 📝 文本       — 统计/JSON/Base64/对比')
    print(f'   ├─ 🔲 二维码     — 文本/Wi-Fi/名片')
    print(f'   ├─ 🎨 色彩       — 调色板/取色/渐变')
    print(f'   └─ 🔧 代码       — 统计/模板/SQL')
    print(f'   ⚡  v0.3.1: 结构化错误处理 + 类型安全')
    print(f'   ────────────────────────────')
    print(f'   🌐 http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
