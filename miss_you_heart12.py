import math
import random
import time
import turtle
import tkinter.font as tkf
from collections import defaultdict

# "I miss you" in many languages
PHRASES = [
    "I miss you",            # English
    "Te extraño",            # Spanish
    "Sinto sua falta",       # Portuguese
    "Tu me manques",         # French
    "Ich vermisse dich",     # German
    "Mi manchi",             # Italian
    "Ik mis je",             # Dutch
    "Ek mis jou",            # Afrikaans
    "Jag saknar dig",        # Swedish
    "Jeg savner deg",        # Norwegian
    "Kaipaan sinua",         # Finnish
    "Tęsknię za tobą",       # Polish
    "Chybíš mi",             # Czech
    "Hiányzol",              # Hungarian
    "Mi-e dor de tine",      # Romanian
    "Μου λείπεις",           # Greek
    "Я скучаю по тебе",      # Russian
    "Я сумую за тобою",      # Ukrainian
    "Seni özledim",          # Turkish
    "Aku rindu kamu",        # Indonesian
    "Miss kita",             # Filipino
    "Anh nhớ em",            # Vietnamese
    "คิดถึง",                  # Thai
    "我想你",                  # Chinese
    "会いたい",                 # Japanese
    "보고 싶어",                # Korean
    "मुझे तुम्हारी याद आती है",  # Hindi
    "Nakukumbuka",           # Swahili
    "Ngiyakukhumbula",       # Zulu
    "Nakuyewa",           # Nyanja
]
ENGLISH = "I miss you"
ENGLISH_OUTLINE = True      # True: the heart's edge words are all English

FONT = "Segoe UI"           # change on Mac/Linux if needed
BG = "#000000"
BASE = ["#f2452f", "#f94d37"]        # word colours
HOT = "#ffe6e0"                      # flash when a word first appears

FADE_IN = 0.6               # seconds: smooth fade-in
GLOW = 1.0                  # seconds: glow pulse after appearing
OUT_SPAN = 4.0              # outline is drawn during the first 4 s
REVEAL_SPAN = 13.5          # last word starts at ~13.5 s -> done at ~15 s

# ---------------------------------------------------------------- window
s = turtle.Screen()
s.setup(width=0.92, height=0.9)
s.bgcolor(BG)
s.title("Love Heart")
cv = s.getcanvas()
s.update()
W, H = s.window_width(), s.window_height()
rng = random.Random(11)


# ---------------------------------------------------------------- heart
def heart_raw(a):
    x = 16 * math.sin(a) ** 3
    y = (13 * math.cos(a) - 5 * math.cos(2 * a)
         - 2 * math.cos(3 * a) - math.cos(4 * a))
    return x, y


_raw = [heart_raw(2 * math.pi * i / 720) for i in range(720)]
_ymin = min(p[1] for p in _raw)
_ymax = max(p[1] for p in _raw)
SC = min(W * 0.90 / 32, H * 0.90 / (_ymax - _ymin))    # fit the window
MIDY = (_ymax + _ymin) / 2
u = SC / 22                                             # text scale factor


def heart(a):
    x, y = heart_raw(a)
    return x * SC, -(y - MIDY) * SC                     # canvas coords


POLY = [heart(2 * math.pi * i / 720) for i in range(720)]

# ---------------------------------------------------------------- helpers
_fonts, _w = {}, {}


def font_for(px):
    if px not in _fonts:
        _fonts[px] = tkf.Font(root=cv, family=FONT, size=-px, weight="bold")
    return _fonts[px]


def width(text, px):
    if (text, px) not in _w:
        _w[(text, px)] = font_for(px).measure(text)
    return _w[(text, px)]


def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


def mix(a, b, t):
    ca, cb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(round(ca[i] + (cb[i] - ca[i]) * t) for i in range(3))


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


def intervals(poly, y):
    xs = []
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            xs.append(xi + (y - yi) * (xj - xi) / (yj - yi))
        j = i
    xs.sort()
    return [(xs[k], xs[k + 1]) for k in range(0, len(xs) - 1, 2)]


def intersect(A, B):
    out, i, j = [], 0, 0
    while i < len(A) and j < len(B):
        lo, hi = max(A[i][0], B[j][0]), min(A[i][1], B[j][1])
        if lo < hi:
            out.append((lo, hi))
        if A[i][1] < B[j][1]:
            i += 1
        else:
            j += 1
    return out


# ---------------------------------------------------------------- rows of text
SIZES = [max(8, round(v * u)) for v in (11, 14, 17, 20)]
WEIGHTS = [0.30, 0.34, 0.28, 0.08]
GAP = max(6, round(9 * u))
PITCH = 21.8 * u
use = defaultdict(int)


INTERIOR = [p for p in PHRASES if not (ENGLISH_OUTLINE and p == ENGLISH)]


def pick_size(lo, hi):
    return rng.choices(SIZES[lo:hi + 1], WEIGHTS[lo:hi + 1])[0]


def edge_text():
    return ENGLISH if ENGLISH_OUTLINE else rng.choice(PHRASES)


