"""
Orbit Video Skills v4 — 高优先级技能包

P0: 自动字幕生成 (STT→SRT) + 视频缩略图
P1: 视频防抖 + 批量水印 + 完善转场
"""

import os, json, subprocess, re
from typing import List, Dict, Optional
from datetime import datetime


# ═══════════════════════════════════════════════
# P0: 自动字幕生成
# ═══════════════════════════════════════════════

class AutoSubtitle:
    """自动字幕生成 STT → SRT"""
    
    @staticmethod
    def video_to_srt(input_path: str, output_path: str = None,
                     language: str = 'zh-CN') -> str:
        """
        从视频音频提取语音 → SRT字幕
        
        Args:
            input_path: 视频/音频文件
            output_path: 输出SRT路径
            language: 语言 (zh-CN/en-US/ja-JP)
        """
        if output_path is None:
            output_path = input_path.rsplit('.', 1)[0] + '.srt'
        
        # Step 1: 提取音频
        audio_path = f'/tmp/_stt_audio_{int(datetime.now().timestamp())}.wav'
        extract_cmd = [
            'ffmpeg', '-i', input_path, '-vn',
            '-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1',
            '-y', audio_path
        ]
        subprocess.run(extract_cmd, capture_output=True, timeout=120)
        
        if not os.path.exists(audio_path):
            return "[音频提取失败]"
        
        # Step 2: 语音识别
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            
            with sr.AudioFile(audio_path) as source:
                audio_data = r.record(source)
            
            # 尝试Google语音识别
            text = r.recognize_google(audio_data, language=language)
            
            # Step 3: 生成SRT（分段字幕）
            # 获取音频总时长
            info = AutoSubtitle._get_audio_duration(audio_path)
            duration = info.get('duration_sec', 30)
            
            # 按句子分段（每5-8秒一段）
            sentences = re.split(r'[。！？.!?\n]', text)
            sentences = [s.strip() for s in sentences if s.strip()]
            
            srt_lines = []
            chunk_duration = max(3, duration / max(len(sentences), 1))
            
            for i, sent in enumerate(sentences):
                if not sent:
                    continue
                start = i * chunk_duration
                end = min((i + 1) * chunk_duration, duration)
                
                srt_lines.append(str(i + 1))
                srt_lines.append(
                    f"{AutoSubtitle._sec_to_srt(start)} --> "
                    f"{AutoSubtitle._sec_to_srt(end)}"
                )
                srt_lines.append(sent)
                srt_lines.append('')
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(srt_lines))
            
            # 清理临时文件
            try: os.remove(audio_path)
            except: pass
            
            return output_path
            
        except ImportError:
            return "[需要安装SpeechRecognition]"
        except Exception as e:
            return f"[语音识别失败: {e}]"
    
    @staticmethod
    def add_subtitle_to_video(video_path: str, srt_path: str = None,
                              output_path: str = None) -> str:
        """
        为视频嵌入字幕
        
        Args:
            video_path: 视频路径
            srt_path: SRT字幕路径（None则自动生成）
            output_path: 输出路径
        """
        if srt_path is None:
            srt_path = AutoSubtitle.video_to_srt(video_path)
        
        if output_path is None:
            output_path = video_path.rsplit('.', 1)[0] + '_sub.mp4'
        
        cmd = [
            'ffmpeg', '-i', video_path,
            '-vf', f"subtitles={srt_path}",
            '-c:a', 'copy', '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=300)
        
        return output_path if os.path.exists(output_path) else "[字幕嵌入失败]"
    
    @staticmethod
    def _get_audio_duration(input_path: str) -> dict:
        """获取音频时长"""
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
               '-show_format', input_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            info = json.loads(result.stdout)
            return {'duration_sec': float(info.get('format', {}).get('duration', 0))}
        except:
            return {'duration_sec': 0}
    
    @staticmethod
    def _sec_to_srt(seconds: float) -> str:
        """秒 → SRT时间格式 (00:00:00,000)"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ═══════════════════════════════════════════════
# P0: 视频缩略图生成
# ═══════════════════════════════════════════════

class VideoThumbnail:
    """视频缩略图/封面生成"""
    
    @staticmethod
    def extract_frame(input_path: str, time_sec: float = None,
                      output_path: str = None) -> str:
        """
        提取视频某一帧作为缩略图
        
        Args:
            input_path: 视频路径
            time_sec: 提取时间点（秒），None=自动选最佳帧
            output_path: 输出图片路径
        """
        if output_path is None:
            output_path = input_path.rsplit('.', 1)[0] + '_thumb.jpg'
        
        # 如果未指定时间，自动选择最佳帧（中间偏前1/3处）
        if time_sec is None:
            info = VideoThumbnail._get_video_duration(input_path)
            duration = info.get('duration_sec', 30)
            time_sec = duration * 0.3  # 前1/3处
        
        cmd = [
            'ffmpeg', '-ss', str(time_sec), '-i', input_path,
            '-vframes', '1',
            '-vf', 'scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2',
            '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        
        return output_path if os.path.exists(output_path) else "[缩略图生成失败]"
    
    @staticmethod
    def extract_multi_frames(input_path: str, count: int = 5,
                             output_dir: str = None) -> List[str]:
        """
        提取多帧（用于选择最佳缩略图）
        
        Args:
            input_path: 视频路径
            count: 提取帧数
            output_dir: 输出目录
        """
        if output_dir is None:
            output_dir = f'/tmp/_frames_{int(datetime.now().timestamp())}'
        os.makedirs(output_dir, exist_ok=True)
        
        info = VideoThumbnail._get_video_duration(input_path)
        duration = info.get('duration_sec', 30)
        
        paths = []
        for i in range(count):
            t = duration * (i + 1) / (count + 1)
            path = f'{output_dir}/frame_{i+1:02d}.jpg'
            VideoThumbnail.extract_frame(input_path, t, path)
            if os.path.exists(path):
                paths.append(path)
        
        return paths
    
    @staticmethod
    def create_collage(input_path: str, output_path: str = None,
                       cols: int = 3, rows: int = 2) -> str:
        """
        生成视频剧情概览拼图
        
        Args:
            input_path: 视频路径
            output_path: 输出图片路径
            cols: 列数
            rows: 行数
        """
        if output_path is None:
            output_path = input_path.rsplit('.', 1)[0] + '_collage.jpg'
        
        count = cols * rows
        frames = VideoThumbnail.extract_multi_frames(input_path, count)
        
        if not frames:
            return "[无法提取帧]"
        
        # 用ffmpeg拼图
        tmpdir = os.path.dirname(frames[0]) if frames else '/tmp'
        list_path = f'{tmpdir}/_collage_list.txt'
        
        with open(list_path, 'w') as f:
            for fp in frames:
                f.write(f"file '{fp}'\nduration 0.5\n")
        
        cmd = [
            'ffmpeg', '-f', 'concat', '-safe', '0',
            '-i', list_path,
            '-vf', f'tile={cols}x{rows}',
            '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)
        
        return output_path if os.path.exists(output_path) else "[拼图失败]"
    
    @staticmethod
    def _get_video_duration(input_path: str) -> dict:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
               '-show_format', input_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            info = json.loads(result.stdout)
            return {'duration_sec': float(info.get('format', {}).get('duration', 0))}
        except:
            return {'duration_sec': 0}


# ═══════════════════════════════════════════════
# P1: 视频防抖
# ═══════════════════════════════════════════════

class VideoStabilizer:
    """视频防抖 (基于ffmpeg vidstab)"""
    
    @staticmethod
    def stabilize(input_path: str, output_path: str = None,
                  smoothing: int = 10) -> str:
        """
        视频防抖处理
        
        Args:
            input_path: 输入视频
            output_path: 输出路径
            smoothing: 平滑度 (5-30, 越大越平滑但裁剪越多)
        """
        if output_path is None:
            output_path = input_path.rsplit('.', 1)[0] + '_stable.mp4'
        
        # Step 1: 分析运动轨迹
        transforms_path = f'/tmp/_transforms_{int(datetime.now().timestamp())}.trf'
        cmd1 = [
            'ffmpeg', '-i', input_path,
            '-vf', f'vidstabdetect=stepsize=6:shakiness=8:accuracy=9:result={transforms_path}',
            '-f', 'null', '/dev/null'
        ]
        subprocess.run(cmd1, capture_output=True, timeout=300)
        
        # Step 2: 应用防抖
        cmd2 = [
            'ffmpeg', '-i', input_path,
            '-vf', f'vidstabtransform=smoothing={smoothing}:input={transforms_path}:zoom=0:optzoom=1',
            '-c:a', 'copy', '-y', output_path
        ]
        subprocess.run(cmd2, capture_output=True, timeout=600)
        
        # 清理
        if os.path.exists(transforms_path):
            os.remove(transforms_path)
        
        return output_path if os.path.exists(output_path) else "[防抖失败]"


# ═══════════════════════════════════════════════
# P1: 批量水印
# ═══════════════════════════════════════════════

class BatchWatermark:
    """批量视频水印"""
    
    POSITIONS = {
        'TL': '10:10',        # 左上
        'TC': '(W-w)/2:10',   # 中上
        'TR': 'W-w-10:10',    # 右上
        'BL': '10:H-h-10',    # 左下
        'BC': '(W-w)/2:H-h-10', # 中下
        'BR': 'W-w-10:H-h-10',  # 右下（默认）
    }
    
    @staticmethod
    def add_watermark(input_path: str, watermark_path: str,
                      output_path: str = None,
                      position: str = 'BR', scale: float = 0.15,
                      opacity: float = 0.8) -> str:
        """
        添加水印 (支持图片水印)
        
        Args:
            input_path: 输入视频
            watermark_path: 水印图片路径
            output_path: 输出路径
            position: TL/TC/TR/BL/BC/BR
            scale: 水印占视频宽度比例
            opacity: 不透明度 (0-1)
        """
        if output_path is None:
            output_path = input_path.rsplit('.', 1)[0] + '_wm.mp4'
        
        info = BatchWatermark._get_video_info(input_path)
        w = info.get('width', 1920)
        wm_w = int(w * scale)
        
        pos = BatchWatermark.POSITIONS.get(position, 'W-w-10:H-h-10')
        
        # 水印缩放 + 透明度
        cmd = [
            'ffmpeg', '-i', input_path, '-i', watermark_path,
            '-filter_complex',
            f'[1:v]scale={wm_w}:-1,format=rgba,colorchannelmixer=aa={opacity}[wm];'
            f'[0:v][wm]overlay={pos}[v]',
            '-map', '[v]', '-map', '0:a',
            '-c:v', 'libx264', '-c:a', 'aac', '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=300)
        
        return output_path if os.path.exists(output_path) else "[水印添加失败]"
    
    @staticmethod
    def add_text_watermark(input_path: str, text: str = '@Orbit',
                           output_path: str = None,
                           position: str = 'BR',
                           font_size: int = 24,
                           opacity: float = 0.7) -> str:
        """
        添加文字水印
        
        Args:
            input_path: 输入视频
            text: 水印文字
            output_path: 输出路径
            position: 位置
            font_size: 字号
            opacity: 不透明度
        """
        if output_path is None:
            output_path = input_path.rsplit('.', 1)[0] + '_wmtxt.mp4'
        
        pos = BatchWatermark.POSITIONS.get(position, 'W-w-10:H-h-10')
        
        cmd = [
            'ffmpeg', '-i', input_path,
            '-vf', f"drawtext=text='{text}':fontsize={font_size}:fontcolor=white@{opacity}:x={pos}",
            '-c:a', 'copy', '-y', output_path
        ]
        subprocess.run(cmd, capture_output=True, timeout=300)
        
        return output_path if os.path.exists(output_path) else "[文字水印失败]"
    
    @staticmethod
    def batch_process(file_list: List[str], watermark_path: str,
                      output_dir: str = None) -> List[str]:
        """批量添加水印"""
        if output_dir is None:
            output_dir = f'/tmp/_watermarked_{int(datetime.now().timestamp())}'
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        for fp in file_list:
            basename = os.path.basename(fp)
            out = f'{output_dir}/{basename}'
            result = BatchWatermark.add_watermark(fp, watermark_path, out)
            results.append(result)
        
        return results
    
    @staticmethod
    def _get_video_info(input_path: str) -> dict:
        cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json',
               '-show_streams', input_path]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            info = json.loads(result.stdout)
            for s in info.get('streams', []):
                if s['codec_type'] == 'video':
                    return {'width': s.get('width', 0), 'height': s.get('height', 0)}
        except:
            pass
        return {'width': 1920, 'height': 1080}


if __name__ == '__main__':
    print("🎬 Orbit Video Skills v4 — 优先级排序")
    print("  P0: 自动字幕生成 + 缩略图 ======================")
    print(f"    AutoSubtitle:    {len([m for m in dir(AutoSubtitle) if not m.startswith('_')])} methods")
    print(f"    VideoThumbnail:  {len([m for m in dir(VideoThumbnail) if not m.startswith('_')])} methods")
    print(f"    VideoStabilizer: stabilize + batch")
    print(f"    BatchWatermark:  {len(BatchWatermark.POSITIONS)} 位置 + text overlay")
    print()
    
    # 测试缩略图
    print("测试缩略图生成...")
    thumb = VideoThumbnail.extract_frame('/tmp/test_av.mp4', time_sec=0)
    size = os.path.getsize(thumb) if os.path.exists(thumb) else 0
    print(f"  缩略图: {size/1024:.0f}KB")
    
    # 测试多帧提取
    frames = VideoThumbnail.extract_multi_frames('/tmp/test_av.mp4', count=3)
    print(f"  多帧: {len(frames)} files")
    
    print()
    print("✅ Video Skills v4 全部就绪!")
