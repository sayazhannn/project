import os, sys, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
from manifest import frames, UP

W, H, FPS, T = 1080, 1920, 25, 1.0
FB = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
FS = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
GREEN_D = (22, 74, 42)
GREEN = (52, 148, 74)
WASH = np.array((233, 244, 228), np.float32)
HERE = os.path.dirname(os.path.abspath(__file__))
SCHOOL_LOGO = UP + "aee4b044-image.jpg"

TEXT = {
    1: ['"Экологиялық тәрбие беруді ұйымдастыру үздік ұйымы" конкурсы',
        '"Қожаберген жырау атындағы 6 орта мектеп" КММ'],
    2: ['Жыл сайын сәуір айында мектебімізде "Экологиялық айлығы" өтеді.'],
    3: ['"Экосағаттар"'],
    4: ['Экологиялық флайерларды тарату', '"Қоқыс сұрыптау"', '"Табиғат дауысы"'],
    5: ['"Құстар күні" суреттер көрмесі', '"Құстар қанатты достар" ұяшықтарды жасау'],
    6: ['"Экология -өмірдің жүрегі" сыныптан тыс іс-шаралар'],
    7: ['Экологиялық ашық сабақтары'],
    8: ['"Жер сағаты" - электр энергияны үнемдеуге арналған жарықты өшіру акциясы'],
    9: ['"Экоәлем" кітап көрмесі'],
    10: ['"Табиғат саз әлемінде" музыкалық әндер байқауы'],
    11: ['"Қоқыстан өнерге" көрмесі'],
    12: ['"Green oases" макеттер сайысы'],
    13: ['ProEco - экологиялық жоба', 'Хабдул Асель 3 орын'],
    14: ['"Эко -дебат: vs әдет"'],
    15: ['"Таза Қазақстан" бағдарламасы аясында "Жасыл маршрут" акциясы'],
    16: ['"Таза Қазақстан" акциясы шеңберінде тазалық жұмыстар'],
    17: ['"Таза Қазақстан" экологиялық акциясын қолдау мақсатында "Ағаш егу" челлендждері'],
    18: ['"Таза бейсенбілік"'],
    19: ['"Таза Қазақстан" акциясы шеңберінде тұрмыстық қалдықтарды "Радуга" ЖШС қайта өңдеуге тапсырылады'],
    20: ['«Жасыл мектеп» ұлттық жобасы аясында мектебімізде жасыл бұрышты жасау басталды.'],
}

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sm(x):
    x = clamp(x); return x * x * (3 - 2 * x)

def duration(k, n):
    if k == 1: return 15
    if k == 20: return 12
    if n <= 2: return 11
    if n <= 4: return 12
    if n <= 8: return 13
    if n <= 13: return 14
    return 15

# ---------- image helpers ----------
def load(p, maxs=2200):
    im = ImageOps.exif_transpose(Image.open(p)).convert("RGB")
    if max(im.size) > maxs: im.thumbnail((maxs, maxs), Image.LANCZOS)
    return im

def rr_mask(w, h, r, ss=4):
    m = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, w * ss - 1, h * ss - 1), r * ss, fill=255)
    return m.resize((w, h), Image.LANCZOS)

def premult(rgba_img):
    a = np.asarray(rgba_img, np.uint8).copy()
    al = a[..., 3:4].astype(np.float32) / 255.0
    a[..., :3] = (a[..., :3].astype(np.float32) * al).astype(np.uint8)
    return a

def make_bg(im):
    a = np.asarray(im, np.uint8); h, w = a.shape[:2]
    tw = int(h * W / H)
    if tw <= w:
        x0 = (w - tw) // 2; a = a[:, x0:x0 + tw]
    else:
        th = int(w * H / W); y0 = (h - th) // 2; a = a[y0:y0 + th]
    s = cv2.resize(a, (108, 192), interpolation=cv2.INTER_AREA)
    s = cv2.GaussianBlur(s, (0, 0), 5)
    b = cv2.resize(s, (W, H), interpolation=cv2.INTER_CUBIC).astype(np.float32)
    out = 0.22 * b + 0.78 * WASH
    return np.clip(out, 0, 255).astype(np.uint8)

