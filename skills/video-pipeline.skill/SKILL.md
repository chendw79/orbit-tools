---
name: video-pipeline
description: >
  完整视频制作流水线。输入主题，自动完成：素材调研→逐字稿→AI配音→时间轴→视频输出。
  端到端自动化，适合科普/教育类短视频制作。
  触发："制作一个关于X的视频"、"创建视频项目"、"视频流水线"
---

# Video Pipeline Skill

## 完整流水线

```
主题输入 → 素材调研 → 逐字稿 → AI配音 → 时间轴 → 视频输出
```

## 5个步骤
1. **调研** - 收集主题素材和关键词
2. **脚本** - 自动生成带时间标的逐字稿
3. **配音** - gTTS生成旁白MP3
4. **时间轴** - 计算音频时长，生成剪辑方案
5. **组装** - 音频+画面融合输出MP4

## 使用方法
```python
pipeline = VideoPipeline('/tmp/my_project')
result = pipeline.run_full_pipeline('AI视频制作技术')
print(result['output'])  # 最终视频路径
```
