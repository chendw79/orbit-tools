"""
Orbit Tools — 色彩工具集

功能：
- 图片主色调提取
- 调色板生成
- 色彩格式转换 (HEX/RGB/HSL)
- 渐变色生成
"""

import io
import re
import colorsys
import random
import base64
from typing import List, Tuple, Optional

from PIL import Image


# ─── 色彩格式转换 ─────────────────────────────────

def hex_to_rgb(hex_color: str) -> dict:
    """HEX → RGB"""
    hex_color = hex_color.lstrip('#')
    if len(hex_color) == 3:
        hex_color = ''.join(c * 2 for c in hex_color)
    try:
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        return {'success': True, 'r': r, 'g': g, 'b': b, 'hex': f'#{hex_color}'}
    except (ValueError, IndexError):
        return {'success': False, 'error': '无效的十六进制颜色'}


def rgb_to_hex(r: int, g: int, b: int) -> dict:
    """RGB → HEX"""
    r, g, b = max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))
    hex_color = f'#{r:02x}{g:02x}{b:02x}'
    # HSL
    h, s, l = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return {
        'success': True,
        'hex': hex_color,
        'r': r, 'g': g, 'b': b,
        'h': round(h * 360, 1),
        's': round(s * 100, 1),
        'l': round(l * 100, 1),
    }


def hex_to_hsl(hex_color: str) -> dict:
    """HEX → HSL"""
    rgb = hex_to_rgb(hex_color)
    if not rgb['success']:
        return rgb
    return rgb_to_hsl(rgb['r'], rgb['g'], rgb['b'])


def rgb_to_hsl(r: int, g: int, b: int) -> dict:
    """RGB → HSL"""
    return rgb_to_hex(r, g, b)


# ─── 图片主色调提取 ─────────────────────────────

