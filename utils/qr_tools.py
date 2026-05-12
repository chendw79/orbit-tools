"""
Orbit Tools — 二维码/条形码工具集

功能：二维码生成 / Wi-Fi / 电子名片
"""

import io
import base64
from typing import Dict, Any, Optional

_QR_AVAILABLE: bool = False
try:
    import qrcode
    _QR_AVAILABLE = True
except ImportError:
    pass


def generate_qr(
    data: str,
    size: int = 10,
    box_size: int = 10,
    border: int = 4,
    fill_color: str = '#000000',
    back_color: str = '#ffffff',
) -> Dict[str, Any]:
    """
    生成二维码
    
    Args:
        data: 编码内容
        size: 二维码版本 (1-40)
        box_size: 每个点的大小
        border: 边框宽度
        fill_color: 前景色
        back_color: 背景色
    """
    if not _QR_AVAILABLE:
        return {'success': False, 'error': '需要安装 qrcode 库: pip install qrcode[pil]'}

    try:
        import qrcode.constants
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
        return {'success': False, 'error': f'二维码生成失败: {str(e)}'}


def generate_wifi_qr(
    ssid: str,
    password: str,
    encryption: str = 'WPA',
    hidden: bool = False,
) -> Dict[str, Any]:
    """生成 Wi-Fi 二维码"""
    wifi_str = f'WIFI:S:{ssid};T:{encryption};P:{password};H:{str(hidden).lower()};;'
    return generate_qr(wifi_str, size=10)


def generate_vcard_qr(
    name: str,
    phone: str = '',
    email: str = '',
    org: str = '',
    title: str = '',
    url: str = '',
    address: str = '',
) -> Dict[str, Any]:
    """生成电子名片 (VCard) 二维码"""
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


def _detect_data_type(data: str) -> Dict[str, str]:
    """检测数据类型"""
    if data.startswith('http://') or data.startswith('https://'):
        return {'type': 'URL', 'preview': data[:50]}
    if data.startswith('WIFI:'):
        return {'type': 'Wi-Fi', 'preview': 'Wi-Fi 网络配置'}
    if data.startswith('BEGIN:VCARD'):
        name = ''
        for line in data.split('\n'):
            if line.startswith('FN:'):
                name = line[3:]
                break
        return {'type': '名片', 'preview': name or '电子名片'}
    if data.startswith('mailto:'):
        return {'type': 'Email', 'preview': data[7:50]}
    if data.startswith('tel:'):
        return {'type': '电话', 'preview': data[4:50]}
    return {'type': '文本', 'preview': data[:50]}
