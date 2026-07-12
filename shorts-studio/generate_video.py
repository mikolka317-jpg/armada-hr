#!/usr/bin/env python3
"""
Генератор вірусних Shorts/TikTok відео (9:16, 1080x1920, 30fps, ~33s).

Формат: кінетична типографіка "психологічні факти" — hook (0-3с) →
4 факти → CTA із зациклюванням. Одне відео рендериться в кількох мовах.

Використання:
    python3 generate_video.py [uk|ru|en|es|all] [output_dir]
"""
import subprocess
import sys
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FPS = 30
DURATION = 33.0

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

AMBER = (255, 179, 71)
WHITE = (245, 245, 250)
DIM = (200, 200, 215)

# (start, end, key) — hook, факти 1-4, CTA
SEGMENTS = [
    (0.0, 3.0, "hook"),
    (3.0, 9.5, "f1"),
    (9.5, 16.0, "f2"),
    (16.0, 22.5, "f3"),
    (22.5, 29.0, "f4"),
    (29.0, 33.0, "cta"),
]

# Текст у *зірочках* підсвічується акцентним кольором
CONTENT = {
    "uk": {
        "chip": "ФАКТ",
        "hook": "Твій мозок *обманює тебе* прямо зараз",
        "f1": "Ти пам'ятаєш не подію, а свій *останній спогад* про неї. Пам'ять переписується щоразу.",
        "f2": "Мозок ухвалює рішення *раніше*, ніж ти встигаєш його усвідомити.",
        "f3": "Більшу частину того, що ти «бачиш», мозок *домальовує сам*.",
        "f4": "Погане запам'ятовується *сильніше* за хороше. Це вбудований баг мозку.",
        "cta": "Подивись ще раз — мозок уже *переписав* це відео.\n→ Підпишись",
    },
    "ru": {
        "chip": "ФАКТ",
        "hook": "Твой мозг *обманывает тебя* прямо сейчас",
        "f1": "Ты помнишь не событие, а своё *последнее воспоминание* о нём. Память переписывается каждый раз.",
        "f2": "Мозг принимает решение *раньше*, чем ты успеваешь его осознать.",
        "f3": "Большую часть того, что ты «видишь», мозг *дорисовывает сам*.",
        "f4": "Плохое запоминается *сильнее* хорошего. Это встроенный баг мозга.",
        "cta": "Посмотри ещё раз — мозг уже *переписал* это видео.\n→ Подпишись",
    },
    "en": {
        "chip": "FACT",
        "hook": "Your brain is *lying to you* right now",
        "f1": "You don't remember the event — you remember your *last memory* of it. It rewrites every time.",
        "f2": "Your brain makes decisions *before* you become aware of them.",
        "f3": "Most of what you “see” is *filled in* by your brain.",
        "f4": "Bad moments stick *harder* than good ones. It's a built-in bug.",
        "cta": "Watch again — your brain already *rewrote* this video.\n→ Follow",
    },
    "es": {
        "chip": "DATO",
        "hook": "Tu cerebro te está *mintiendo* ahora mismo",
        "f1": "No recuerdas el evento: recuerdas tu *último recuerdo* de él. Se reescribe cada vez.",
        "f2": "Tu cerebro decide *antes* de que seas consciente.",
        "f3": "Gran parte de lo que “ves” la *inventa* tu cerebro.",
        "f4": "Lo malo se graba *más fuerte* que lo bueno. Es un bug de fábrica.",
        "cta": "Míralo otra vez: tu cerebro ya *reescribió* este video.\n→ Sígueme",
    },
}

WATERMARK = "MINDLOOP"


def ease_out_cubic(x):
    return 1 - (1 - x) ** 3


def parse_accents(text):
    """'a *b c* d' -> [('a ', False), ('b c', True), (' d', False)]"""
    parts = text.split("*")
    return [(p, i % 2 == 1) for i, p in enumerate(parts) if p]


def wrap_tokens(text, font, max_width):
    """Розбиває текст із *акцентами* на рядки слів [(word, accent), ...]."""
    lines = []
    for para in text.split("\n"):
        words = []
        for chunk, accent in parse_accents(para):
            for w in chunk.split(" "):
                if w:
                    words.append((w, accent))
        space = font.getlength(" ")
        cur, cur_w = [], 0.0
        for word, accent in words:
            ww = font.getlength(word)
            add = ww if not cur else ww + space
            if cur and cur_w + add > max_width:
                lines.append(cur)
                cur, cur_w = [(word, accent)], ww
            else:
                cur.append((word, accent))
                cur_w += add
        if cur:
            lines.append(cur)
    return lines


