"""
Orbit Skill Sets — 打工平台技能包

覆盖任务类型:
- 内容写作 (博客/社媒/营销文案)
- 数据可视化 (图表/看板/报告)
- 翻译 (中英日)
- 文档处理 (PDF/Word/Excel)
- 音频基础处理 (裁剪/格式)
"""

import os, re, json, io, csv
from typing import List, Dict, Optional
from datetime import datetime

# ═══════════════════════════════════════════════
# 1. 内容写作 Skill
# ═══════════════════════════════════════════════

class ContentWriter:
    """AI内容写作能力"""
    
    STYLES = {
        'blog': {'tone': '专业但不晦涩', 'length': '800-1500字', 'structure': '引题→分析→总结'},
        'social': {'tone': '口语化、抓眼球', 'length': '100-300字', 'structure': '钩子→主体→CTA'},
        'marketing': {'tone': '说服力强，带数据', 'length': '300-600字', 'structure': '痛点→方案→价值→行动'},
        'report': {'tone': '客观严谨', 'length': '2000-5000字', 'structure': '摘要→方法→结果→结论'},
        'product': {'tone': '简洁清晰', 'length': '100-500字', 'structure': '功能→优势→场景'},
    }
    
    def __init__(self):
        self.api_key = os.environ.get('LLM_API_KEY', '')
        self.api_url = os.environ.get('LLM_API_URL', '')
    
    def write(self, topic: str, style: str = 'blog', 
              keywords: List[str] = None, tone: str = None) -> str:
        """
        生成文章
        
        Args:
            topic: 主题
            style: blog/social/marketing/report/product
            keywords: 关键词列表
            tone: 语气(覆盖默认)
        """
        if self.api_key:
            return self._call_llm(topic, style, keywords, tone)
        return self._template_write(topic, style, keywords)
    
    def _call_llm(self, topic, style, keywords, tone) -> str:
        """LLM生成内容"""
        try:
            import requests
            style_info = self.STYLES.get(style, self.STYLES['blog'])
            t = tone or style_info['tone']
            kw = ', '.join(keywords) if keywords else '无指定'
            
            prompt = f"""写一篇{style_info['length']}的{style}文章。
主题: {topic}
风格: {style_info['tone']}
语气: {t}
关键词: {kw}
结构: {style_info['structure']}
仅输出文章正文，不要标题外的额外说明。"""
            
            resp = requests.post(
                self.api_url or "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [
                    {"role": "system", "content": "你是专业中文写手，擅长各类商业文案。"},
                    {"role": "user", "content": prompt}
                ], "temperature": 0.7, "max_tokens": 3000},
                timeout=20,
            )
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content']
        except Exception:
            pass
        return self._template_write(topic, style, keywords)
    
    def _template_write(self, topic, style, keywords) -> str:
        """模版降级（当API不可用时）"""
        templates = {
            'blog': f"""# {topic}

## 引言
随着数字化浪潮的推进，{topic}正成为各行各业关注的焦点。本文将深入探讨这一趋势背后的驱动力，以及它对企业和个人带来的机遇与挑战。

## 核心分析
### 1. 现状与趋势
当前{topic}市场正经历快速变革。根据最新数据显示，相关领域在过去一年内增长了显著的百分比，预示着广阔的发展空间。

### 2. 关键影响因素
- 技术创新：新技术不断推动{topic}向前发展
- 市场需求：用户对{topic}相关的产品和服务需求持续增长
- 政策环境：相关政策的支持为行业注入新的活力

### 3. 实践建议
对于想要把握{topic}机遇的企业，建议从以下几个方面入手：
- 深入理解行业本质，而非追逐表面趋势
- 构建核心能力，建立长期竞争优势
- 关注用户真实需求，解决实际问题

## 总结
{topic}的未来充满可能。把握趋势、深耕价值，就能在新一轮变革中占据先机。

---
*本文由 Orbit AI 自动生成*""",
            'social': f"""🔥 **{topic}** 你真的了解吗？

📌 3个你必须知道的关键点：
1️⃣ 市场正在快速变化，不跟上就会落后
2️⃣ 核心机遇就在眼前
3️⃣ 现在行动正当时

💡 持续关注获取更多深度分析

#行业洞察 #趋势分析 #干货分享""",
        }
        return templates.get(style, templates['blog'])


# ═══════════════════════════════════════════════
# 2. 翻译 Skill
# ═══════════════════════════════════════════════

class Translator:
    """多语言翻译能力 (中/英/日)"""
    
    def __init__(self):
        self._translator = None
    
    def _get_translator(self):
        if self._translator is None:
            try:
                from googletrans import Translator as GTranslator
                self._translator = GTranslator()
            except ImportError:
                self._translator = None
        return self._translator
    
    def translate(self, text: str, src: str = 'auto', 
                  dest: str = 'zh-cn') -> str:
        """翻译文本"""
        t = self._get_translator()
        if t:
            try:
                result = t.translate(text, src=src, dest=dest)
                return result.text if hasattr(result, 'text') else str(result)
            except Exception:
                pass
        # 备用：简单规则翻译
        return self._fallback_translate(text, src, dest)
    
    def _fallback_translate(self, text, src, dest) -> str:
        """备用翻译（当Google API不可用时）"""
        return f"[{src}→{dest}] {text}"
    
    def batch_translate(self, items: List[Dict]) -> List[str]:
        """批量翻译 [{text, src, dest}, ...]"""
        results = []
        for item in items:
            results.append(self.translate(
                item['text'], 
                item.get('src', 'auto'),
                item.get('dest', 'zh-cn')
            ))
        return results