def extract_colors(image_bytes: bytes, num_colors: int = 5) -> dict:
    """提取图片主色调"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        # 缩小图片加速
        if img.width > 200 or img.height > 200:
            ratio = min(200 / img.width, 200 / img.height)
            img = img.resize((int(img.width * ratio), int(img.height * ratio)), Image.LANCZOS)
        
        # 转换为RGB
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        pixels = list(img.getdata())
        
        # 简单颜色聚类（用平均分桶）
        buckets = {}
        for r, g, b in pixels:
            # 量化到16x16x16
            key = (r // 16, g // 16, b // 16)
            buckets[key] = buckets.get(key, 0) + 1
        
        # 按出现频率排序
        sorted_buckets = sorted(buckets.items(), key=lambda x: -x[1])
        
        colors = []
        for (br, bg, bb), count in sorted_buckets[:num_colors]:
            # 取桶中心颜色
            cr, cg, cb = br * 16 + 8, bg * 16 + 8, bb * 16 + 8
            ratio = round(count / len(pixels) * 100, 1)
            colors.append({
                'rgb': [cr, cg, cb],
                'hex': f'#{cr:02x}{cg:02x}{cb:02x}',
                'ratio': ratio,
            })
        
        return {
            'success': True,
            'colors': colors,
            'total_pixels': len(pixels),
            'dominant': colors[0] if colors else None,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


# ─── 调色板生成器 ───────────────────────────────

def generate_palette(base_color: str, scheme: str = 'monochromatic', count: int = 5) -> dict:
    """生成调色板"""
    rgb = hex_to_rgb(base_color)
    if not rgb['success']:
        return rgb
    
    r, g, b = rgb['r'], rgb['g'], rgb['b']
    h, s, l = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    h *= 360
    
    if scheme == 'monochromatic':
        # 单色：固定色相，变化亮度
        colors = []
        for i in range(count):
            li = 20 + (i * 60 / max(count - 1, 1))
            li = min(li, 90)
            rr, rg, rb = colorsys.hls_to_rgb(h / 360, li / 100, s)
            clr = rgb_to_hex(int(rr * 255), int(rg * 255), int(rb * 255))
            colors.append(clr)
    
    elif scheme == 'complementary':
        # 互补色
        colors = [
            rgb_to_hex(r, g, b),
            rgb_to_hex(int(r * 0.7), int(g * 0.7), int(b * 0.7)),
            rgb_to_hex(int(r * 0.5), int(g * 0.5), int(b * 0.5)),
        ]
        # 互补色
        h2 = (h + 180) % 360
        r2, g2, b2 = [int(x * 255) for x in colorsys.hls_to_rgb(h2 / 360, l / 100, s)]
        colors.append(rgb_to_hex(r2, g2, b2))
        # 互补色变体
        r3, g3, b3 = [int(x * 255) for x in colorsys.hls_to_rgb(h2 / 360, min(l / 100 + 0.2, 0.9), s)]
        colors.append(rgb_to_hex(r3, g3, b3))
    
    elif scheme == 'triadic':
        # 三等分
        colors = []
        for i in range(3):
            hi = (h + 120 * i) % 360
            rr, rg, rb = colorsys.hls_to_rgb(hi / 360, l / 100, s)
            colors.append(rgb_to_hex(int(rr * 255), int(rg * 255), int(rb * 255)))
        # 两个变体
        for i in range(2):
            hi = (h + 120 * i + 60) % 360
            rr, rg, rb = colorsys.hls_to_rgb(hi / 360, min(l / 100 + 0.15, 0.85), s * 0.8)
            colors.append(rgb_to_hex(int(rr * 255), int(rg * 255), int(rb * 255)))
    
    elif scheme == 'analogous':
        # 类似色
        colors = []
        for i in range(count):
            hi = (h - 40 + i * 80 / max(count - 1, 1)) % 360
            li = max(25, min(80, l + (i - count // 2) * 8))
            rr, rg, rb = colorsys.hls_to_rgb(hi / 360, li / 100, s)
            colors.append(rgb_to_hex(int(rr * 255), int(rg * 255), int(rb * 255)))
    
    else:
        # 默认单色
        return generate_palette(base_color, 'monochromatic', count)
    
    return {
        'success': True,
        'scheme': scheme,
        'colors': colors,
        'base_color': base_color,
        'count': len(colors),
    }


# ─── 渐变生成器 ─────────────────────────────────

GRADIENT_SCHEMES = [
    {'name': '日落', 'start': '#FF6B35', 'end': '#F7C59F'},
    {'name': '海洋', 'start': '#0077B6', 'end': '#90E0EF'},
    {'name': '森林', 'start': '#2D6A4F', 'end': '#95D5B2'},
    {'name': '极光', 'start': '#7400B8', 'end': '#80FFDB'},
    {'name': '火焰', 'start': '#FF0000', 'end': '#FFD700'},
    {'name': '薰衣草', 'start': '#7B2D8E', 'end': '#E0AAFF'},
    {'name': '草莓', 'start': '#FF006E', 'end': '#FFBE0B'},
    {'name': '深空', 'start': '#0B132B', 'end': '#1C2541'},
    {'name': '沙漠', 'start': '#D4A373', 'end': '#FAEDCD'},
    {'name': '霓虹', 'start': '#00F5D4', 'end': '#00BBF9'},
]


def list_gradients() -> list:
    """列出所有渐变色方案"""
    return GRADIENT_SCHEMES


def generate_gradient_css(start: str, end: str, direction: str = '135deg') -> str:
    """生成 CSS 渐变色"""
    return f'linear-gradient({direction}, {start}, {end})'


if __name__ == '__main__':
    # 测试
    print(rgb_to_hex(66, 133, 244))
    print(hex_to_rgb('#4285f4'))
    
    pal = generate_palette('#4285f4', 'complementary')
    if pal['success']:
        print(f"调色板 ({pal['scheme']}):")
        for c in pal['colors']:
            print(f"  {c['hex']}")
