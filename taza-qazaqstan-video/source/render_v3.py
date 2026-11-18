import os, sys, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
import render_v as R
from render_v import (W, H, load, rr_mask, premult, make_bg, layout, build_header, build_title_panel,
                      build_logo, blend_premult, TEXT, AX, AY, AW, AH, HX, HY, SHM, WASH, SCHOOL_LOGO)
from manifest import frames
from PIL import ImageFont
import render_v as _R

def build_header(lines):
    f, sz, out = _R.fit_text(lines, 744, 340, smax=62, smin=30)
    d0 = ImageDraw.Draw(Image.new("L", (4, 4)))
    tw = max(d0.textlength(t, font=f) for t, _ in out)
    pw = int(min(844, max(440, tw + 52 + 56)))
    lh = sz * 1.26
    ph = int(max(120, lh * len(out) + 56))
    im = _R.panel_img(pw, ph)
    y0 = SHM + (ph - lh * len(out)) / 2 - 2
    d = ImageDraw.Draw(im)
    for n, (t, li) in enumerate(out):
        col = _R.GREEN if (len(lines) == 2 and li == 1 and lines[1].startswith("Хабдул")) else _R.GREEN_D
        d.text((SHM + 52, y0 + n * lh), t, font=f, fill=col)
    return premult(im), ph

def build_title_panel(lines):
    pw = 1008
    f1 = ImageFont.truetype(_R.FB, 68); f2 = ImageFont.truetype(_R.FB, 52)
    l1 = _R.wrap(lines[0], f1, pw - 90); l2 = _R.wrap(lines[1], f2, pw - 90)
    h1 = len(l1) * 68 * 1.28; h2 = len(l2) * 52 * 1.28
    ph = int(64 + h1 + 44 + h2 + 64)
    im = _R.panel_img(pw, ph, bar=False)
    d = ImageDraw.Draw(im); y = SHM + 64
    for t in l1:
        d.text((SHM + pw / 2, y), t, font=f1, fill=_R.GREEN_D, anchor="ma"); y += 68 * 1.28
    y += 14
    d.rounded_rectangle((SHM + pw / 2 - 100, y, SHM + pw / 2 + 100, y + 7), 3, fill=_R.GREEN)
    y += 30
    for t in l2:
        d.text((SHM + pw / 2, y), t, font=f2, fill=_R.GREEN, anchor="ma"); y += 52 * 1.28
    return premult(im), pw, ph

def focus_of(im):
    """content-aware crop centre: weighted centroid of edge/detail energy, blended with the image centre"""
    a = np.asarray(im.convert("L"), np.float32); h, w = a.shape
    k = 200 / max(w, h)
    g = cv2.resize(a, (max(8, int(w * k)), max(8, int(h * k))), interpolation=cv2.INTER_AREA)
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0); gy = cv2.Sobel(g, cv2.CV_32F, 0, 1)
    e = cv2.GaussianBlur(np.sqrt(gx * gx + gy * gy), (0, 0), 4)
    e = e - e.min()
    if e.sum() < 1e-3: return 0.5, 0.5
    ys, xs = np.mgrid[0:e.shape[0], 0:e.shape[1]]
    cx = float((e * xs).sum() / e.sum()) / e.shape[1]; cy = float((e * ys).sum() / e.sum()) / e.shape[0]
    return 0.5 * 0.5 + 0.5 * cx, 0.5 * 0.5 + 0.5 * cy

def cover(im, tw, th, focus):
    iw, ih = im.size; s = max(tw / iw, th / ih)
    cw, ch = min(tw / s, iw), min(th / s, ih)
    x0 = max(0.0, min(focus[0] * iw - cw / 2, iw - cw)); y0 = max(0.0, min(focus[1] * ih - ch / 2, ih - ch))
    return im.resize((tw, th), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))

