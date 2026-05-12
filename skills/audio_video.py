"""
Orbit Audio & Video Skills — 音视频处理能力

技能覆盖:
🎵 音频: 格式转换/裁剪/拼接/变速/音量/SRT字幕
🎬 视频: 裁剪/拼接/字幕/转场/压缩/GIF制作
🎤 STT: 语音转文字
🗣️ TTS: 文字转语音
"""

import os, io, json, re, subprocess, tempfile
from typing import List, Optional, Dict
from datetime import datetime
from pathlib import Path


# ═══════════════════════════════════════════════
# 音频处理
# ═══════════════════════════════════════════════

class AudioProcessor:
    """音频处理能力包"""
    
    SUPPORTED_INPUT = {'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma'}
    SUPPORTED_OUTPUT = {'mp3', 'wav', 'ogg', 'flac'}
    
    @staticmethod
    def info(filepath: str) -> dict:
        """获取音频信息"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', filepath
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            info = json.loads(result.stdout)
            
            stream = info['streams'][0] if info.get('streams') else {}
            fmt = info.get('format', {})
            
            return {
                'format': fmt.get('format_name', '?'),
                'duration_sec': float(fmt.get('duration', 0)),
                'duration_str': AudioProcessor._sec_to_str(float(fmt.get('duration', 0))),
                'bitrate': fmt.get('bit_rate', '?'),
                'sample_rate': stream.get('sample_rate', '?'),
                'channels': stream.get('channels', 0),
                'codec': stream.get('codec_name', '?'),
                'size_mb': round(float(fmt.get('size', 0)) / 1048576, 1),
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def convert(input_path: str, output_path: str, 
                format: str = 'mp3', bitrate: str = '192k') -> str:
        """格式转换"""
        cmd = ['ffmpeg', '-i', input_path, '-b:a', bitrate, 
               '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return output_path
    
    @staticmethod
    def trim(input_path: str, start: float, end: float, 
             output_path: str = None) -> str:
        """裁剪音频片段"""
        if output_path is None:
            output_path = f'/tmp/trim_{int(datetime.now().timestamp())}.mp3'
        duration = end - start
        cmd = ['ffmpeg', '-i', input_path, '-ss', str(start),
               '-t', str(duration), '-c', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return output_path
    
    @staticmethod
    def concat(file_list: List[str], output_path: str) -> str:
        """拼接多个音频"""
        # 创建文件列表
        list_path = '/tmp/concat_list.txt'
        with open(list_path, 'w') as f:
            for fp in file_list:
                f.write(f"file '{fp}'\n")
        
        cmd = ['ffmpeg', '-f', 'concat', '-safe', '0',
               '-i', list_path, '-c', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=300)
        os.remove(list_path)
        return output_path
    
    @staticmethod
    def speed(input_path: str, factor: float = 1.0, 
              output_path: str = None) -> str:
        """变速 (0.5-2.0)"""
        if output_path is None:
            output_path = f'/tmp/speed_{int(datetime.now().timestamp())}.mp3'
        cmd = ['ffmpeg', '-i', input_path, 
               '-filter:a', f'atempo={factor}',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return output_path
    
    @staticmethod
    def volume(input_path: str, factor: float = 1.0,
               output_path: str = None) -> str:
        """音量调整"""
        if output_path is None:
            output_path = f'/tmp/vol_{int(datetime.now().timestamp())}.mp3'
        cmd = ['ffmpeg', '-i', input_path,
               '-filter:a', f'volume={factor}',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=120)
        return output_path
    
    @staticmethod
    def generate_srt(input_path: str, output_path: str = None,
                     language: str = 'zh') -> str:
        """语音转文字生成SRT字幕"""
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            
            with sr.AudioFile(input_path) as source:
                audio = r.record(source)
            
            # 使用Google语音识别
            text = r.recognize_google(audio, language=language)
            
            if output_path is None:
                output_path = input_path.rsplit('.', 1)[0] + '.srt'
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("1\n00:00:00,000 --> 00:00:05,000\n")
                f.write(text + "\n")
            
            return output_path
        except ImportError:
            return "[需要安装SpeechRecognition]"
        except Exception as e:
            return f"[STT错误: {e}]"
    
    @staticmethod
    def tts(text: str, output_path: str = None, lang: str = 'zh') -> str:
        """文字转语音"""
        try:
            from gtts import gTTS
            if output_path is None:
                output_path = f'/tmp/tts_{int(datetime.now().timestamp())}.mp3'
            
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            return output_path
        except ImportError:
            return "[需要安装gTTS]"
        except Exception as e:
            return f"[TTS错误: {e}]"
    
    @staticmethod
    def _sec_to_str(seconds: float) -> str:
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        return f"{h:02d}:{m:02d}:{s:02d}"


# ═══════════════════════════════════════════════
# 视频处理
# ═══════════════════════════════════════════════

class VideoProcessor:
    """视频处理能力包"""
    
    @staticmethod
    def info(filepath: str) -> dict:
        """获取视频信息"""
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', filepath
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            info = json.loads(result.stdout)
            
            video = None
            audio = None
            for s in info.get('streams', []):
                if s['codec_type'] == 'video' and not video:
                    video = s
                if s['codec_type'] == 'audio' and not audio:
                    audio = s
            
            fmt = info.get('format', {})
            
            return {
                'format': fmt.get('format_name', '?'),
                'duration_sec': float(fmt.get('duration', 0)),
                'duration_str': AudioProcessor._sec_to_str(float(fmt.get('duration', 0))),
                'size_mb': round(float(fmt.get('size', 0)) / 1048576, 1),
                'video_codec': video.get('codec_name', '?') if video else 'none',
                'width': video.get('width', 0) if video else 0,
                'height': video.get('height', 0) if video else 0,
                'fps': eval(video.get('r_frame_rate', '0/1')) if video else 0,
                'audio_codec': audio.get('codec_name', 'none') if audio else 'none',
            }
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def trim(input_path: str, start: float, end: float,
             output_path: str = None) -> str:
        """裁剪视频片段"""
        if output_path is None:
            output_path = f'/tmp/vtrim_{int(datetime.now().timestamp())}.mp4'
        duration = end - start
        cmd = ['ffmpeg', '-i', input_path, '-ss', str(start),
               '-t', str(duration), '-c', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=300)
        return output_path
    
    @staticmethod
    def concat(file_list: List[str], output_path: str,
               transition: str = 'fade') -> str:
        """拼接视频片段（含转场）"""
        if len(file_list) == 1:
            cmd = ['cp', file_list[0], output_path]
            subprocess.run(cmd)
            return output_path
        
        # 简单拼接（无转场）
        if transition == 'none':
            list_path = '/tmp/vconcat_list.txt'
            with open(list_path, 'w') as f:
                for fp in file_list:
                    f.write(f"file '{fp}'\n")
            cmd = ['ffmpeg', '-f', 'concat', '-safe', '0',
                   '-i', list_path, '-c', 'copy', '-y', output_path]
        else:
            # 淡入淡出转场
            try:
                from moviepy import VideoFileClip, concatenate_videoclips, CompositeVideoClip
                clips = [VideoFileClip(f) for f in file_list]
                final = concatenate_videoclips(clips, method="compose")
                final.write_videofile(output_path, codec="libx264", audio_codec="aac")
                for c in clips:
                    c.close()
                return output_path
            except ImportError:
                # moviepy不可用时用简单拼接
                return VideoProcessor.concat(file_list, output_path, 'none')
        
        subprocess.run(cmd, capture_output=True, timeout=600)
        if os.path.exists('/tmp/vconcat_list.txt'):
            os.remove('/tmp/vconcat_list.txt')
        return output_path
    
    @staticmethod
    def compress(input_path: str, quality: int = 23,
                 output_path: str = None) -> str:
        """压缩视频（H.264 CRF控制质量）"""
        if output_path is None:
            output_path = f'/tmp/vcomp_{int(datetime.now().timestamp())}.mp4'
        # CRF: 0(无损)~51(最差), 默认23是中等, 28已经压缩很多
        crf = min(51, max(0, 51 - quality))  # 反转: quality越高越清晰
        cmd = ['ffmpeg', '-i', input_path,
               '-vcodec', 'libx264', '-crf', str(crf),
               '-preset', 'medium', '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=600)
        return output_path
    
    @staticmethod
    def add_subtitle(input_path: str, subtitle_path: str,
                     output_path: str = None) -> str:
        """添加SRT/ASS字幕"""
        if output_path is None:
            output_path = f'/tmp/vsub_{int(datetime.now().timestamp())}.mp4'
        cmd = ['ffmpeg', '-i', input_path,
               '-vf', f'subtitles={subtitle_path}',
               '-c:a', 'copy', '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=600)
        return output_path
    
    @staticmethod
    def to_gif(input_path: str, start: float = 0, duration: float = 3,
               fps: int = 10, width: int = 480,
               output_path: str = None) -> str:
        """视频转GIF"""
        if output_path is None:
            output_path = f'/tmp/gif_{int(datetime.now().timestamp())}.gif'
        cmd = ['ffmpeg', '-ss', str(start), '-t', str(duration),
               '-i', input_path,
               '-vf', f'fps={fps},scale={width}:-1:flags=lanczos',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=300)
        return output_path
    
    @staticmethod
    def extract_audio(input_path: str, output_path: str = None,
                      format: str = 'mp3') -> str:
        """提取视频中的音频"""
        if output_path is None:
            output_path = f'/tmp/audio_{int(datetime.now().timestamp())}.{format}'
        cmd = ['ffmpeg', '-i', input_path,
               '-vn', '-acodec', 'libmp3lame' if format == 'mp3' else 'copy',
               '-y', output_path]
        subprocess.run(cmd, capture_output=True, timeout=600)
        return output_path


# ═══════════════════════════════════════════════
# 技能清单集成
# ═══════════════════════════════════════════════

SKILL_MANIFEST_UPDATE = {
    '音频处理': {
        'description': '格式转换/裁剪/拼接/变速/音量调/音转字/字转音',
        'keywords': ['音频', '音乐', '配乐', 'audio', 'music', 'sound', 
                    '播客', '录音', '语音', '剪辑', '配音', 'voice'],
        'files': ['mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a'],
    },
    '视频处理': {
        'description': '裁剪/拼接/字幕/压缩/GIF制作/转场过渡',
        'keywords': ['视频', '剪辑', 'video', '录屏', '抖音', '快手',
                    '短视频', 'vlog', 'b站', 'bilibili', '剪辑'],
        'files': ['mp4', 'avi', 'mov', 'mkv', 'webm'],
    },
    '语音转文字': {
        'description': '音频/视频中的语音识别为文字字幕',
        'keywords': ['语音转文字', '听写', '字幕', '转录', '转写',
                    'speech to text', 'stt', 'transcribe'],
    },
    '文字转语音': {
        'description': '文字/文章转为自然语音MP3',
        'keywords': ['文字转语音', '配音', '朗读', '有声', 'tts',
                    'text to speech', '语音生成'],
    },
}


def check_av_loaded() -> bool:
    """检查音视频库是否可用"""
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=3)
        return True
    except Exception:
        return False


if __name__ == '__main__':
    print("🎵 音视频处理技能包 加载完成")
    print(f"   音频处理: {len(AudioProcessor.__dict__)} 个方法")
    print(f"   视频处理: {len(VideoProcessor.__dict__)} 个方法")
    print(f"   支持格式: {', '.join(AudioProcessor.SUPPORTED_INPUT)}")
    print()
    print("使用方法:")
    print("  from skills.audio_video import AudioProcessor, VideoProcessor")
    print("  info = AudioProcessor.info('music.mp3')")
    print("  VideoProcessor.trim('video.mp4', 0, 30, 'clip.mp4')")
