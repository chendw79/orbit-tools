"""
Orbit Tools — AI 办公工具箱 v0.2.0

更新: HTML幻灯片预览 + 8种模板 + 图片拖拽
"""

import os, sys, io, json, uuid, base64

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, send_file, redirect, Response

from utils.ppt_generator import PPTGenerator, TEMPLATES
from utils.image_tools import (remove_background, compress_image,
                               convert_format, get_image_info)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['SECRET_KEY'] = os.urandom(24).hex()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(UPLOAD_DIR, exist_ok=True)

ppt_gen = PPTGenerator()


@app.route('/')
def index():
    return render_template('index.html')


# ─── AI PPT — 全功能重写 ────────────────────────

@app.route('/ppt')
def ppt_page():
    return render_template('ppt_v2.html', templates=TEMPLATES)


@app.route('/api/ppt/generate', methods=['POST'])
def api_ppt_generate():
    """生成PPT → 返回HTML预览 + pptx下载链接"""
    data = request.get_json()
    topic = data.get('topic', '')
    pages = int(data.get('pages', 5))
    template = data.get('template', 'business')
    
    if not topic:
        return jsonify({'success': False, 'error': '请输入主题'})
    
    try:
        result = ppt_gen.render_html_preview(topic, pages, template)
        
        # 保存pptx
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


# ─── 图片处理 ─────────────────────────────────────

@app.route('/image')
def image_page():
    return render_template('image_v2.html')


@app.route('/api/image/info', methods=['POST'])
def api_image_info():
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    file = request.files['image']
    data = file.read()
    info = get_image_info(data)
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
        
        # 保存
        filename = f"nobg_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(result)
        
        # base64预览
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
        'version': '0.2.0', 
        'templates': len(TEMPLATES),
        'tools': ['PPT生成(8模板+预览)', '背景移除', '图片压缩', '格式转换'],
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8767))
    print(f'🚀 Orbit Tools v0.2.0')
    print(f'   Templates: {len(TEMPLATES)} styles')
    print(f'   PPT: HTML preview + PPTX download')
    print(f'   Image: remove-bg / compress / convert')
    print(f'   http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
