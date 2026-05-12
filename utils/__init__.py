"""
Orbit Tools — AI 办公工具箱 v0.3.1

工具模块索引
"""

from utils.ppt_generator import PPTGenerator, TEMPLATES
from utils.image_tools import remove_background, compress_image, convert_format, get_image_info
from utils.text_tools import word_count, check_sensitive, text_diff, format_json, base64_encode, base64_decode
from utils.code_tools import count_lines, list_templates, get_template, format_sql
from utils.qr_tools import generate_qr, generate_wifi_qr, generate_vcard_qr
from utils.color_tools import extract_colors, generate_palette, hex_to_rgb, rgb_to_hex, list_gradients

__all__ = [
    # PPT
    'PPTGenerator', 'TEMPLATES',
    # Image
    'remove_background', 'compress_image', 'convert_format', 'get_image_info',
    # Text
    'word_count', 'check_sensitive', 'text_diff', 'format_json', 'base64_encode', 'base64_decode',
    # Code
    'count_lines', 'list_templates', 'get_template', 'format_sql',
    # QR
    'generate_qr', 'generate_wifi_qr', 'generate_vcard_qr',
    # Color
    'extract_colors', 'generate_palette', 'hex_to_rgb', 'rgb_to_hex', 'list_gradients',
]