def build_row(x0, x1, all_edge, tip):
    """Fill [x0, x1] with phrases, justified edge to edge.
    Returns (text, px, center_x, is_outline) tuples."""
    span = x1 - x0
    if span < 26 * u and not tip:
        return []
    items, remaining, recent = [], span, []

    if all_edge:                                    # whole row is outline
        while True:
            ph, px = edge_text(), pick_size(0, 2)
            w = width(ph, px)
            need = w + (GAP if items else 0)
            if need > remaining:
                px = SIZES[0]
                w = width(ph, px)
                need = w + (GAP if items else 0)
                if need > remaining:
                    break
            items.append([ph, px, w, True])
            remaining -= need
        if not items and tip:
            ph = edge_text()
            items.append([ph, SIZES[0], width(ph, SIZES[0]), True])
    else:
        lt, rt = edge_text(), edge_text()
        pl, pr = pick_size(0, 2), pick_size(0, 2)
        wl, wr = width(lt, pl), width(rt, pr)
        if span < wl + wr + GAP:                    # too narrow for two edges
            ph = edge_text()
            for px in reversed(SIZES):
                if width(ph, px) <= span:
                    items.append([ph, px, width(ph, px), True])
                    break
            if not items and tip:
                items.append([ph, SIZES[0], width(ph, SIZES[0]), True])
        else:
            remaining = span - wl - wr - GAP
            mid = []
            while True:                              # main pass: mixed sizes
                cands = []
                for _ in range(16):
                    ph = rng.choice(INTERIOR)
                    if ph in recent:
                        continue
                    px = rng.choices(SIZES, WEIGHTS)[0]
                    w = width(ph, px)
                    if w + GAP <= remaining:
                        cands.append((use[ph], rng.random(), ph, px, w))
                if not cands:
                    break
                cands.sort()
                _, _, ph, px, w = cands[0]
                mid.append([ph, px, w, False])
                remaining -= w + GAP
                use[ph] += 1
                recent = (recent + [ph])[-4:]
            small = SIZES[0]
            while True:                              # filler pass: small words
                fits = [(ph, width(ph, small)) for ph in INTERIOR
                        if ph not in recent and width(ph, small) + GAP <= remaining]
                if not fits:
                    break
                ph, w = rng.choice(fits)
                mid.append([ph, small, w, False])
                remaining -= w + GAP
                use[ph] += 1
                recent = (recent + [ph])[-4:]
            rng.shuffle(mid)
            items = [[lt, pl, wl, True]] + mid + [[rt, pr, wr, True]]

    if not items:
        return []
    n = len(items)
    gap = (span - sum(i[2] for i in items)) / (n - 1) if n > 1 else 0
    x = x0 if n > 1 else x0 + (span - items[0][2]) / 2
    out = []
    for ph, px, w, edge in items:
        out.append((ph, px, x + w / 2, edge))
        x += w + gap
    return out


def build_all():
    y_top = min(p[1] for p in POLY)
    y_bot = max(p[1] for p in POLY)
    y0, y1 = y_top + 16 * u, y_bot - 6 * u
    nrows = int((y1 - y0) // PITCH) + 1
    pitch = (y1 - y0) / (nrows - 1)
    words = []
    for r in range(nrows):
        y = y0 + r * pitch
        iv = intersect(intersect(intervals(POLY, y - 3 * u), intervals(POLY, y)),
                       intervals(POLY, y + 3 * u))
        tip = r >= nrows - 3
        if tip and not iv:
            iv = [(-1.0, 1.0)]
        all_edge = r == 0 or tip
        for x0, x1 in iv:
            for ph, px, cx, edge in build_row(x0, x1, all_edge, tip):
                words.append((ph, px, cx, y, edge))
    return words


# ---------------------------------------------------------------- animation
NEAR = [(-1.4, 0), (1.4, 0), (0, -1.4), (0, 1.4)]
FAR = [(-2.2, -2.2), (2.2, -2.2), (-2.2, 2.2), (2.2, 2.2)]
active = []


def spawn(word, now):
    text, px, x, y, _ = word
    f = font_for(px)
    halos = [cv.create_text(x + dx, y + dy, text=text, font=f, fill=BG)
             for dx, dy in NEAR + FAR]
    main = cv.create_text(x, y, text=text, font=f, fill=BG)
    active.append([now, main, halos, rng.choice(BASE), -1])


def set_halos(rec, e):
    base, halos = rec[3], rec[2]
    near, far = mix(BG, base, 0.30 * e), mix(BG, base, 0.10 * e)
    for i, h in enumerate(halos):
        cv.itemconfig(h, fill=near if i < 4 else far)


def animate(now):
    keep = []
    for rec in active:
        age = now - rec[0]
        base = rec[3]
        if age < FADE_IN:                                   # smooth fade-in
            cv.itemconfig(rec[1], fill=mix(BG, base, smooth(age / FADE_IN)))
            keep.append(rec)
        elif age < FADE_IN + GLOW:                          # glow pulse
            g = (age - FADE_IN) / GLOW
            cv.itemconfig(rec[1], fill=mix(base, HOT, 0.85 * math.sin(math.pi * g) ** 2))
            q = int(g * 8)
            if q != rec[4]:
                rec[4] = q
                set_halos(rec, smooth(g))
            keep.append(rec)
        else:                                               # settle
            cv.itemconfig(rec[1], fill=base)
            set_halos(rec, 1.0)
    active[:] = keep


words = build_all()
outline = sorted((w for w in words if w[4]),
                 key=lambda w: math.atan2(w[2], -w[3]) % (2 * math.pi))  # clockwise from notch
inner = [w for w in words if not w[4]]
rng.shuffle(inner)

sched = [(i / len(outline) * OUT_SPAN, w) for i, w in enumerate(outline)]
t_in = OUT_SPAN + 0.3
sched += [(t_in + j / len(inner) * (REVEAL_SPAN - t_in), w) for j, w in enumerate(inner)]

state = {"i": 0, "t0": None}


def tick():
    now = time.perf_counter()
    if state["t0"] is None:
        state["t0"] = now
    elapsed = now - state["t0"]
    while state["i"] < len(sched) and sched[state["i"]][0] <= elapsed:
        spawn(sched[state["i"]][1], now)
        state["i"] += 1
    animate(now)
    if state["i"] < len(sched) or active:
        cv.after(16, tick)


tick()
turtle.mainloop()
