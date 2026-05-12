---
name: video-thumbnail
description: >
  视频缩略图/封面生成。提取关键帧、多帧选择、剧情拼图。
  自动选择最佳时间点，适配1280x720封面尺寸。
  触发："生成封面"、"视频缩略图"、"提取帧"、"截图"
---

# Video Thumbnail Skill

## 能力
- 单帧提取（可指定/自动选择最佳时间点）
- 多帧提取（供选择最佳封面）
- 剧情拼图（多帧组合为一张预览图）

## 使用方法
```python
from skills.audio_video_v4 import VideoThumbnail

# 提取一帧（自动选择前1/3处）
thumb = VideoThumbnail.extract_frame('video.mp4')

# 提取5帧供选择
frames = VideoThumbnail.extract_multi_frames('video.mp4', 5)

# 生成剧情拼图 (3x2)
collage = VideoThumbnail.create_collage('video.mp4', cols=3, rows=2)
```
