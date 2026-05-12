---
name: audio-processing
description: >
  音频处理技能包。支持格式转换、裁剪、拼接、变速、降噪、TTS语音合成等。
  Python实现，底层基于FFmpeg。
  触发："帮我处理音频"、"音频格式转换"、"提取语音"、"文字转语音"
---

# Audio Processing Skill

## 能力
- 格式转换 (mp3/wav/ogg/flac/aac)
- 精确裁剪（秒级精度）
- 多文件拼接
- 变速不变调 (0.5x~2.0x)
- 降噪处理
- 立体声转单声道
- 语音识别生成SRT字幕
- 文字转语音 (gTTS)

## 核心方法
```python
AudioProcessor.info('file.mp3')      # 获取信息
AudioProcessor.convert('a.wav','b.mp3')  # 格式转换
AudioProcessor.trim('a.mp3', 10, 30)     # 裁剪(从10秒开始,长30秒)
AudioProcessor.concat(['a.mp3','b.mp3'], 'out.mp3')  # 拼接
AudioProcessor.speed('a.mp3', 1.5)       # 1.5倍速
AudioProcessor.noise_reduce('a.mp3')     # 降噪
AudioProcessor.tts('文字内容', 'out.mp3') # 文字转语音
```

## 支持格式
mp3, wav, ogg, flac, aac, m4a, wma
