import io
import os
import random
import textwrap

import numpy as np
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

from moviepy.editor import ImageClip, concatenate_videoclips


# ---------- TEXT -> IMAGE (PIL) ----------
def make_text_frame(
    text: str,
    w: int = 1080,
    h: int = 1920,
    font_size: int = 90,
    margin: int = 80,
):
    img = Image.new("RGB", (w, h), (0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Use a safe default font (works in most environments)
    # If you want custom fonts, upload a .ttf and point to it.
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Wrap text to fit width
    max_width_px = w - 2 * margin

    def text_width(s):
        bbox = draw.textbbox((0, 0), s, font=font)
        return bbox[2] - bbox[0]

    # greedy wrap by words
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = (current + " " + word).strip()
        if text_width(test) <= max_width_px:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    # measure height
    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_heights.append(bbox[3] - bbox[1])

    total_text_h = sum(line_heights) + (len(lines) - 1) * 20
    y = (h - total_text_h) // 2

    # draw centered
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        line_h = bbox[3] - bbox[1]

        x = (w - line_w) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_h + 20

    return np.array(img)


# ---------- BUILD VIDEO ----------
def build_video(lines, total_duration, w, h, font_size, fps):
    clip_len = total_duration / len(lines)

    clips = []
    for t in lines:
        frame = make_text_frame(
            t,
            w=w,
            h=h,
            font_size=font_size,
        )

        # "engaging" micro-movement: tiny zoom jitter
        zoom = random.uniform(1.00, 1.06)

        clip = (
            ImageClip(frame)
            .set_duration(clip_len)
            .resize(zoom)
            .set_position("center")
        )

        clips.append(clip)

    final = concatenate_videoclips(clips, method="compose")
    return final


# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="Quick Cuts Text Video", layout="centered")
st.title("Quick Cuts Text Video Generator")

default_script = """Stop scrolling.
This AI tool is insane.
One prompt.
Done.
Try it today."""

script = st.text_area("Script (one line per cut)", value=default_script, height=200)

total_duration = st.slider("Total duration (seconds)", 8.0, 15.0, 10.0, 0.5)
font_size = st.slider("Font size", 50, 130, 95, 5)

format_choice = st.selectbox("Format", ["Vertical (1080x1920)", "Square (1080x1080)", "Horizontal (1920x1080)"])
fps = st.selectbox("FPS", [24, 30, 60], index=1)

if format_choice == "Vertical (1080x1920)":
    w, h = 1080, 1920
elif format_choice == "Square (1080x1080)":
    w, h = 1080, 1080
else:
    w, h = 1920, 1080

if st.button("Generate Video"):
    lines = [l.strip() for l in script.split("\n") if l.strip()]
    if len(lines) == 0:
        st.error("Enter at least 1 line.")
        st.stop()

    st.write(f"Lines: {len(lines)}")
    st.write(f"Each cut: {total_duration/len(lines):.2f}s")

    final = build_video(lines, total_duration, w, h, font_size, fps)

    out_path = "quick_cuts_text.mp4"
    final.write_videofile(out_path, fps=fps, codec="libx264", audio=False, verbose=False, logger=None)

    with open(out_path, "rb") as f:
        st.download_button(
            "Download MP4",
            data=f,
            file_name="quick_cuts_text.mp4",
            mime="video/mp4",
        )