# ---------- layout ----------
def layout(ars, rw, rh, gap, caps):
    k = len(ars); best = None
    for mask in range(1 << (k - 1)):
        rows = []; cur = [0]
        for i in range(1, k):
            if mask >> (i - 1) & 1: rows.append(cur); cur = [i]
            else: cur.append(i)
        rows.append(cur)
        hs = [(rw - gap * (len(r) - 1)) / sum(ars[i] for i in r) for r in rows]
        tot = sum(hs) + gap * (len(rows) - 1)
        f = 1.0 if tot <= rh else (rh - gap * (len(rows) - 1)) / sum(hs)
        area = sum(math.log(ars[i] * (f * h) ** 2 + 1) for r, h in zip(rows, hs) for i in r)
        if best is None or area > best[0]: best = (area, rows, hs, f)
    _, rows, hs, f = best
    heights = [f * h for h in hs]
    tot = sum(heights) + gap * (len(rows) - 1)
    y = (rh - tot) / 2; boxes = [None] * k
    for r, h in zip(rows, heights):
        wrow = sum(ars[i] * h for i in r) + gap * (len(r) - 1)
        x = (rw - wrow) / 2
        for i in r:
            w = ars[i] * h; cw, ch = w, h
            m = min(1.0, caps[i][0] / w, caps[i][1] / h)
            cw, ch = w * m, h * m
            boxes[i] = (x + (w - cw) / 2, y + (h - ch) / 2, cw, ch)
            x += w + gap
        y += h + gap
    return boxes

AX, AY, AW, AH = 36, 270, 1008, 1610

def comp(layer, im, x, y):
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + im.width, layer.width), min(y + im.height, layer.height)
    if x1 <= x0 or y1 <= y0: return
    layer.alpha_composite(im.crop((x0 - x, y0 - y, x1 - x, y1 - y)), (x0, y0))

def make_layer(ims):
    layer = Image.new("RGBA", (AW, AH), (0, 0, 0, 0))
    ars = [i.width / i.height for i in ims]
    cm = 2.1 if len(ims) == 1 else 1.6
    caps = [(i.width * cm, i.height * cm) for i in ims]
    inset = 22
    boxes = layout(ars, AW - 2 * inset, AH - 2 * inset, 26, caps)
    b = 7
    for im, (x, y, w, h) in zip(ims, boxes):
        x = int(round(x + inset)); y = int(round(y + inset)); w = int(round(w)); h = int(round(h))
        pad = 70
        sh = Image.new("L", (w + 2 * pad, h + 2 * pad), 0)
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 10, pad + w, pad + h + 10), 22, fill=95)
        sh = sh.filter(ImageFilter.GaussianBlur(16))
        blk = Image.new("RGBA", sh.size, (20, 50, 30, 255)); blk.putalpha(sh)
        comp(layer, blk, x - pad, y - pad)
        card = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        ph = im.resize((w - 2 * b, h - 2 * b), Image.LANCZOS)
        card.paste(ph, (b, b))
        card.putalpha(rr_mask(w, h, 20))
        # inner photo rounding via full mask already; paste card
        layer.alpha_composite(card, (x, y))
    return premult(layer)

# ---------- text ----------
def wrap(text, font, maxw):
    words = text.split(" "); lines = []; cur = ""
    d = ImageDraw.Draw(Image.new("L", (4, 4)))
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw or not cur: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def fit_text(lines, maxw, maxh, smax=46, smin=26, lh=1.28):
    def go(sz):
        f = ImageFont.truetype(FB, sz); out = []
        for li, L in enumerate(lines): out += [(t, li) for t in wrap(L, f, maxw)]
        return f, out
    for sz in range(smax, 37, -2):          # prefer no wrapping
        f, out = go(sz)
        if len(out) == len(lines) and len(out) * sz * lh <= maxh: return f, sz, out
    for sz in range(smax, smin - 1, -2):
        f, out = go(sz)
        if len(out) * sz * lh <= maxh: return f, sz, out
    f, out = go(smin); return f, smin, out

HX, HY, HW, HH = 36, 36, 844, 210
SHM = 34

