---
name: video-processing
description: >
  视频处理技能包。支持转码、裁剪、压缩、变速、字幕、GIF、水印、分割等。
  Python实现，底层基于FFmpeg生产级命令。
  触发："帮我处理视频"、"视频压缩"、"加字幕"、"视频转GIF"
---

# Video Processing Skill

## 能力
- 格式转换 (←mkv/avi/mov →mp4)
- 视频压缩 (CRF控制, 0无损~51最小)
- 精确裁剪/无损裁剪
- 视频变速 (0.5x~4x, 音频同步)
- 字幕嵌入 (SRT/ASS)
- 视频转GIF
- 添加水印 (4角可选)
- 分割为片段
- 提取音频

## 核心方法
```python
VideoProcessor.info('video.mp4')           # 视频信息
VideoProcessor.convert_to_mp4('a.mkv')     # 转码
VideoProcessor.compress('a.mp4', crf=28)   # 压缩
VideoProcessor.trim('a.mp4', 5, 30)        # 裁剪
VideoProcessor.resize('a.mp4', 1280, 720)  # 缩放
VideoProcessor.speed('a.mp4', 2.0)         # 2倍速
VideoProcessor.to_gif('a.mp4', 0, 3)       # 转GIF
VideoProcessor.add_subtitle('a.mp4', 'sub.srt')  # 嵌字幕
VideoProcessor.extract_audio('a.mp4')      # 提取音频
```

## 质量参考
- CRF 18: 视觉无损
- CRF 23: 默认(推荐)
- CRF 28: 小体积(微信发送)
- CRF 35: 极小体积
