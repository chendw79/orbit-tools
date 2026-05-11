"""
Orbit Tools — AI 办公工具箱

综合平台，提供多个AI小组件：
- /ppt: AI幻灯片生成
- /image: 图片处理
- /compress: 图片压缩
- /removebg: 背景移除
"""

import os
import sys
import io
import json
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, jsonify, send_file, redirect

from utils.ppt_generator import PPTGenerator
from utils.image_tools import (remove_background, compress_image, 
                               convert_format, get_image_info)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
app.config['SECRET_KEY'] = os.urandom(24).hex()

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ─── 首页 ─────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


# ─── AI PPT ───────────────────────────────────────

@app.route('/ppt')
def ppt_page():
    return render_template('ppt.html')


@app.route('/api/ppt/generate', methods=['POST'])
def api_ppt_generate():
    """生成PPT"""
    data = request.get_json()
    topic = data.get('topic', '')
    pages = int(data.get('pages', 5))
    template = data.get('template', 'business')
    
    if not topic:
        return jsonify({'success': False, 'error': '请输入主题'})
    
    try:
        generator = PPTGenerator()
        ppt_bytes = generator.create_pptx(topic, pages, template)
        
        filename = f"ppt_{uuid.uuid4().hex[:8]}.pptx"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(ppt_bytes)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': len(ppt_bytes),
            'download_url': f'/download/{filename}',
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/ppt/preview', methods=['POST'])
def api_ppt_preview():
    """预览大纲"""
    data = request.get_json()
    topic = data.get('topic', '')
    pages = int(data.get('pages', 5))
    
    generator = PPTGenerator()
    outline = generator.generate_outline(topic, pages)
    
    return jsonify({
        'success': True,
        'outline': outline,
    })


# ─── 图片处理 ─────────────────────────────────────

@app.route('/image')
def image_page():
    return render_template('image.html')


@app.route('/api/image/info', methods=['POST'])
def api_image_info():
    """图片信息"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    
    file = request.files['image']
    data = file.read()
    info = get_image_info(data)
    
    return jsonify({'success': True, 'info': info})


@app.route('/api/image/remove-bg', methods=['POST'])
def api_remove_bg():
    """背景移除"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    
    file = request.files['image']
    data = file.read()
    
    try:
        result = remove_background(data)
        filename = f"nobg_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(result)
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{filename}',
            'size_before': len(data),
            'size_after': len(result),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/image/compress', methods=['POST'])
def api_compress():
    """图片压缩"""
    if 'image' not in request.files:
        return jsonify({'success': False, 'error': '请上传图片'})
    
    file = request.files['image']
    quality = int(request.form.get('quality', 70))
    data = file.read()
    
    try:
        result = compress_image(data, quality=quality)
        filename = f"compressed_{uuid.uuid4().hex[:8]}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        with open(filepath, 'wb') as f:
            f.write(result)
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{filename}',
            'size_before': len(data),
            'size_after': len(result),
            'saved_percent': round((1 - len(result)/len(data)) * 100, 1),
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/image/convert', methods=['POST'])
def api_convert():
    """格式转换"""
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
        
        return jsonify({
            'success': True,
            'download_url': f'/download/{filename}',
            'format': target_format,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


# ─── 文件下载 ─────────────────────────────────────

@app.route('/download/<filename>')
def download(filename):
    return send_file(
        os.path.join(UPLOAD_DIR, filename),
        as_attachment=True,
        download_name=filename,
    )


# ─── 系统状态 ─────────────────────────────────────

@app.route('/api/status')
def api_status():
    return jsonify({
        'success': True,
        'name': 'Orbit Tools',
        'version': '0.1.0',
        'tools': ['PPT生成', '背景移除', '图片压缩', '格式转换'],
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8767))
    print(f'🚀 Orbit Tools 启动: http://0.0.0.0:{port}')
    app.run(host='0.0.0.0', port=port, debug=False)
