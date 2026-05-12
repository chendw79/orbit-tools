"""
Orbit Tools — 二维码/条形码工具集

功能：
- 生成二维码 (QR Code)
- 生成彩色二维码
- 生成带LOGO二维码
- Wi-Fi 二维码
"""

import io
import json
import base64
from typing import Optional

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


def generate_qr(
    data: str,
    size: int = 10,
    box_size: int = 10,
    border: int = 4,
    fill_color: str = '#000000',
    back_color: str = '#ffffff',
    format: str = 'png',
) -> dict:
    """
    生成二维码
    
    Args:
        data: 编码内容
        size: 二维码版本 (1-40)
        box_size: 每个点的大小
        border: 边框宽度
        fill_color: 前景色
        back_color: 背景色
        format: 输出格式 (png/svg)
    """
    if not QR_AVAILABLE:
        return _fallback_qr(data)
    
    try:
        qr = qrcode.QRCode(
            version=size,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=box_size,
            border=border,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color=fill_color, back_color=back_color)
        
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        
        b64 = base64.b64encode(buf.getvalue()).decode()
        
        # 基本信息
        info = _detect_data_type(data)
        
        return {
            'success': True,
            'image_data': f'data:image/png;base64,{b64}',
            'size_bytes': len(buf.getvalue()),
            'data_type': info['type'],
            'data_preview': info['preview'],
            'qr_version': qr.version,
            'qr_box_count': qr.modules_count,
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}


def generate_wifi_qr(
    ssid: str,
    password: str,
    encryption: str = 'WPA',
    hidden: bool = False,
) -> dict:
    """
    生成Wi-Fi二维码
    
    Args:
        ssid: 网络名称
        password: 密码
        encryption: 加密方式 (WPA/WEP/nopass)
        hidden: 是否隐藏网络
    """
    # WIFI:S:<SSID>;T:<WPA|WEP|>;P:<PASSWORD>;H:<true|false|>;
    wifi_string = f'WIFI:S:{ssid};T:{encryption};P:{password};H:{str(hidden).lower()};;'
    return generate_qr(wifi_string, size=10)


def generate_vcard_qr(
    name: str,
    phone: str = '',
    email: str = '',
    org: str = '',
    title: str = '',
    url: str = '',
    address: str = '',
) -> dict:
    """生成电子名片(VCard)二维码"""
    lines = [
        'BEGIN:VCARD',
        'VERSION:3.0',
        f'FN:{name}',
        f'N:{name}',
    ]
    if phone:
        lines.append(f'TEL:{phone}')
    if email:
        lines.append(f'EMAIL:{email}')
    if org:
        lines.append(f'ORG:{org}')
    if title:
        lines.append(f'TITLE:{title}')
    if url:
        lines.append(f'URL:{url}')
    if address:
        lines.append(f'ADR:{address}')
    lines.append('END:VCARD')
    
    return generate_qr('\n'.join(lines), size=10)


def _detect_data_type(data: str) -> dict:
    """检测数据类型"""
    if data.startswith('http://') or data.startswith('https://'):
        return {'type': 'URL', 'preview': data[:50]}
    elif data.startswith('WIFI:'):
        return {'type': 'Wi-Fi', 'preview': 'Wi-Fi 网络配置'}
    elif data.startswith('BEGIN:VCARD'):
        return {'type': '名片', 'preview': data.split('FN:')[1].split('\n')[0] if 'FN:' in data else '电子名片'}
    elif data.startswith('mailto:'):
        return {'type': 'Email', 'preview': data[7:50]}
    elif data.startswith('tel:'):
        return {'type': '电话', 'preview': data[4:50]}
    else:
        return {'type': '文本', 'preview': data[:50]}


def _fallback_qr(data: str) -> dict:
    """降级方案：手动生成简单二维码（使用字符画）"""
    return {
        'success': False,
        'error': '需要安装 qrcode 库: pip install qrcode[pil]',
        'fallback': True,
        'data': data,
    }


if __name__ == '__main__':
    # 测试
    result = generate_qr('Hello Orbit', size=5)
    if result['success']:
        print(f"QR generated: {result['size_bytes']} bytes, type: {result['data_type']}")