def panel_img(w, h, bar=True):
    im = Image.new("RGBA", (w + 2 * SHM, h + 2 * SHM), (0, 0, 0, 0))
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).rounded_rectangle((SHM, SHM + 8, SHM + w, SHM + h + 8), 30, fill=80)
    sh = sh.filter(ImageFilter.GaussianBlur(14))
    blk = Image.new("RGBA", im.size, (20, 60, 35, 255)); blk.putalpha(sh); im.alpha_composite(blk)
    p = Image.new("RGBA", (w, h), (255, 255, 255, 240))
    if bar:
        g = Image.new("RGBA", (14, h), GREEN + (255,)); p.paste(g, (0, 0))
    p.putalpha(rr_mask(w, h, 30).point(lambda v: int(v * 240 / 255)))
    im.alpha_composite(p, (SHM, SHM))
    return im

def build_header(lines):
    f, s, out = fit_text(lines, HW - 100, HH - 34, smax=44)
    d0 = ImageDraw.Draw(Image.new("L", (4, 4)))
    tw = max(d0.textlength(t, font=f) for t, _ in out)
    pw = int(min(HW, max(420, tw + 52 + 56)))
    lh = s * 1.28
    ph = int(max(120, lh * len(out) + 56))
    im = panel_img(pw, ph)
    y0 = SHM + (ph - lh * len(out)) / 2 - 2
    d = ImageDraw.Draw(im)
    for n, (t, li) in enumerate(out):
        col = GREEN if (len(lines) == 2 and li == 1 and lines[1].startswith("Хабдул")) else GREEN_D
        d.text((SHM + 52, y0 + n * lh), t, font=f, fill=col)
    return premult(im)

def build_title_panel(lines):
    pw = 960
    f1 = ImageFont.truetype(FB, 56); f2 = ImageFont.truetype(FB, 42)
    l1 = wrap(lines[0], f1, pw - 110); l2 = wrap(lines[1], f2, pw - 110)
    h1 = len(l1) * 56 * 1.3; h2 = len(l2) * 42 * 1.3
    ph = int(70 + h1 + 44 + h2 + 70)
    im = panel_img(pw, ph, bar=False)
    d = ImageDraw.Draw(im); y = SHM + 70
    for t in l1:
        d.text((SHM + pw / 2, y), t, font=f1, fill=GREEN_D, anchor="ma"); y += 56 * 1.3
    y += 14
    d.rounded_rectangle((SHM + pw / 2 - 90, y, SHM + pw / 2 + 90, y + 6), 3, fill=GREEN)
    y += 30
    for t in l2:
        d.text((SHM + pw / 2, y), t, font=f2, fill=GREEN, anchor="ma"); y += 42 * 1.3
    return premult(im), pw, ph

def build_logo():
    l = Image.open(os.path.join(HERE, "logo.png")).convert("RGBA")
    lh = 124; lw = int(l.width * lh / l.height)
    l = l.resize((lw, lh), Image.LANCZOS)
    return premult(l), lw, lh

def blend_premult(dst, src, x, y, a=1.0):
    h, w = src.shape[:2]
    x0, y0 = max(x, 0), max(y, 0); x1, y1 = min(x + w, dst.shape[1]), min(y + h, dst.shape[0])
    if x1 <= x0 or y1 <= y0 or a <= 0: return
    s = src[y0 - y:y1 - y, x0 - x:x1 - x].astype(np.float32)
    al = s[..., 3:4] / 255.0 * a
    dst[y0:y1, x0:x1] = dst[y0:y1, x0:x1] * (1 - al) + s[..., :3] * a