def fill_layout(ars, Wc, Hc, gap, fmax):
    k = len(ars); best = None
    for orient in (0, 1):
        a = ars if orient == 0 else [1 / x for x in ars]
        Wd, Hd = (Wc, Hc) if orient == 0 else (Hc, Wc)
        for mask in range(1 << (k - 1)):
            rows = []; cur = [0]
            for i in range(1, k):
                if mask >> (i - 1) & 1: rows.append(cur); cur = [i]
                else: cur.append(i)
            rows.append(cur)
            hs = [(Wd - gap * (len(r) - 1)) / sum(a[i] for i in r) for r in rows]
            f = (Hd - gap * (len(rows) - 1)) / sum(hs)
            crop = max(f, 1 / f)
            ar_ = [a[i] * (h * f) ** 2 * 1.0 for r, h in zip(rows, hs) for i in r]
            score = crop + 0.45 * math.log(max(ar_) / min(ar_))
            if best is None or score < best[0]: best = (score, orient, rows, hs, f, a, Wd, Hd)
    _, orient, rows, hs, f, a, Wd, Hd = best
    boxes = [None] * k
    if f >= 1 / fmax:
        fc = min(f, fmax); heights = [h * fc for h in hs]
        tot = sum(heights) + gap * (len(rows) - 1); y = (Hd - tot) / 2
        for r, h in zip(rows, heights):
            sa = sum(a[i] for i in r); avail = Wd - gap * (len(r) - 1); x = 0
            for i in r:
                w = avail * a[i] / sa; boxes[i] = (x, y, w, h); x += w + gap
            y += h + gap
    else:
        heights = [h * f for h in hs]
        tot = sum(heights) + gap * (len(rows) - 1); y = (Hd - tot) / 2
        for r, h in zip(rows, heights):
            wrow = sum(a[i] * h for i in r) + gap * (len(r) - 1); x = (Wd - wrow) / 2
            for i in r:
                w = a[i] * h; boxes[i] = (x, y, w, h); x += w + gap
            y += h + gap
    if orient == 1: boxes = [(y, x, h, w) for (x, y, w, h) in boxes]
    return boxes

FPS = 30
BPM = 95.0
BEAT = 60.0 / BPM
PH = 0.27           # time of the first beat in the track
T = BEAT            # slide transition = 1 beat
# beats per scene (sum = 338 -> 213.7 s)
NB = {1: 18, 2: 18, 3: 18, 4: 20, 5: 16, 6: 16, 7: 16, 8: 16, 9: 15, 10: 18, 11: 15, 12: 16, 13: 16,
      14: 15, 15: 15, 16: 18, 17: 20, 18: 16, 19: 20, 20: 16}
assert sum(NB.values()) == 338
INTRO_BEATS = 8

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def sm(x):
    x = clamp(x); return x * x * (3 - 2 * x)
def eoc(p): p = clamp(p); return 1 - (1 - p) ** 3
def eob(p):
    c1 = 1.70158; c3 = c1 + 1; p = clamp(p) - 1
    return 1 + c3 * p ** 3 + c1 * p ** 2