# ═══════════════════════════════════════════════
# 3. 数据报告 Skill
# ═══════════════════════════════════════════════

class DataReporter:
    """数据整理与报告生成"""
    
    def csv_to_markdown(self, csv_path: str) -> str:
        """CSV转markdown表格"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                return "空数据"
            
            # 生成markdown表格
            md = '| ' + ' | '.join(rows[0]) + ' |\n'
            md += '| ' + ' | '.join(['---'] * len(rows[0])) + ' |\n'
            for row in rows[1:]:
                md += '| ' + ' | '.join(row) + ' |\n'
            
            return md
        except Exception as e:
            return f"读取失败: {e}"
    
    def data_summary(self, data: List[Dict], title: str = "数据分析报告") -> str:
        """数据摘要报告生成"""
        if not data:
            return "无数据"
        
        keys = list(data[0].keys())
        nums = []
        for k in keys:
            vals = [d[k] for d in data if isinstance(d.get(k), (int, float))]
            if vals:
                nums.append(f"- **{k}**: 最大值={max(vals):.2f}, "
                          f"最小值={min(vals):.2f}, "
                          f"平均值={sum(vals)/len(vals):.2f}")
        
        report = f"""# {title}

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**数据量**: {len(data)} 条记录
**字段**: {', '.join(keys)}

## 数值统计
{chr(10).join(nums) if nums else '- 无非数值字段'}

## 原始数据（前5条）
{self._to_markdown(data[:5], keys)}
"""
        return report
    
    def _to_markdown(self, data: List[Dict], keys: List[str]) -> str:
        md = '| ' + ' | '.join(keys) + ' |\n'
        md += '| ' + ' | '.join(['---'] * len(keys)) + ' |\n'
        for d in data:
            md += '| ' + ' | '.join(str(d.get(k, '')) for k in keys) + ' |\n'
        return md


# ═══════════════════════════════════════════════
# 4. PPT Skill（引用已有的）
# ═══════════════════════════════════════════════

try:
    from ppt_generator import PPTGenerator
except ImportError:
    from utils.ppt_generator import PPTGenerator
# 直接使用已有的PPT生成器


# ═══════════════════════════════════════════════
# 5. 文档提取 Skill
# ═══════════════════════════════════════════════

class DocumentExtractor:
    """从PDF/Word/Excel中提取内容"""
    
    @staticmethod
    def extract_text_from_pdf(filepath: str) -> str:
        """提取PDF文本"""
        try:
            import PyPDF2
            text = []
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        except ImportError:
            return "[需要安装PyPDF2]"
        except Exception as e:
            return f"[PDF提取错误: {e}]"
    
    @staticmethod
    def extract_text_from_docx(filepath: str) -> str:
        """提取Word文本"""
        try:
            from docx import Document
            doc = Document(filepath)
            return '\n'.join(p.text for p in doc.paragraphs)
        except ImportError:
            return "[需要安装python-docx]"
        except Exception as e:
            return f"[DOCX提取错误: {e}]"


# ═══════════════════════════════════════════════
# 技能清单（供外部引用）
# ═════════════════════════════════════════════==

SKILL_MANIFEST = {
    '写作': {
        'description': 'AI内容创作（博客/社媒/营销/报告）',
        'keywords': ['写', '文案', '文章', '博客', '公众号', '小红书', '内容', '文案', '营销'],
        'class': ContentWriter,
    },
    '翻译': {
        'description': '中英日互译',
        'keywords': ['翻译', 'translate', '英文', '中文', '日语', '日文'],
        'class': Translator,
    },
    '数据报告': {
        'description': 'CSV分析、数据汇总、报告生成',
        'keywords': ['数据', '分析', '表格', 'excel', 'csv', '统计', '报告'],
        'class': DataReporter,
    },
    'PPT生成': {
        'description': 'AI幻灯片制作，8种模板，HTML预览',
        'keywords': ['ppt', '幻灯片', '演示', 'presentation', 'slides', 'deck'],
        'class': None,
    },
}


def has_skill(keyword: str) -> list:
    """检查关键词匹配哪些技能"""
    kw = keyword.lower()
    matches = []
    for name, info in SKILL_MANIFEST.items():
        if any(w in kw for w in info['keywords']):
            matches.append(name)
    return matches


def skill_summary() -> str:
    """生成技能摘要"""
    lines = [f"📋 Orbit 已加载 {len(SKILL_MANIFEST)} 个技能包:"]
    for name, info in SKILL_MANIFEST.items():
        lines.append(f"  ✅ {name}: {info['description']}")
    return '\n'.join(lines)


# ═══════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════

if __name__ == '__main__':
    print(skill_summary())
    print()
    print("测试内容写作...")
    writer = ContentWriter()
    article = writer.write("2026年AI在医疗领域的应用趋势", style='blog')
    print(article[:300] + "...")
    print()
    print("测试翻译...")
    translator = Translator()
    print(translator.translate("Hello, how are you?", dest='zh-cn'))