# ---------- scenes ----------
def split_pages(n, D):
    P = math.ceil(n / 3)
    cap = int((D - 0.6) // 2.8)
    P = max(1, min(P, cap))
    base, extra = divmod(n, P)
    sizes = [base + (1 if i < extra else 0) for i in range(P)]
    return sizes

class Scene: pass

def build_scene(k, F):
    sc = Scene(); sc.k = k; paths = F.get(k, [])
    sc.D = duration(k, len(paths))
    if k == 1:
        sc.kind = "title"
        pick = [F[j][0] for j in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 19)]
        cw, ch = 360, 384
        canvas = np.zeros((ch * 5, cw * 3, 3), np.uint8)
        for n, p in enumerate(pick):
            im = np.asarray(load(p, 1200)); h, w = im.shape[:2]
            sc_ = max(cw / w, ch / h)
            r = cv2.resize(im, (int(w * sc_) + 1, int(h * sc_) + 1), interpolation=cv2.INTER_AREA)
            y0 = (r.shape[0] - ch) // 2; x0 = (r.shape[1] - cw) // 2
            canvas[(n // 3) * ch:(n // 3 + 1) * ch, (n % 3) * cw:(n % 3 + 1) * cw] = r[y0:y0 + ch, x0:x0 + cw]
        canvas = cv2.resize(canvas, (W + 60, H + 107), interpolation=cv2.INTER_AREA)
        sc.collage = (0.34 * canvas.astype(np.float32) + 0.66 * WASH).astype(np.uint8)
        sc.panel, sc.pw, sc.ph = build_title_panel(TEXT[1])
        # school logo intro: cover-fit the portrait logo picture to the 9:16 frame
        sl = np.asarray(load(SCHOOL_LOGO, 2400)); sh_, sw_ = sl.shape[:2]
        k_ = max(W / sw_, H / sh_) * 1.0
        slr = cv2.resize(sl, (int(sw_ * k_) + 1, int(sh_ * k_) + 1), interpolation=cv2.INTER_AREA)
        x0 = (slr.shape[1] - W) // 2; y0 = (slr.shape[0] - H) // 2
        bgf = slr[y0:y0 + H, x0:x0 + W].astype(np.float32)
        sc.intro = bgf.astype(np.uint8)
        sc.header = None
        return sc
    sc.kind = "pages"
    sizes = split_pages(len(paths), sc.D); P = len(sizes)
    a = (sc.D + 0.6 * (P - 1)) / P
    sc.pages = []; idx = 0
    for p, sz in enumerate(sizes):
        ims = [load(q) for q in paths[idx:idx + sz]]; idx += sz
        pg = dict(ts=p * (a - 0.6), dur=a, layer=make_layer(ims), bg=make_bg(ims[0]), first=(p == 0))
        sc.pages.append(pg)
    sc.header = build_header(TEXT[k])
    return sc

def render_page(pg, t):
    u = clamp((t - pg["ts"]) / pg["dur"]); s = 1.0 + 0.03 * u
    e = sm((t - pg["ts"]) / 0.8); dy = (1 - e) * 18
    cx, cy = AW / 2, AH / 2
    M = np.float32([[s, 0, (1 - s) * cx], [0, s, (1 - s) * cy + dy]])
    w = cv2.warpAffine(pg["layer"], M, (AW, AH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    out = pg["bg"].astype(np.float32)
    reg = out[AY:AY + AH, AX:AX + AW]
    al = w[..., 3:4].astype(np.float32) / 255.0
    out[AY:AY + AH, AX:AX + AW] = reg * (1 - al) + w[..., :3].astype(np.float32)
    return out

def render_body(sc, t):
    if sc.kind == "title":
        # intro (school logo) 0..4.6s, crossfade to title 4.0..5.0
        z = 1.0 + 0.06 * clamp(t / 15)
        M = np.float32([[z, 0, (1 - z) * (W + 80) / 2 - 40 * 0], [0, z, (1 - z) * (H + 45) / 2]])
        col = cv2.warpAffine(sc.collage, np.float32([[z, 0, (1 - z) * W / 2 - 30 * z], [0, z, (1 - z) * H / 2 - 53 * z]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        wi = 1 - sm((t - 4.0) / 1.0)
        zi = 1.0 + 0.05 * clamp(t / 5.0)
        intro = cv2.warpAffine(sc.intro, np.float32([[zi, 0, (1 - zi) * W / 2], [0, zi, (1 - zi) * H / 2]]), (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        out = col * (1 - wi) + intro * wi
        pa = sm((t - 5.3) / 0.7) * (1 - sm((t - (sc.D - T - 1.6)) / 0.5))
        if pa > 0:
            blend_premult(out, sc.panel, (W - sc.panel.shape[1]) // 2, int((H - sc.panel.shape[0]) / 2 + 60 - (1 - pa) * 18), pa)
        return out
    cur = None
    pgs = [p for p in sc.pages if p["ts"] <= t + 1e-9] or [sc.pages[0]]
    p = pgs[-1]
    cur = render_page(p, t)
    if len(pgs) > 1:
        f = sm((t - p["ts"]) / 0.6)
        if f < 1:
            cur = render_page(pgs[-2], t) * (1 - f) + cur * f
    return cur

# ---------- timeline ----------
class Timeline:
    def __init__(self):
        self.F = frames()
        self.ks = list(range(1, 21))
        self.D = {k: duration(k, len(self.F.get(k, []))) for k in self.ks}
        self.S = {}; t = 0.0
        for k in self.ks:
            self.S[k] = t; t += self.D[k] - T
        self.total = self.S[20] + self.D[20]
        self.nframes = int(round(self.total * FPS))
        self.cache = {}
        self.logo, self.lw, self.lh = build_logo()

    def scene(self, k):
        if k not in self.cache:
            if len(self.cache) > 3: self.cache.pop(next(iter(self.cache)))
            self.cache[k] = build_scene(k, self.F)
        return self.cache[k]

    def frame(self, n):
        t = n / FPS
        out = np.full((H, W, 3), 255, np.float32)
        act = [k for k in self.ks if self.S[k] <= t <= self.S[k] + self.D[k]]
        for k in act:
            sc = self.scene(k); tl = t - self.S[k]
            body = render_body(sc, tl)
            w = sm(tl / T)
            out = out * (1 - w) + body * w
        last = self.S[20] + self.D[20]
        if t > last - T:
            wf = sm((last - t) / T); out = out * wf + 255 * (1 - wf)
        # headers
        for k in act:
            sc = self.scene(k); tl = t - self.S[k]
            if k == 1 or sc.header is None: continue
            ain = sm((tl - 0.45) / 0.5)
            aout = 1 - sm((tl - (self.D[k] - T)) / 0.45) if k < 20 else sm((self.D[k] - tl) / 0.8)
            a = ain * aout
            if a > 0:
                blend_premult(out, sc.header, HX - SHM, HY - SHM + int((1 - ain) * -12), a)
        # logo (+ white badge in the school-logo intro)
        la = sm(t / 1.0)
        lx = W - HX - self.lw; ly = HY
        if t < 5.2:
            ba = 1 - sm((t - 4.0) / 1.0)
            if ba > 0:
                badge = np.zeros((self.lh + 24, self.lw + 36, 4), np.uint8)
                m = np.asarray(rr_mask(badge.shape[1], badge.shape[0], 26))
                badge[..., :3] = 255; badge[..., 3] = (m * 0.92).astype(np.uint8)
                blend_premult(out, premult(Image.fromarray(badge, "RGBA")), lx - 18, ly - 12, ba * la)
        wfade = 1.0
        if t > last - T: wfade = sm((last - t) / T)
        blend_premult(out, self.logo, lx, ly, la * wfade)
        # progress bar
        bw = int(W * t / self.total)
        out[H - 6:H, :bw] = out[H - 6:H, :bw] * 0.25 + np.array(GREEN, np.float32) * 0.75
        return np.clip(out, 0, 255).astype(np.uint8)

TL = None
def worker(args):
    global TL
    idx, f0, f1, path = args
    if TL is None: TL = Timeline()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-g", "50", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(f0, f1):
        p.stdin.write(TL.frame(n).tobytes())
    p.stdin.close(); p.wait()
    return idx

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "info":
        tl = Timeline()
        for k in tl.ks: print(k, tl.D[k], round(tl.S[k], 1), len(tl.F.get(k, [])))
        print("total", tl.total, tl.nframes)
    elif mode == "preview":
        tl = Timeline(); os.makedirs("prev_v", exist_ok=True)
        for s in sys.argv[2:]:
            t = float(s); Image.fromarray(tl.frame(int(t * FPS))).save(f"prev_v/t{int(t * 10):04d}.jpg", quality=88)
    elif mode == "full":
        from multiprocessing import Pool
        tl = Timeline(); os.makedirs("chunks_v", exist_ok=True)
        step = 150; jobs = []
        for i, f0 in enumerate(range(0, tl.nframes, step)):
            jobs.append((i, f0, min(tl.nframes, f0 + step), f"chunks_v/c{i:03d}.mp4"))
        with Pool(4) as pool:
            for r in pool.imap_unordered(worker, jobs): print("done", r, flush=True)
        with open("chunks_v/list.txt", "w") as fh:
            for j in jobs: fh.write(f"file '{os.path.abspath(j[3])}'\n")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "chunks_v/list.txt", "-c", "copy", "video_v_silent.mp4"])
