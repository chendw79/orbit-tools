"""
Orbit Tools — AI图片处理工具集

功能：背景移除 / 图片压缩 / 格式转换
"""

import io
from typing import Optional, Dict, Any, Tuple

from PIL import Image, ImageEnhance


# ─── 背景移除 ─────────────────────────────────────

def remove_background(image_bytes: bytes) -> Optional[bytes]:
    """
    使用 rembg 移除背景
    
    Args:
        image_bytes: 原始图片字节
    
    Returns:
        处理后 PNG 图片字节
    """
    try:
        from rembg import remove
        input_img = Image.open(io.BytesIO(image_bytes))
        output = remove(input_img)
        buf = io.BytesIO()
        output.save(buf, format='PNG')
        buf.seek(0)
        return buf.getvalue()
    except ImportError:
        raise  # 让上层知道需要安装 rembg
    except Exception:
        return _simple_background_removal(image_bytes)


def _simple_background_removal(image_bytes: bytes) -> bytes:
    """降级：简单背景移除（对比度增强）"""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()


# ─── 图片压缩 ─────────────────────────────────────

def compress_image(
    image_bytes: bytes,
    quality: int = 70,
    max_width: int = 1920,
) -> bytes:
    """
    压缩图片
    
    Args:
        image_bytes: 原始图片
        quality: 压缩质量 1-100
        max_width: 最大宽度
    
    Returns:
        压缩后图片字节
    """
    img = Image.open(io.BytesIO(image_bytes))

    if img.width > max_width:
        ratio = max_width / img.width
        new_height = int(img.height * ratio)
        img = img.resize((max_width, new_height), Image.LANCZOS)

    buf = io.BytesIO()
    fmt = img.format or 'JPEG'
    if fmt.upper() == 'PNG':
        img.save(buf, format='PNG', optimize=True)
    else:
        img = img.convert('RGB')
        img.save(buf, format='JPEG', quality=quality, optimize=True)

    buf.seek(0)
    return buf.getvalue()


# ─── 格式转换 ─────────────────────────────────────

def convert_format(image_bytes: bytes, target_format: str = 'PNG') -> bytes:
    """
    图片格式转换
    
    Args:
        image_bytes: 原始图片
        target_format: 目标格式 PNG/JPEG/WEBP
    
    Returns:
        转换后图片字节
    """
    img = Image.open(io.BytesIO(image_bytes))

    if target_format.upper() == 'JPEG' and img.mode == 'RGBA':
        img = img.convert('RGB')

    buf = io.BytesIO()
    img.save(buf, format=target_format.upper())
    buf.seek(0)
    return buf.getvalue()


# ─── 图片信息 ─────────────────────────────────────

def get_image_info(image_bytes: bytes) -> Dict[str, Any]:
    """获取图片元信息"""
    img = Image.open(io.BytesIO(image_bytes))
    return {
        'format': img.format,
        'width': img.width,
        'height': img.height,
        'mode': img.mode,
        'size_bytes': len(image_bytes),
        'size_kb': round(len(image_bytes) / 1024, 1),
    }
