#!/usr/bin/env python3
"""Сборка вертикального видео (1080x1920) серии «КЕЛІН» из кадров и озвучки.

Использование:
    python3 build_episode.py ASSETS_DIR OUT_DIR

ASSETS_DIR содержит:
    f01.png ... f12.png  - кадры сцен (если файла нет - ставится заметная заглушка)
    a01.mp3, a02a.mp3 ... - реплики (если файла нет - субтитр идёт без звука)

Результат: OUT_DIR/ep01.mp4
Когда появляются недостающие кадры или реплики, достаточно положить их в ASSETS_DIR
и запустить скрипт заново.
"""
import os
import subprocess
import sys
import textwrap

from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LEAD, GAP, TAIL = 0.35, 0.35, 0.55  # сек: до первой реплики, между репликами, после последней

# Сцены: кадр, подпись для заглушки, реплики. Реплика = (audio, [субтитры...], оценка длительности без аудио)
# Если у реплики несколько субтитров, они делят её длительность пропорционально длине текста.
SCENES = [
    dict(n=1, hint="Свадебный танец Аружан и Данияра",
         lines=[("a01", ["Два года вместе — и вот мы муж и жена!"], 3.6)]),
    dict(n=2, hint="Машина, огромный дом на юге",
         lines=[("a02a", ["Ого… какой большой дом."], 3.0),
                ("a02b", ["Наш. Привыкай."], 1.8)]),
    dict(n=3, hint="Порог дома, шашу, Гульмира встречает",
         lines=[("a03", ["Добро пожаловать, келін.\nТеперь это и твой дом."], 4.0)]),
    dict(n=4, hint="Знакомство: Әже, Серик, Мадина",
         lines=[("a04", ["Бала, дастархан жаса.\n(Дитя, накрывай стол.)"], 2.6)]),
    dict(n=5, hint="Гостиная, Мадина командует Аружан",
         lines=[("a05", ["Келін, чай принеси.\nИ мне тоже. Только горячий."], 4.0)]),
    dict(n=6, hint="Кухня после тоя, гора посуды",
         lines=[("a06a", ["У нас дома все делали вместе…"], 2.8),
                ("a06b", ["Здесь по-другому."], 1.8)]),
    dict(n=7, hint="Гульмира объясняет правила",
         lines=[("a07", ["Слушай внимательно.",
                         "Келін встаёт раньше всех.",
                         "Готовит завтрак на всю семью.",
                         "Убирает дом.",
                         "Встречает гостей.",
                         "Так принято."], 10.6)]),
    dict(n=8, hint="Аружан кивает, натянутая улыбка",
         lines=[("a08", ["Хорошо, шеше.",
                         "Ну… это же просто просьбы, да?"], 4.3)]),
    dict(n=9, hint="Ночь, Данияр обнимает Аружан, телефон 23:47",
         lines=[("a09a", ["Мама строгая, но добрая.\nПотерпи немного."], 3.6),
                ("a09b", ["Я справлюсь."], 1.8)]),
    dict(n=10, hint="Тёмный коридор, часы 5:58, тень",
         lines=[], silent=3.0),
    dict(n=11, hint="6:00, дверь, силуэт Гульмиры",
         lines=[("a11", ["Келін, сен әлі ұйықтап жатырсың ба?\n(Невестка, ты ещё спишь?)"], 3.0)]),
    dict(n=12, hint="Аружан застыла в шоке", lines=[], silent=2.6,
         end_card=["2 серия скоро", "Подписывайся, чтобы не пропустить ❤"]),
]


def font(size):
    return ImageFont.truetype(FONT_BOLD, size)


def cover(img):
    """Масштабирует с обрезкой до 1080x1920."""
    scale = max(W / img.width, H / img.height)
    img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
    x, y = (img.width - W) // 2, (img.height - H) // 2
    return img.crop((x, y, x + W, y + H))


def placeholder(n, hint):
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):  # тёплый бежево-золотой градиент
        t = y / H
        c = (round(236 - 40 * t), round(218 - 55 * t), round(188 - 70 * t))
        for x in range(W):
            px[x, y] = c
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((60, 60, W - 60, H - 60), 40, outline=(176, 138, 74), width=8)
    d.rounded_rectangle((90, 90, W - 90, H - 90), 30, outline=(176, 138, 74), width=3)
    d.text((W / 2, 640), f"КАДР {n:02d}", font=font(150), fill=(122, 90, 40), anchor="mm")
    y = 800
    for line in textwrap.wrap(hint, 26):
        d.text((W / 2, y), line, font=font(58), fill=(122, 90, 40), anchor="mm")
        y += 80
    d.text((W / 2, y + 80), "ЧЕРНОВИК: кадр ещё не сгенерирован", font=font(44),
           fill=(150, 60, 50), anchor="mm")
    return img


