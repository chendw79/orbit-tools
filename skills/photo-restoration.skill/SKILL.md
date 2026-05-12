---
name: photo-restoration
description: >
  老照片修复/翻新技能包。支持黑白照片检测、去噪、色彩增强、
  自动色阶、高清放大(2x/4x)、划痕修复(OpenCV Inpainting)。
  一键全自动修复流水线。
  触发："修复老照片"、"老照片翻新"、"黑白照片上色"、"图片去噪"
---

# Photo Restoration Skill

## 能力
- 黑白/褪色照片检测
- 去噪 (Non-local Means Denoising)
- 色彩增强/恢复
- 自动对比度+亮度+锐化
- 高清放大 (最高4x, Lanczos插值)
- 划痕/破损修复 (Inpainting)
- 一键全自动修复

## 核心方法
```python
PhotoRestorer.info(img_bytes)               # 图片信息
PhotoRestorer.is_black_white(img_bytes)     # 黑白检测
PhotoRestorer.denoise(img_bytes, 10)        # 去噪 (1-20)
PhotoRestorer.enhance_color(img_bytes, 1.5) # 色彩增强
PhotoRestorer.upscale(img_bytes, 2)         # 2x高清放大
PhotoRestorer.auto_levels(img_bytes)        # 自动色阶
PhotoRestorer.remove_scratches(img_bytes)   # 划痕修复
PhotoRestorer.full_restore(img_bytes)       # 一键全自动
```

## 底层依赖
- OpenCV (Non-local Means, Inpainting)
- Pillow (Lanczos resize, Unsharp Mask)
- numpy
