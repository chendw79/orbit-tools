---
name: auto-subtitle
description: >
  视频自动字幕生成。从视频音频提取语音 → SRT字幕文件 →
  嵌入到视频中。支持中文/英文/日文。
  触发："加字幕"、"生成字幕"、"语音转文字"、"SRT"
---

# Auto Subtitle Skill

## 能力
- 自动语音识别 (SpeechRecognition + Google API)
- SRT字幕文件生成
- 字幕嵌入到视频
- 支持中文/英文/日文

## 使用方法
```python
from skills.audio_video_v4 import AutoSubtitle

# 从视频生成SRT字幕
srt = AutoSubtitle.video_to_srt('video.mp4', language='zh-CN')

# 自动生成+嵌入字幕
output = AutoSubtitle.add_subtitle_to_video('video.mp4')
```