def render_text_block(text, size, max_width=900):
    """Рендерить центрований текстовий блок у RGBA-зображення."""
    font = ImageFont.truetype(FONT_BOLD, size)
    lines = wrap_tokens(text, font, max_width)
    lh = int(size * 1.32)
    img = Image.new("RGBA", (W, lh * len(lines) + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    space = font.getlength(" ")
    for i, line in enumerate(lines):
        total = sum(font.getlength(w) for w, _ in line) + space * (len(line) - 1)
        x = (W - total) / 2
        y = i * lh
        for word, accent in line:
            color = AMBER if accent else WHITE
            d.text((x, y), word, font=font, fill=color + (255,))
            x += font.getlength(word) + space
    return img


def render_chip(label):
    font = ImageFont.truetype(FONT_BOLD, 40)
    tw = font.getlength(label)
    pad_x, pad_y = 34, 16
    img = Image.new("RGBA", (int(tw + pad_x * 2), 40 + pad_y * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, img.width - 1, img.height - 1], radius=18,
                        fill=AMBER + (255,))
    d.text((pad_x, pad_y - 2), label, font=font, fill=(26, 26, 46, 255))
    return img


def build_background():
    """Статичний градієнт + віньєтка + легкий шум (проти бандингу)."""
    y = np.linspace(0, 1, H)[:, None, None]
    top = np.array([16, 16, 42], dtype=np.float64)
    bottom = np.array([44, 18, 66], dtype=np.float64)
    bg = top * (1 - y) + bottom * y
    bg = np.broadcast_to(bg, (H, W, 3)).copy()
    # віньєтка
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    bg *= (1 - 0.35 * np.clip(r - 0.4, 0, 1)[:, :, None])
    rng = np.random.default_rng(7)
    bg += rng.normal(0, 2.2, (H, W, 1))
    return np.clip(bg, 0, 255).astype(np.uint8)


def build_glow():
    """М'яка тепла пляма світла, що повільно дрейфує."""
    size = 1000
    yy, xx = np.mgrid[0:size, 0:size]
    r = np.sqrt((xx - size / 2) ** 2 + (yy - size / 2) ** 2) / (size / 2)
    alpha = np.clip(1 - r, 0, 1) ** 2 * 70
    glow = np.zeros((size, size, 4), dtype=np.uint8)
    glow[:, :, 0] = 255
    glow[:, :, 1] = 150
    glow[:, :, 2] = 60
    glow[:, :, 3] = alpha.astype(np.uint8)
    return Image.fromarray(glow, "RGBA")


def make_frames(lang):
    texts = CONTENT[lang]
    bg = build_background()
    glow = build_glow()
    wm_font = ImageFont.truetype(FONT_BOLD, 34)

    blocks = {}
    for start, end, key in SEGMENTS:
        size = 88 if key == "hook" else (66 if key != "cta" else 68)
        blocks[key] = render_text_block(texts[key], size)
    chips = {f"f{i}": render_chip(f"{texts['chip']} {i}/4") for i in range(1, 5)}

    total = int(DURATION * FPS)
    for n in range(total):
        t = n / FPS
        frame = Image.fromarray(bg, "RGB").convert("RGBA")
        # дрейф світлової плями
        gx = int(W / 2 + 270 * math.sin(2 * math.pi * t / 26) - 500)
        gy = int(650 + 320 * math.sin(2 * math.pi * t / 19 + 1.3) - 500)
        frame.alpha_composite(glow, (gx, gy))

        # активний сегмент
        for start, end, key in SEGMENTS:
            if not (start <= t < end):
                continue
            tr = t - start
            appear = ease_out_cubic(min(1.0, tr / 0.4))
            left = end - t
            vanish = min(1.0, left / 0.3) if key != "cta" else 1.0
            alpha = appear * vanish
            dy = int((1 - appear) * 60 - (1 - vanish) * 30)

            block = blocks[key]
            y0 = (H - block.height) // 2 + dy
            if key in chips:
                chip = chips[key]
                ca = chip.copy()
                ca.putalpha(ca.getchannel("A").point(lambda a: int(a * alpha)))
                frame.alpha_composite(ca, ((W - chip.width) // 2, y0 - 130))
            ba = block.copy()
            ba.putalpha(ba.getchannel("A").point(lambda a: int(a * alpha)))
            frame.alpha_composite(ba, (0, y0))

        d = ImageDraw.Draw(frame)
        # прогрес-бар зверху (утримує увагу до кінця)
        d.rectangle([0, 0, int(W * t / DURATION), 12], fill=AMBER + (255,))
        # вотермарка
        tw = wm_font.getlength(WATERMARK)
        d.text(((W - tw) / 2, H - 90), WATERMARK, font=wm_font,
               fill=DIM + (110,))

        yield frame.convert("RGB").tobytes()


# Ембіент-пад + м'який пульс (замінюйте трендовим звуком при публікації)
AUDIO_EXPR = (
    "0.14*sin(2*PI*110*t)*(0.7+0.3*sin(2*PI*0.21*t))"
    "+0.09*sin(2*PI*164.8*t)*(0.7+0.3*sin(2*PI*0.13*t+1))"
    "+0.07*sin(2*PI*220*t)*(0.6+0.4*sin(2*PI*0.17*t+2))"
    "+0.10*exp(-9*mod(t\\,2))*sin(2*PI*55*t)"
)


def render(lang, out_dir):
    out = os.path.join(out_dir, f"mindloop_{lang}.mp4")
    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", f"aevalsrc='{AUDIO_EXPR}':d={DURATION}:s=44100",
        "-c:v", "libx264", "-preset", "medium", "-crf", "21",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k",
        "-shortest", "-movflags", "+faststart", out,
    ]
    log_path = os.path.join(out_dir, f".ffmpeg_{lang}.log")
    with open(log_path, "wb") as log:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=log)
        try:
            for frame in make_frames(lang):
                proc.stdin.write(frame)
            proc.stdin.close()
        except BrokenPipeError:
            pass  # ffmpeg впав — причина буде в лог-файлі
        proc.wait()
    if proc.returncode != 0:
        with open(log_path) as f:
            tail = "".join(f.readlines()[-15:])
        raise RuntimeError(f"ffmpeg failed for {lang}:\n{tail}")
    os.remove(log_path)
    print(f"OK {out}")


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    os.makedirs(out_dir, exist_ok=True)
    langs = list(CONTENT) if which == "all" else [which]
    for lang in langs:
        render(lang, out_dir)
