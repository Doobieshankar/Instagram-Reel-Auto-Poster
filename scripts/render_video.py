#!/usr/bin/env python3
"""
render_video.py  <image_path> <audio_path> <output_path> <caption_text>

- Resizes image to 1080x1920 (Instagram Reels portrait)
- Ken Burns zoom effect
- Word-level captions from the script text (no Whisper needed — TTS text is known)
- Requires: moviepy==1.0.3, Pillow, numpy
"""
import sys, os, textwrap, math
import numpy as np
from PIL import Image
from moviepy.editor import (
    AudioFileClip, ImageClip, VideoClip, TextClip, CompositeVideoClip
)

REEL_W, REEL_H = 1080, 1920
FPS = 30

image_path  = sys.argv[1]
audio_path  = sys.argv[2]
output_path = sys.argv[3]
caption_text = sys.argv[4] if len(sys.argv) > 4 else ""

# ---------- Audio ----------
audio = AudioFileClip(audio_path)
duration = audio.duration

# ---------- Image → 1080x1920 (fill, center-crop) ----------
pil_img = Image.open(image_path).convert("RGB")
target_ratio = REEL_W / REEL_H
src_ratio    = pil_img.width / pil_img.height
if src_ratio > target_ratio:
    # wider than target: fit height, crop width
    new_h = REEL_H
    new_w = int(src_ratio * new_h)
else:
    new_w = REEL_W
    new_h = int(new_w / src_ratio)
pil_img = pil_img.resize((new_w, new_h), Image.LANCZOS)
left = (new_w - REEL_W) // 2
top  = (new_h - REEL_H) // 2
pil_img = pil_img.crop((left, top, left + REEL_W, top + REEL_H))
frame_np = np.array(pil_img)

# ---------- Ken Burns: slow zoom in ----------
def make_frame(t):
    scale = 1.0 + 0.04 * (t / duration)          # 1.0x → 1.04x
    new_w = int(REEL_W * scale)
    new_h = int(REEL_H * scale)
    resized = Image.fromarray(frame_np).resize((new_w, new_h), Image.BILINEAR)
    x = (new_w - REEL_W) // 2
    y = (new_h - REEL_H) // 2
    cropped = np.array(resized)[y:y+REEL_H, x:x+REEL_W]
    return cropped

img_clip = VideoClip(make_frame, duration=duration).set_fps(FPS)

# ---------- Captions: evenly distribute words over duration ----------
txt_clips = []
if caption_text.strip():
    words = caption_text.split()
    # chunk into lines of ~6 words
    chunks = [" ".join(words[i:i+6]) for i in range(0, len(words), 6)]
    seg_dur = duration / len(chunks)
    for idx, chunk in enumerate(chunks):
        try:
            txt = (TextClip(
                        chunk,
                        fontsize=55,
                        font="DejaVu-Sans-Bold",
                        color="white",
                        stroke_color="black",
                        stroke_width=2,
                        method="caption",
                        size=(REEL_W - 80, None),
                    )
                    .set_start(idx * seg_dur)
                    .set_duration(seg_dur)
                    .set_position(("center", REEL_H - 220)))
            txt_clips.append(txt)
        except Exception as e:
            print(f"[warn] TextClip failed for chunk '{chunk}': {e}", file=sys.stderr)

# ---------- Compose ----------
layers = [img_clip] + txt_clips
video = CompositeVideoClip(layers, size=(REEL_W, REEL_H))
video = video.set_audio(audio)

os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
video.write_videofile(
    output_path,
    fps=FPS,
    codec="libx264",
    audio_codec="aac",
    preset="fast",          # faster encode on low-end CPU
    ffmpeg_params=["-crf", "23"],
    logger=None,
)
print(output_path)
