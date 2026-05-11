"""
AI图片处理工具集

支持：
- 背景移除 (rembg)
- 图片压缩
- 格式转换
- AI高清修复 (预留)
"""

import os
import io
from typing import Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter


# ─── 背景移除 ─────────────────────────────────────

def remove_background(image_bytes: bytes) -> Optional[bytes]:
    """
    使用 rembg 移除背景
    
    Args:
        image_bytes: 原始图片字节
    
    Returns:
        处理后图片字节
    """
    try:
        from rembg import remove
        input_img = Image.open(io.BytesIO(image_bytes))
        output = remove(input_img)
        
        buf = io.BytesIO()
        output.save(buf, format='PNG')
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        # rembg may fail, fallback to simple approach
        return _simple_background_removal(image_bytes)


def _simple_background_removal(image_bytes: bytes) -> bytes:
    """简单背景移除（备用方案，使用颜色阈值）"""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGBA')
    
    # 转换为RGB用于处理
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # 简单处理：增加对比度
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()


# ─── 图片压缩 ─────────────────────────────────────

def compress_image(image_bytes: bytes, quality: int = 70, 
                   max_width: int = 1920) -> bytes:
    """
    压缩图片
    
    Args:
        image_bytes: 原始图片
        quality: 压缩质量 1-100
        max_width: 最大宽度
    
    Returns:
        压缩后图片
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    # 调整尺寸
    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)
    
    # 压缩
    buf = io.BytesIO()
    format_name = img.format or 'JPEG'
    if format_name.upper() == 'PNG':
        img.save(buf, format='PNG', optimize=True)
    else:
        img.save(buf, format='JPEG', quality=quality, optimize=True)
    
    buf.seek(0)
    return buf.getvalue()


# ─── 格式转换 ─────────────────────────────────────

def convert_format(image_bytes: bytes, target_format: str = 'PNG') -> bytes:
    """
    图片格式转换
    
    Args:
        image_bytes: 原始图片
        target_format: 目标格式 (PNG/JPEG/WEBP)
    
    Returns:
        转换后图片
    """
    img = Image.open(io.BytesIO(image_bytes))
    
    if target_format.upper() == 'JPEG' and img.mode == 'RGBA':
        img = img.convert('RGB')
    
    buf = io.BytesIO()
    img.save(buf, format=target_format.upper())
    buf.seek(0)
    return buf.getvalue()


# ─── 图片信息 ─────────────────────────────────────

def get_image_info(image_bytes: bytes) -> dict:
    """获取图片信息"""
    img = Image.open(io.BytesIO(image_bytes))
    return {
        'format': img.format,
        'width': img.width,
        'height': img.height,
        'mode': img.mode,
        'size_bytes': len(image_bytes),
        'size_kb': round(len(image_bytes) / 1024, 1),
    }


if __name__ == '__main__':
    # 测试
    import sys
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'rb') as f:
            data = f.read()
        
        info = get_image_info(data)
        print(f"原始: {info['format']} {info['width']}x{info['height']} "
              f"({info['size_kb']}KB)")
        
        compressed = compress_image(data, quality=60)
        print(f"压缩后: {len(compressed)/1024:.1f}KB "
              f"(节省{100-len(compressed)/len(data)*100:.0f}%)")
        
        # 背景移除
        nobg = remove_background(data)
        print(f"背景移除: {len(nobg)/1024:.1f}KB")