def wrap_block(draw, text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            test = (cur + " " + word).strip()
            if draw.textlength(test, font=fnt) <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def subtitle_png(text, path, y_bottom=1500, size=60):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    fnt = font(size)
    lines = wrap_block(d, text, fnt, W - 160)
    lh = size + 16
    y = y_bottom - lh * len(lines)
    for i, ln in enumerate(lines):
        small = ln.startswith("(")
        f = font(round(size * 0.78)) if small else fnt
        d.text((W / 2, y + i * lh), ln, font=f, fill=(255, 255, 255, 255),
               stroke_width=7, stroke_fill=(20, 12, 6, 255), anchor="ma")
    img.save(path)


def end_card_png(lines, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, H), fill=(20, 12, 6, 110))
    d.text((W / 2, 820), lines[0], font=font(110), fill=(255, 236, 190, 255),
           stroke_width=8, stroke_fill=(20, 12, 6, 255), anchor="mm")
    y = 980
    for ln in textwrap.wrap(lines[1], 22):
        d.text((W / 2, y), ln, font=font(58), fill=(255, 255, 255, 255),
               stroke_width=6, stroke_fill=(20, 12, 6, 255), anchor="mm")
        y += 80
    img.save(path)


def duration(path):
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path])
    return float(out.decode().strip())


def build_scene(sc, assets, tmp, idx):
    n = sc["n"]
    frame_path = os.path.join(assets, f"f{n:02d}.png")
    have_frame = os.path.exists(frame_path)
    base = cover(Image.open(frame_path).convert("RGB")) if have_frame else placeholder(n, sc["hint"])
    base_png = os.path.join(tmp, f"base{n:02d}.png")
    base.save(base_png)

    t = LEAD
    subs, auds = [], []  # subs: (png, start, end); auds: (mp3, start)
    for key, texts, est in sc["lines"]:
        mp3 = os.path.join(assets, key + ".mp3")
        has_audio = os.path.exists(mp3)
        dur = duration(mp3) if has_audio else est
        if has_audio:
            auds.append((mp3, t))
        total_chars = sum(len(s) for s in texts)
        s0 = t
        for j, s in enumerate(texts):
            part = dur * len(s) / total_chars
            png = os.path.join(tmp, f"sub{n:02d}_{len(subs)}.png")
            subtitle_png(s, png)
            subs.append((png, s0, s0 + part))
            s0 += part
        t += dur + GAP
    total = (t - GAP + TAIL) if sc["lines"] else sc.get("silent", 2.5)

    if sc.get("end_card"):
        png = os.path.join(tmp, f"end{n:02d}.png")
        end_card_png(sc["end_card"], png)
        subs.append((png, 0.5, total))

    nframes = max(1, round(total * FPS))
    zoom = (f"1+0.07*on/{nframes}" if idx % 2 == 0 else f"1.07-0.07*on/{nframes}")
    cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", base_png]
    for png, _, _ in subs:
        cmd += ["-loop", "1", "-framerate", str(FPS), "-t", f"{total:.3f}", "-i", png]
    cmd += ["-f", "lavfi", "-t", f"{total:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
    sil_idx = 1 + len(subs)
    for mp3, _ in auds:
        cmd += ["-i", mp3]

    fc = [f"[0:v]scale=1620:2880,zoompan=z='{zoom}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={FPS}[bg0]"]
    for i, (_, a, b) in enumerate(subs):
        fc.append(f"[bg{i}][{1 + i}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[bg{i + 1}]")
    fc.append(f"[bg{len(subs)}]format=yuv420p[vout]")
    labels = [f"[{sil_idx}:a]"]
    for k, (_, st) in enumerate(auds):
        ms = round(st * 1000)
        fc.append(f"[{sil_idx + 1 + k}:a]aformat=sample_rates=44100:channel_layouts=stereo,adelay={ms}|{ms}[a{k}]")
        labels.append(f"[a{k}]")
    fc.append("".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=first[aout]")

    out = os.path.join(tmp, f"scene{n:02d}.mp4")
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", "-t", f"{total:.3f}", out]
    subprocess.run(cmd, check=True)
    return out, have_frame, [k for k, _, _ in sc["lines"] if not os.path.exists(os.path.join(assets, k + ".mp3"))]


def main():
    assets, out_dir = sys.argv[1], sys.argv[2]
    tmp = os.path.join(out_dir, "tmp")
    os.makedirs(tmp, exist_ok=True)
    clips, missing_frames, missing_audio = [], [], []
    for idx, sc in enumerate(SCENES):
        clip, have_frame, miss = build_scene(sc, assets, tmp, idx)
        clips.append(clip)
        if not have_frame:
            missing_frames.append(sc["n"])
        missing_audio += miss
        print(f"сцена {sc['n']:02d}: кадр {'есть' if have_frame else 'ЗАГЛУШКА'}"
              + (f", нет озвучки: {miss}" if miss else ""))

    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")
    raw = os.path.join(tmp, "ep01_raw.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", raw], check=True)
    final = os.path.join(out_dir, "ep01.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-c:v", "copy",
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", final], check=True)
    print(f"\nГотово: {final} ({duration(final):.1f} с)")
    print(f"Заглушки вместо кадров: {missing_frames or 'нет'}; нет озвучки: {missing_audio or 'нет'}")


if __name__ == "__main__":
    main()