# ---------- helpers ----------
def zoom_warp(img, z, offx=0.0, offy=0.0):
    M = np.float32([[z, 0, (1 - z) * W / 2 - offx * z], [0, z, (1 - z) * H / 2 - offy * z]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)

def draw_tile(frame, arr, cx, cy, scale, angle, alpha):
    if alpha <= 0.002 or scale <= 0.01: return
    h, w = arr.shape[:2]
    w2, h2 = int(w * 1.3) + 2, int(h * 1.3) + 2
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    M[0, 2] += (w2 - w) / 2; M[1, 2] += (h2 - h) / 2
    wp = cv2.warpAffine(arr, M, (w2, h2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    blend_premult(frame, wp, int(round(cx - w2 / 2)), int(round(cy - h2 / 2)), alpha)

def slide_up(old, new, p):
    e = eoc(p)
    ny = int(round((1 - e) * H)); oy = int(round(e * 0.22 * H))
    if ny <= 0: return new
    out = np.empty_like(old)
    out[:H - oy] = old[oy:]; out[H - oy:] = old[-1:]
    out *= (1 - 0.28 * e)
    sh = 70; y0 = max(0, ny - sh)
    out[y0:ny] *= (1 - 0.32 * np.linspace(0, 1, ny - y0, dtype=np.float32))[:, None, None]
    out[ny:] = new[:H - ny]
    return out

rng = np.random.default_rng(3)
BK = [(rng.uniform(0, 270), rng.uniform(0, 480), rng.uniform(10, 34), rng.uniform(8, 22), rng.uniform(0, 6.28), int(rng.integers(0, 2))) for _ in range(12)]
def add_bokeh(out, t):
    m = np.zeros((480, 270), np.float32); g = np.zeros_like(m)
    for x0, y0, r, sp, ph, c in BK:
        y = (y0 - sp * t) % (480 + 2 * r) - r; x = x0 + 10 * math.sin(0.4 * t + ph)
        cv2.circle(g if c else m, (int(x), int(y)), int(r), 1.0, -1, cv2.LINE_AA)
    m = cv2.resize(cv2.GaussianBlur(m, (0, 0), 2.5), (W, H)); g = cv2.resize(cv2.GaussianBlur(g, (0, 0), 2.5), (W, H))
    out = out * (1 - 0.30 * m[..., None]) + 255 * 0.30 * m[..., None]
    out = out * (1 - 0.20 * g[..., None]) + np.array((120, 190, 130), np.float32) * 0.20 * g[..., None]
    return out

# ---------- tiles ----------
def make_tiles(ims, ay, ah):
    if len(ims) == 1 and ims[0].width >= 700:
        im0 = ims[0]; fx, fy = focus_of(im0)
        cw_, ch_ = im0.width * 0.62, im0.height * 0.62
        x0 = max(0, min(fx * im0.width - cw_ / 2, im0.width - cw_)); y0 = max(0, min(fy * im0.height - ch_ / 2, im0.height - ch_))
        ims = [im0, im0.crop((int(x0), int(y0), int(x0 + cw_), int(y0 + ch_)))]
    ars = [i.width / i.height for i in ims]
    inset = 14; gap = 22
    Wc, Hc = AW - 2 * inset, ah - 2 * inset
    boxes = fill_layout(ars, Wc, Hc, gap, 2.0 if len(ims) == 1 else 1.7)
    tiles = []; pad = 44; b = 7
    for k, (im, (x, y, w, h)) in enumerate(zip(ims, boxes)):
        w = int(round(w)); h = int(round(h)); x += inset; y += inset
        # limit extreme upscaling of small photos (shrink the card around its centre)
        sneed = max((w - 2 * b) / im.width, (h - 2 * b) / im.height)
        lim = 3.0 if len(ims) == 1 else 2.4
        if sneed > lim:
            m_ = lim / sneed; x += w * (1 - m_) / 2; y += h * (1 - m_) / 2; w = int(w * m_); h = int(h * m_)
        cv = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
        sh = Image.new("L", cv.size, 0)
        ImageDraw.Draw(sh).rounded_rectangle((pad, pad + 9, pad + w, pad + h + 9), 22, fill=95)
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        blk = Image.new("RGBA", cv.size, (20, 50, 30, 255)); blk.putalpha(sh); cv.alpha_composite(blk)
        card = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        card.paste(cover(im, w - 2 * b, h - 2 * b, focus_of(im)), (b, b))
        card.putalpha(rr_mask(w, h, 20))
        cv.alpha_composite(card, (pad, pad))
        tiles.append(dict(img=premult(cv), cx=AX + x + w / 2, cy=ay + y + h / 2, rot=(4.0 if k % 2 == 0 else -4.0)))
    return tiles

class Sc: pass

def build_page_scene(k, F):
    sc = Sc(); sc.k = k; paths = F[k]; B = NB[k]; N = len(paths)
    P = min(math.ceil(N / 3), B // 4) if N >= 16 else min(math.ceil(N / 3), max(1, B // 5))
    P = max(1, P)
    b0, e0 = divmod(B, P); beats = [b0 + (1 if i < e0 else 0) for i in range(P)]
    n0, m0 = divmod(N, P); sizes = [n0 + (1 if i < m0 else 0) for i in range(P)]
    sc.header, hph = build_header(TEXT[k])
    ay = HY + hph + 22; ah = 1886 - ay
    sc.pages = []; idx = 0; cum = 0
    for p in range(P):
        ims = [load(q) for q in paths[idx:idx + sizes[p]]]; idx += sizes[p]
        sc.pages.append(dict(start=cum * BEAT, tiles=make_tiles(ims, ay, ah), bg=make_bg(ims[0]).astype(np.float32)))
        cum += beats[p]
    return sc

def body_pages(sc, t, A):
    tl = t - A; P = len(sc.pages)
    bg = sc.pages[0]["bg"]
    for p in range(1, P):
        w = sm((tl - (sc.pages[p]["start"] - 0.28)) / 0.5)
        if w > 0: bg = bg * (1 - w) + sc.pages[p]["bg"] * w
    out = add_bokeh(bg.copy(), t)
    ph = (t - PH) % BEAT
    for p, pg in enumerate(sc.pages):
        s = pg["start"]; e = sc.pages[p + 1]["start"] if p + 1 < P else 1e9
        if tl < s or tl >= e: continue
        ex = sm((tl - (e - 0.28)) / 0.28) if e < 1e8 else 0.0
        for i, tile in enumerate(pg["tiles"]):
            u = (tl - (s + i * BEAT / 2)) / 0.5
            if u <= 0: continue
            pc = clamp(u)
            scale = 0.55 + 0.45 * eob(pc)
            ang = (1 - eoc(pc)) * tile["rot"]
            dy = (1 - eoc(pc)) * 70
            al = clamp(pc * 4)
            if u >= 1: scale *= 1 + 0.012 * math.exp(-9 * ph)
            scale *= 1 - 0.06 * ex; al *= 1 - ex
            draw_tile(out, tile["img"], tile["cx"], tile["cy"] + dy, scale, ang, al)
    return out

# ---------- title scene ----------
def build_title_scene(F):
    sc = Sc(); sc.k = 1
    pick = [F[j][0] for j in (2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17, 19)]
    cw, ch = 360, 384
    canvas = np.zeros((ch * 5, cw * 3, 3), np.uint8)
    for n, p in enumerate(pick):
        im = np.asarray(load(p, 1200)); h, w = im.shape[:2]
        k_ = max(cw / w, ch / h)
        r = cv2.resize(im, (int(w * k_) + 1, int(h * k_) + 1), interpolation=cv2.INTER_AREA)
        y0 = (r.shape[0] - ch) // 2; x0 = (r.shape[1] - cw) // 2
        canvas[(n // 3) * ch:(n // 3 + 1) * ch, (n % 3) * cw:(n % 3 + 1) * cw] = r[y0:y0 + ch, x0:x0 + cw]
    canvas = cv2.resize(canvas, (W + 60, H + 107), interpolation=cv2.INTER_AREA)
    sc.collage = (0.34 * canvas.astype(np.float32) + 0.66 * WASH).astype(np.uint8)
    sc.panel, _, _ = build_title_panel(TEXT[1])
    sl = np.asarray(load(SCHOOL_LOGO, 2400)); sh_, sw_ = sl.shape[:2]
    k_ = max(W / sw_, H / sh_)
    slr = cv2.resize(sl, (int(sw_ * k_) + 1, int(sh_ * k_) + 1), interpolation=cv2.INTER_AREA)
    x0 = (slr.shape[1] - W) // 2; y0 = (slr.shape[0] - H) // 2
    sc.intro = np.ascontiguousarray(slr[y0:y0 + H, x0:x0 + W])
    return sc

AT = PH + INTRO_BEATS * BEAT   # moment the title lands

def body_title(sc, t):
    pulse = 1 + 0.022 * math.exp(-7 * ((t - PH) % BEAT)) if t >= PH else 1.0
    z = (1.0 + 0.05 * clamp(t / 6.0)) * pulse
    out = zoom_warp(sc.intro, z)
    wf = sm(t / 0.5); out = out * wf + 255 * (1 - wf)
    p = (t - (AT - T)) / T
    if p > 0:
        z2 = 1.0 + 0.06 * clamp((t - (AT - T)) / 8.0)
        col = zoom_warp(sc.collage, z2, 30, 53)
        col = add_bokeh(col, t)
        out = slide_up(out, col, clamp(p))
        u = (t - AT) / 0.55
        if u > 0:
            pc = clamp(u)
            sc_ = 0.7 + 0.3 * eob(pc)
            if u >= 1: sc_ *= 1 + 0.01 * math.exp(-9 * ((t - PH) % BEAT))
            draw_tile(out, sc.panel, W / 2, H / 2 + 60 + (1 - eoc(pc)) * 40, sc_, (1 - eoc(pc)) * -3.0, clamp(pc * 3))
    return out

# ---------- timeline ----------
class Timeline:
    def __init__(self):
        self.F = frames(); self.A = {1: 0.0}
        self.A[2] = PH + NB[1] * BEAT
        for k in range(2, 20): self.A[k + 1] = self.A[k] + NB[k] * BEAT
        self.end = self.A[20] + NB[20] * BEAT
        self.nframes = int(round(self.end * FPS))
        self.cache = {}
        self.logo, self.lw, self.lh = build_logo()

    def scene(self, k):
        if k not in self.cache:
            if len(self.cache) > 3: self.cache.pop(next(iter(self.cache)))
            self.cache[k] = build_title_scene(self.F) if k == 1 else build_page_scene(k, self.F)
        return self.cache[k]

    def body(self, k, t):
        sc = self.scene(k)
        return body_title(sc, t) if k == 1 else body_pages(sc, t, self.A[k])

    def frame(self, n):
        t = n / FPS
        k = max(kk for kk in range(1, 21) if self.A[kk] <= t + 1e-9)
        cur = self.body(k, t)
        if k < 20 and t >= self.A[k + 1] - T:
            nxt = self.body(k + 1, t)
            cur = slide_up(cur, nxt, (t - (self.A[k + 1] - T)) / T)
        out = cur
        wfin = 1.0
        if t > self.end - 0.6:
            wfin = sm((self.end - t) / 0.6); out = out * wfin + 255 * (1 - wfin)
        # headers
        for kk in (k, k + 1):
            if kk < 2 or kk > 20: continue
            tl = t - self.A[kk]
            if tl < 0: continue
            sc = self.scene(kk)
            p = clamp(tl / 0.5)
            a = clamp(p * 2.5); dy = -(1 - eob(p)) * 90
            if kk < 20:
                te = t - (self.A[kk + 1] - T)
                if te > 0:
                    q = clamp(te / 0.25); a *= 1 - q; dy -= q * 50
            a *= wfin
            if a > 0.003:
                blend_premult(out, sc.header, HX - SHM, int(HY - SHM + dy), a)
        # Taza Qazaqstan logo: fixed size and position
        la = sm(t / 0.5) * wfin
        lx = W - HX - self.lw; ly = HY
        if t < AT:
            ba = 1.0
            badge = np.zeros((self.lh + 24, self.lw + 36, 4), np.uint8)
            m = np.asarray(rr_mask(badge.shape[1], badge.shape[0], 26))
            badge[..., :3] = 255; badge[..., 3] = (m * 0.92).astype(np.uint8)
            blend_premult(out, premult(Image.fromarray(badge, "RGBA")), lx - 18, ly - 12, ba * la)
        blend_premult(out, self.logo, lx, ly, la)
        bw = int(W * t / self.end)
        out[H - 6:H, :bw] = out[H - 6:H, :bw] * 0.25 + np.array(R.GREEN, np.float32) * 0.75
        return np.clip(out, 0, 255).astype(np.uint8)

TL = None
def worker(args):
    global TL
    idx, f0, f1, path = args
    if TL is None: TL = Timeline()
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p", "-g", "60", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for n in range(f0, f1): p.stdin.write(TL.frame(n).tobytes())
    p.stdin.close(); p.wait()
    return idx

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "info":
        tl = Timeline()
        for k in range(1, 21):
            D = (tl.A[k + 1] if k < 20 else tl.end) - (tl.A[k] - (T if k > 1 else 0))
            print(k, "A=%.2f" % tl.A[k], "len=%.2f" % D, len(tl.F.get(k, [])))
        print("end %.2f frames %d" % (tl.end, tl.nframes))
    elif mode == "preview":
        tl = Timeline(); os.makedirs("prev_v3", exist_ok=True)
        for s in sys.argv[2:]:
            t = float(s); Image.fromarray(tl.frame(int(round(t * FPS)))).save(f"prev_v3/t{int(t * 100):05d}.jpg", quality=88)
    elif mode == "full":
        from multiprocessing import Pool
        tl = Timeline(); os.makedirs("chunks_v3", exist_ok=True)
        step = 180; jobs = []
        for i, f0 in enumerate(range(0, tl.nframes, step)):
            jobs.append((i, f0, min(tl.nframes, f0 + step), f"chunks_v3/c{i:03d}.mp4"))
        with Pool(4) as pool:
            for r in pool.imap_unordered(worker, jobs): print("done", r, flush=True)
        with open("chunks_v3/list.txt", "w") as fh:
            for j in jobs: fh.write(f"file '{os.path.abspath(j[3])}'\n")
        subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "chunks_v3/list.txt", "-c", "copy", "video_v3_silent.mp4"])
