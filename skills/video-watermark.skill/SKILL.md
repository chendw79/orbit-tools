---
name: video-watermark
description: >
  视频水印添加。支持图片水印(6位置+透明度+缩放)和文字水印。
  批量处理。适合品牌保护/内容分发。
  触发："加水印"、"水印"、"logo"、"品牌保护"
---

# Video Watermark Skill

## 能力
- 图片水印 (6个位置, 可调大小和透明度)
- 文字水印 (自定义文字/字号/透明度)
- 批量处理 (多个视频一次加水印)
- 视频防抖 (ffmpeg vidstab)

## 水印位置
TL=左上, TC=中上, TR=右上
BL=左下, BC=中下, BR=右下

## 使用方法
```python
from skills.audio_video_v4 import BatchWatermark

# 图片水印
out = BatchWatermark.add_watermark('v.mp4', 'logo.png', 'out.mp4', 'BR')

# 文字水印
out = BatchWatermark.add_text_watermark('v.mp4', '@Orbit')

# 批量
outs = BatchWatermark.batch_process(['a.mp4','b.mp4'], 'logo.png')
```
