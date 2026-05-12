"""
Orbit Tools — AI 办公工具箱 v0.3.0
🛸 多功能工具包：PPT生成 / 图片处理 / 文本工具 / 二维码 / 色彩工具 / 代码工具
"""

import os, sys, io, json, uuid, base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, send_file

# 工具模块
from utils.ppt_generator import PPTGenerator, TEMPLATES
from utils.image_tools import (remove_background, compress_image,
                               convert_format, get_image_info)
from utils.text_tools import (word_count, check_sensitive, text_diff,
                              format_json, base64_encode, base64_decode)
from utils.code_tools import (count_lines, list_templates, get_template,
                              format_sql)
from utils.qr_tools import (generate_qr, generate_wifi_qr, generate_vcard_qr)
from utils.color_tools import (extract_colors, generate_palette,
                               hex_to_rgb, rgb_to_hex, hex_to_hsl,
                               list_gradients, generate_gradient_css)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.urandom(24).hex()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(UPLOAD_DIR, exist_ok=True)

ppt_gen = PPTGenerator()


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
    data = request.get_json()
    topic = data.get('topic', '')
    pages = int(data.get('pages', 5))
    template = data.get('template', 'business')
    
    if not topic:
        return jsonify({'success': False, 'error': '请输入主题'})
    
    try:
        result = ppt_gen.render_html_preview(topic, pages, template)
        
        filename = f"ppt_{uuid.uuid4().hex[:8]}.pptx"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(result['pptx_bytes'])
        
        return jsonify({
            'success': True,
            'slides': result['slides'],
            'outline': result['outline'],
            'template_name': result['template_name'],
            'total_pages': result['total_pages'],
            'download_url': f'/download/{filename}',
            'size': len(result['pptx_bytes']),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ppt/templates')
def api_ppt_templates():
    return jsonify({'success': True, 'templates': {
        k: {'name': v['name'], 'desc': v['desc']}
        for k, v in TEMPLATES.items()
    }})


# ═══════════════════════════════════════════════════
#  API: 图片处理
# ═══════════════════════════════════════════════════

@app.route('/api/image/info', methods=['POST'])
def api_image_info():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    file = request.files['image']
    info = get_image_info(file.read())
    return jsonify({'success': True, 'info': info})

@app.route('/api/image/remove-bg', methods=['POST'])
def api_remove_bg():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    file = request.files['image']
    data = file.read()
    
    try:
        import time
        t0 = time.time()
        result = remove_background(data)
        elapsed = time.time() - t0
        
        filename = f"nobg_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(result)
        
        preview_b64 = base64.b64encode(result).decode()
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{filename}',
            'preview_data': f'data:image/png;base64,{preview_b64}',
            'size_before': len(data),
            'size_after': len(result),
            'time_ms': int(elapsed * 1000),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/image/compress', methods=['POST'])
def api_compress():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    file = request.files['image']
    quality = int(request.form.get('quality', 70))
    data = file.read()
    
    try:
        result = compress_image(data, quality=quality)
        ext = 'png' if data[:4] == b'\x89PNG' else 'jpg'
        filename = f"compressed_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(result)
        
        preview_b64 = base64.b64encode(result).decode()
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{filename}',
            'preview_data': f'data:image/{ext};base64,{preview_b64}',
            'size_before': len(data),
            'size_after': len(result),
            'saved_percent': round((1 - len(result)/len(data)) * 100, 1),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/image/convert', methods=['POST'])
def api_convert():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    file = request.files['image']
    target_format = request.form.get('format', 'PNG')
    data = file.read()
    
    try:
        result = convert_format(data, target_format)
        ext = target_format.lower()
        filename = f"converted_{uuid.uuid4().hex[:8]}.{ext}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(result)
        
        preview_b64 = base64.b64encode(result).decode()
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{filename}',
            'preview_data': f'data:image/{ext};base64,{preview_b64}',
            'format': target_format,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ═══════════════════════════════════════════════════
#  API: 文本工具
# ═══════════════════════════════════════════════════

@app.route('/api/text/stats', methods=['POST'])
def api_text_stats():
    data = request.get_json()
    text = data.get('text', '')
    if not text:
        return jsonify({'success': False, 'error': '请输入文本'})
    
    stats = word_count(text)
    sensitive = check_sensitive(text)
    
    return jsonify({
        'success': True,
        'stats': stats,
        'sensitive': sensitive,
    })

@app.route('/api/text/json', methods=['POST'])
def api_text_json():
    data = request.get_json()
    text = data.get('text', '')
    action = data.get('action', 'format')
    
    if not text:
        return jsonify({'success': False, 'error': '请输入文本'})
    
    result = format_json(text)
    
    if action == 'compress' and result['success']:
        try:
            parsed = json.loads(text)
            compressed = json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))
            result['formatted'] = compressed
        except Exception:
            pass
    
    return jsonify(result)

@app.route('/api/text/base64', methods=['POST'])
def api_text_base64():
    data = request.get_json()
    text = data.get('text', '')
    action = data.get('action', 'encode')
    
    if not text:
        return jsonify({'success': False, 'error': '请输入文本'})
    
    if action == 'encode':
        return jsonify(base64_encode(text))
    else:
        return jsonify(base64_decode(text))

