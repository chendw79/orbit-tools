---
name: advanced-video-processing
description: >
  高级视频处理技能包v3。场景自动分割、智能拼接(交叉淡入淡出)、
  画中画叠加、文字叠加、平台预设压缩(微信/抖音/B站/4K)、
  高清转换(2x/4x Lanczos)、智能剪辑(去空段+转场+压缩)
  触发："视频拼接"、"自动剪辑"、"画中画"、"压缩视频"
---

# Advanced Video Processing v3

## 能力
- 场景检测 (scenedetect + ffmpeg)
- 智能拼接 (crossfade/fade/cut/slide)
- 画中画PIP (4角位置, 可调大小)
- 文字叠加 (底部/顶部/居中, 自定义)
- 平台预设压缩 (微信/抖音/B站/4K)
- 高清转换 (2x/4x Lanczos+锐化)
- 一键自动剪辑

## 平台预设
| 预设 | CRF | 分辨率 | 场景 |
|------|-----|--------|------|
| wechat | 32 | 720p | 微信发送 |
| douyin | 26 | 1080p | 抖音/快手 |
| bilibili | 23 | 1080p | B站/YouTube |
| hd | 18 | 4K | 高质量存储 |
| 4k | 28 | 4K | H.265压缩 |

## 核心方法
```python
# 场景检测
scenes = AVP.detect_scenes('video.mp4', threshold=27)

# 智能拼接
AVP.smart_concat(['a.mp4','b.mp4'], 'out.mp4', 'crossfade')

# 画中画
AVP.overlay_pip('main.mp4', 'pip.mp4', 'out.mp4', 'BR', 0.3)

# 文字叠加
AVP.add_text_overlay('v.mp4', 'Hello', 'out.mp4', 'bottom', 36)

# 平台压缩
AVP.compress_for_platform('v.mp4', 'wechat')

# 高清转换
AVP.hd_convert('v.mp4', 2)

# 一键自动剪辑
AVP.auto_edit('v.mp4', 'out.mp4')

# 智能分割重组
AVP.split_and_reassemble('v.mp4', 'out.mp4')
```
