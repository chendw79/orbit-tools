"""
AI PPT 生成器核心模块

支持：
- 输入主题 → AI生成大纲 → 生成pptx下载
- 单页/多页模板
- 中英文内容
"""

import os
import json
import re
from typing import List, Dict, Optional
from datetime import datetime

# python-pptx
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE


# ─── 模板定义 ─────────────────────────────────────

TEMPLATES = {
    'business': {
        'name': '商务蓝',
        'primary_color': (41, 98, 255),
        'bg_color': (245, 247, 250),
        'accent_color': (0, 180, 216),
        'font': '微软雅黑',
    },
    'tech': {
        'name': '科技暗',
        'primary_color': (0, 230, 200),
        'bg_color': (15, 15, 35),
        'accent_color': (100, 100, 255),
        'font': '微软雅黑',
    },
    'minimal': {
        'name': '简约白',
        'primary_color': (50, 50, 50),
        'bg_color': (255, 255, 255),
        'accent_color': (200, 200, 200),
        'font': '微软雅黑',
    },
    'nature': {
        'name': '自然绿',
        'primary_color': (34, 139, 34),
        'bg_color': (240, 250, 240),
        'accent_color': (144, 238, 144),
        'font': '微软雅黑',
    },
}


class PPTGenerator:
    """AI PPT生成器"""
    
    def __init__(self):
        self.templates = TEMPLATES
    
    def generate_outline(self, topic: str, pages: int = 5) -> List[Dict]:
        """
        生成PPT大纲
        
        实际生产环境调用LLM API，这里先使用规则生成
        """
        # 尝试调用AI生成大纲（使用Orbit的API能力）
        outline = self._call_llm_for_outline(topic, pages)
        if outline:
            return outline
        
        # 降级：规则生成
        return self._rule_based_outline(topic, pages)
    
    def _call_llm_for_outline(self, topic: str, pages: int) -> Optional[List[Dict]]:
        """调用外部LLM API生成大纲（预留接口）"""
        try:
            import requests
            # 使用DeepSeek/Claude API
            prompt = f"""为以下主题生成{pages}页PPT大纲，返回JSON格式：
主题：{topic}

输出格式（严格JSON数组）：
[
  {{"title": "页标题", "content": ["要点1", "要点2", "要点3"]}},
  ...
]
要求：每页3-5个要点，专业简洁"""
            
            # 这里接入实际的API（后续配置）
            # response = requests.post(...)
            return None
        except Exception:
            return None
    
    def _rule_based_outline(self, topic: str, pages: int) -> List[Dict]:
        """规则生成大纲（备用方案）"""
        slides = [
            {"title": topic, "content": ["概述与背景", "核心概念", "应用场景", "未来展望"]},
        ]
        
        for i in range(1, pages):
            slides.append({
                "title": f"{topic} — 第{i+1}部分",
                "content": [f"关键点{i*3-2}", f"关键点{i*3-1}", f"关键点{i*3}",
                           f"数据分析", f"实践建议"],
            })
        
        return slides
    
    def create_pptx(self, topic: str, pages: int = 5, 
                    template: str = 'business') -> bytes:
        """
        生成PPT文件
        
        Args:
            topic: PPT主题
            pages: 页数
            template: 模板名称
            
        Returns:
            pptx文件字节
        """
        outline = self.generate_outline(topic, pages)
        tmpl = self.templates.get(template, self.templates['business'])
        
        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)
        
        # 封面
        self._add_title_slide(prs, topic, tmpl)
        
        # 内容页
        for slide_data in outline:
            self._add_content_slide(prs, slide_data, tmpl)
        
        # 结束页
        self._add_end_slide(prs, tmpl)
        
        # 保存到内存
        import io
        buf = io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        return buf.getvalue()
    
    def _add_title_slide(self, prs, topic: str, tmpl: Dict):
        """封面页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局
        
        # 背景
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = RGBColor(*tmpl['bg_color'])
        
        # 标题
        txBox = slide.shapes.add_textbox(
            Inches(1), Inches(2), Inches(11), Inches(2))
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = topic
        p.font.size = Pt(44)
        p.font.color.rgb = RGBColor(*tmpl['primary_color'])
        p.font.bold = True
        p.alignment = PP_ALIGN.CENTER
        
        # 副标题：日期
        txBox2 = slide.shapes.add_textbox(
            Inches(1), Inches(4.5), Inches(11), Inches(1))
        tf2 = txBox2.text_frame
        p2 = tf2.paragraphs[0]
        p2.text = f"AI 自动生成 · {datetime.now().strftime('%Y-%m-%d')}"
        p2.font.size = Pt(18)
        p2.font.color.rgb = RGBColor(150, 150, 150)
        p2.alignment = PP_ALIGN.CENTER
    
    def _add_content_slide(self, prs, slide_data: Dict, tmpl: Dict):
        """内容页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        
        # 背景
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = RGBColor(*tmpl['bg_color'])
        
        # 标题栏
        title_bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), 
            Inches(13.333), Inches(1.2))
        title_bar.fill.solid()
        title_bar.fill.fore_color.rgb = RGBColor(*tmpl['primary_color'])
        title_bar.line.fill.background()
        
        tf = title_bar.text_frame
        tf.paragraphs[0].text = slide_data.get('title', '')
        tf.paragraphs[0].font.size = Pt(28)
        tf.paragraphs[0].font.color.rgb = RGBColor(255, 255, 255)
        tf.paragraphs[0].font.bold = True
        tf.margin_left = Inches(0.5)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        
        # 内容列表
        content = slide_data.get('content', [])
        txBox = slide.shapes.add_textbox(
            Inches(1), Inches(2), Inches(11), Inches(5))
        tf = txBox.text_frame
        tf.word_wrap = True
        
        for i, item in enumerate(content):
            if i == 0:
                p = tf.paragraphs[0]
            else:
                p = tf.add_paragraph()
            p.text = f"  ▸  {item}"
            p.font.size = Pt(22)
            p.font.color.rgb = RGBColor(60, 60, 60)
            p.space_after = Pt(12)
    
    def _add_end_slide(self, prs, tmpl: Dict):
        """结束页"""
        slide = prs.slides.add_slide(prs.slide_layouts[6])
        
        bg = slide.background.fill
        bg.solid()
        bg.fore_color.rgb = RGBColor(*tmpl['primary_color'])
        
        txBox = slide.shapes.add_textbox(
            Inches(1), Inches(2.5), Inches(11), Inches(2))
        tf = txBox.text_frame
        p = tf.paragraphs[0]
        p.text = "感谢观看"
        p.font.size = Pt(48)
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.font.bold = True
        p.alignment = PP_ALIGN.CENTER
        
        p2 = tf.add_paragraph()
        p2.text = "由 Orbit AI自动生成"
        p2.font.size = Pt(20)
        p2.font.color.rgb = RGBColor(220, 220, 220)
        p2.alignment = PP_ALIGN.CENTER


# ─── 简化版：单页生成 ────────────────────────────

def quick_slide(topic: str, template: str = 'business') -> bytes:
    """一键生成单页PPT（快速预览用）"""
    gen = PPTGenerator()
    return gen.create_pptx(topic, pages=3, template=template)


if __name__ == '__main__':
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "AI技术发展趋势"
    data = PPTGenerator().create_pptx(topic, pages=5, template='tech')
    with open('/tmp/test.pptx', 'wb') as f:
        f.write(data)
    print(f"✅ PPT生成成功: /tmp/test.pptx ({len(data)} bytes)")