@app.route('/api/text/diff', methods=['POST'])
def api_text_diff():
    data = request.get_json()
    text1 = data.get('text1', '')
    text2 = data.get('text2', '')
    
    result = text_diff(text1, text2)
    return jsonify({'success': True, **result})


# ═══════════════════════════════════════════════════
#  API: 二维码
# ═══════════════════════════════════════════════════

@app.route('/api/qr/generate', methods=['POST'])
def api_qr_generate():
    data = request.get_json()
    mode = data.get('mode', 'text')
    
    fg = data.get('fg_color', '#000000')
    bg = data.get('bg_color', '#ffffff')
    
    if mode == 'text':
        qr_data = data.get('data', '')
        if not qr_data:
            return jsonify({'success': False, 'error': '请输入内容'})
        result = generate_qr(qr_data, fill_color=fg, back_color=bg)
    
    elif mode == 'wifi':
        ssid = data.get('ssid', '')
        password = data.get('password', '')
        encryption = data.get('encryption', 'WPA')
        hidden = data.get('hidden', False)
        if not ssid:
            return jsonify({'success': False, 'error': '请输入Wi-Fi名称'})
        result = generate_wifi_qr(ssid, password, encryption, hidden)
    
    elif mode == 'vcard':
        result = generate_vcard_qr(
            name=data.get('name', ''),
            phone=data.get('phone', ''),
            email=data.get('email', ''),
            org=data.get('org', ''),
        )
    
    else:
        return jsonify({'success': False, 'error': '无效模式'})
    
    return jsonify(result)


# ═══════════════════════════════════════════════════
#  API: 色彩工具
# ═══════════════════════════════════════════════════

@app.route('/api/color/palette', methods=['POST'])
def api_color_palette():
    data = request.get_json()
    color = data.get('color', '#4285f4')
    scheme = data.get('scheme', 'monochromatic')
    
    result = generate_palette(color, scheme)
    return jsonify(result)

@app.route('/api/color/extract', methods=['POST'])
def api_color_extract():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    file = request.files['image']
    data = file.read()
    
    result = extract_colors(data)
    return jsonify(result)

@app.route('/api/color/gradients')
def api_color_gradients():
    gradients = list_gradients()
    return jsonify({'success': True, 'gradients': gradients})

@app.route('/api/color/convert', methods=['POST'])
def api_color_convert():
    data = request.get_json()
    color_input = data.get('color', '').strip()
    
    if color_input.startswith('#'):
        result = hex_to_rgb(color_input)
        if result['success']:
            return jsonify(rgb_to_hex(result['r'], result['g'], result['b']))
    
    elif color_input.startswith('rgb'):
        import re
        m = re.search(r'(\d+)\s*,\s*(\d+)\s*,\s*(\d+)', color_input)
        if m:
            r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
            return jsonify(rgb_to_hex(r, g, b))
    
    return jsonify({'success': False, 'error': '无法解析颜色格式，请使用 #HEX 或 rgb(r,g,b)'})


# ═══════════════════════════════════════════════════
#  API: 代码工具
# ═══════════════════════════════════════════════════

@app.route('/api/code/count', methods=['POST'])
def api_code_count():
    data = request.get_json()
    code = data.get('code', '')
    language = data.get('language', 'python')
    if not code:
        return jsonify({'success': False, 'error': '请输入代码'})
    counts = count_lines(code, language)
    return jsonify({'success': True, 'counts': counts})


@app.route('/api/code/templates')
def api_code_templates():
    return jsonify({'success': True, 'templates': list_templates()})


@app.route('/api/code/template', methods=['POST'])
def api_code_template():
    data = request.get_json()
    template_id = data.get('template_id', '')
    variables = data.get('variables', {})
    result = get_template(template_id, variables)
    return jsonify(result)


@app.route('/api/code/sql', methods=['POST'])
def api_code_sql():
    data = request.get_json()
    sql = data.get('sql', '')
    if not sql:
        return jsonify({'success': False, 'error': '请输入 SQL'})
    result = format_sql(sql)
    return jsonify(result)


# ═══════════════════════════════════════════════════
#  API: 系统状态 & 文件下载
# ═══════════════════════════════════════════════════

@app.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(UPLOAD_DIR, filename),
        as_attachment=True,
        download_name=filename,
    )

@app.route('/api/status')
def api_status():
    return jsonify({
        'success': True,
        'name': 'Orbit Tools',
        'version': '0.3.0',
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
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8767))
    print(f'🚀 Orbit Tools v0.3.0')
    print(f'   ├─ 📊 AI PPT —— 8模板 + HTML预览')
    print(f'   ├─ 🖼️  图片  —— 移除背景/压缩/格式转换')
    print(f'   ├─ 📝 文本  —— 统计/JSON/Base64/对比')
    print(f'   ├─ 🔲 二维码 —— 文本/Wi-Fi/名片')
    print(f'   ├─ 🎨 色彩  —— 调色板/取色/渐变')
    print(f'   └─ 🔧 代码  —— 统计/模板/SQL')
    print(f'   ────────────────────────────')
    print(f'   🌐 http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
