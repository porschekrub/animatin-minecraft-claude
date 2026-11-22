#!/usr/bin/env python3
"""Hand-built "epic fantasy" 3D models, written over the auto-generated ones in the "Lifelike 3D Items" pack.

Every model is made of boxes with its own painted pixel-art texture. Tiers climb from plain to legendary:
wood (grain, iron rivets) -> stone (chipped) -> iron (polished, blue gem) -> gold (ornate, swept guard, ruby) ->
diamond (crystal with glowing runes) -> netherite (dark, glowing ember cracks, amethyst). Glowing parts use Forge's
per-element light ("forge_data"), so they shine in the dark.

Models are built standing up (handle down, tip up) and turned onto the diagonal by their display transforms.

usage: gen_hand_models.py <pack dir> [names...]
"""
import json
import math
import os
import random
import sys

from PIL import Image

PACK = sys.argv[1]
ONLY = set(sys.argv[2:])
NS = "lifelikemotion"
TEX = 128
RES = 2  # texture pixels per design pixel: regions are painted at double detail

TIERS = ["wooden", "stone", "iron", "golden", "diamond", "netherite"]
METAL = {"wooden": (150, 108, 60), "stone": (128, 128, 128), "iron": (224, 226, 230), "golden": (252, 214, 74),
         "diamond": (86, 232, 216), "netherite": (70, 60, 66)}
TRIM = {"wooden": (92, 92, 98), "stone": (110, 86, 60), "iron": (150, 156, 166), "golden": (255, 236, 140),
        "diamond": (230, 236, 255), "netherite": (234, 178, 60)}
GEM = {"wooden": None, "stone": None, "iron": (90, 150, 255), "golden": (230, 40, 70), "diamond": (140, 255, 250),
       "netherite": (200, 90, 255)}
RUNE = {"diamond": (150, 255, 255), "netherite": (255, 140, 40)}
LEGENDARY = ("golden", "diamond", "netherite")
WOOD = (122, 86, 48)
DARK_WOOD = (78, 52, 30)
LEATHER = (96, 54, 34)
WRAP = (58, 36, 26)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- painting
class Painter:
    def __init__(self, seed):
        self.img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
        self.x = self.y = self.row = 0
        self.rng = random.Random(seed)

    def region(self, w, h, paint, bevel=True):
        """paints w x h design pixels at RES detail; bevelled: a lit top-left rim, a dark bottom-right rim and a
        thin dark outline, so every face of every part reads as a carved, shaded piece"""
        w, h = w * RES, h * RES
        if self.x + w > TEX:
            self.x, self.y, self.row = 0, self.y + self.row, 0
        x, y = self.x, self.y
        self.x += w
        self.row = max(self.row, h)
        for j in range(h):
            for i in range(w):
                c = paint(i, j, w, h, self.rng)
                if bevel:
                    # rims only along the sides, so long parts built from several boxes don't look banded
                    if i == 0 or i == w - 1:
                        c = shade(c, 0.68)
                    elif i == 1:
                        c = mix(c, (255, 255, 255), 0.22)
                    elif i == w - 2:
                        c = shade(c, 0.8)
                    c = shade(c, 1.04 - 0.08 * (j / h))
                self.img.putpixel((x + i, y + j), c + (255,))
        s = 16 / TEX
        return [x * s, y * s, (x + w) * s, (y + h) * s]


def metal(c, polish=1.0):
    hi, lo = mix(shade(c, 1.3), (255, 255, 255), 0.15 * polish), shade(c, 0.6)

    def f(i, j, w, h, r):
        t = i / max(w - 1, 1)
        base = mix(hi, c, min(t * 1.8, 1)) if t < 0.5 else mix(c, lo, (t - 0.5) * 2)
        if (i + j * 3) % 11 == 0 and polish > 0.8:
            base = mix(base, (255, 255, 255), 0.35)
        return shade(base, 0.95 + r.random() * 0.08)
    return f


def edge(c):
    hi = mix(shade(c, 1.4), (255, 255, 255), 0.45)
    return lambda i, j, w, h, r: shade(hi, 0.95 + r.random() * 0.07)


def flat(c, noise=0.08):
    return lambda i, j, w, h, r: shade(c, 1 - noise / 2 + r.random() * noise)


def stone_chips(c):
    def f(i, j, w, h, r):
        k = 0.75 + r.random() * 0.45
        if r.random() < 0.12:
            k *= 0.7
        return shade(c, k)
    return f


def wood(c):
    def f(i, j, w, h, r):
        g = 0.86 + 0.14 * math.sin(i * 1.9 + j * 0.15 + r.random() * 0.3)
        if j % 7 == 3 and r.random() < 0.3:
            g *= 0.82
        return shade(c, g * (0.96 + r.random() * 0.06))
    return f


def wrap(a, b):
    return lambda i, j, w, h, r: shade(a if ((i + j) // 2) % 2 == 0 else b, 0.94 + r.random() * 0.1)


def gem(c):
    def f(i, j, w, h, r):
        if j == 0:
            return mix(c, (255, 255, 255), 0.7)
        return shade(c, 1.15 if i + j < (w + h) / 2 else 0.75)
    return f


def cracks(base, glow):
    def f(i, j, w, h, r):
        if abs(math.sin(j * 0.55 + i * 1.3)) < 0.18 or abs(math.sin(j * 0.31 - i * 0.9 + 2)) < 0.12:
            return glow
        return metal(base, 0.6)(i, j, w, h, r)
    return f


def glow_grad(a, b):
    return lambda i, j, w, h, r: mix(a, b, j / max(h - 1, 1))


# ---------------------------------------------------------------- building
GLOW = {"block_light": 15, "sky_light": 15}


class Model:
    def __init__(self, name):
        self.name = name
        self.p = Painter(sum(map(ord, name)))
        self.els = []
        self.cache = {}
        self.dy = 0.0

    def style(self, key, paint, w=8, h=8):
        if key not in self.cache:
            # glowing parts stay pure light, no bevel
            self.cache[key] = self.p.region(w, h, paint, bevel=not key.startswith(("rune", "bladerune", "glow", "flame", "core", "glass", "fw", "spark", "line", "string")))
        return self.cache[key]

    def box(self, frm, to, uv, side=None, end=None, rot=None, glow=False):
        side = side or uv
        end = end or side
        faces = {f: {"uv": u, "texture": "#t"} for f, u in
                 (("north", uv), ("south", uv), ("east", side), ("west", side), ("up", end), ("down", end))}
        frm = (frm[0], frm[1] + self.dy, frm[2])
        to = (to[0], to[1] + self.dy, to[2])
        e = {"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": faces}
        if rot:
            axis, angle, o = rot
            assert angle in (-45, -22.5, 0, 22.5, 45), f"{self.name}: rotation {angle} not allowed"
            e["rotation"] = {"angle": angle, "axis": axis, "origin": [o[0], o[1] + self.dy, o[2]]}
        if glow:
            e["forge_data"] = GLOW
            e["shade"] = False
        self.els.append(e)

    def bar(self, x0, x1, y0, y1, half, uv, **kw):
        self.box((x0, y0, 8 - half), (x1, y1, 8 + half), uv, **kw)

    def write(self, display, model_name=None):
        name = model_name or self.name
        tex = f"item/hand/{name}"
        p = os.path.join(PACK, "assets", NS, "textures", tex + ".png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        self.p.img.save(p)
        model = {"gui_light": "front", "textures": {"t": f"{NS}:{tex}", "particle": f"{NS}:{tex}"},
                 "display": display, "elements": self.els}
        mp = os.path.join(PACK, "assets", NS, "models", "item3d", name + ".json")
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        with open(mp, "w") as f:
            json.dump(model, f, separators=(",", ":"))


def hand_display(turn=45, scale=0.68, tp_scale=0.85):
    return {
        "thirdperson_righthand": {"rotation": [0, -90, 55 + turn], "translation": [0, 4.0, 0.5], "scale": [tp_scale] * 3},
        "thirdperson_lefthand": {"rotation": [0, 90, -55 - turn], "translation": [0, 4.0, 0.5], "scale": [tp_scale] * 3},
        "firstperson_righthand": {"rotation": [0, -90, 25 + turn], "translation": [1.13, 3.2, 1.13], "scale": [scale] * 3},
        "firstperson_lefthand": {"rotation": [0, 90, -25 - turn], "translation": [1.13, 3.2, 1.13], "scale": [scale] * 3},
        "ground": {"rotation": [0, 0, turn], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, turn], "scale": [1, 1, 1]},
        "head": {"rotation": [0, 180, turn], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }


def blade_style(m, tier):
    c = METAL[tier]
    if tier == "wooden":
        return m.style("blade", wood(c), 8, 16), m.style("edge", wood(shade(c, 1.15)), 4, 16)
    if tier == "stone":
        return m.style("blade", stone_chips(c), 8, 16), m.style("edge", stone_chips(shade(c, 1.2)), 4, 16)
    if tier == "netherite":
        return m.style("blade", cracks(c, RUNE[tier]), 8, 16), m.style("edge", edge(c), 4, 16)
    return m.style("blade", metal(c), 8, 16), m.style("edge", edge(c), 4, 16)


def head_styles(m, tier):
    c = METAL[tier]
    if tier == "wooden":
        return m.style("head", wood(c), 8, 8), m.style("dark", wood(shade(c, 0.8)), 8, 8), m.style("edge", wood(shade(c, 1.2)), 4, 8)
    if tier == "stone":
        return (m.style("head", stone_chips(c), 8, 8), m.style("dark", stone_chips(shade(c, 0.8)), 8, 8),
                m.style("edge", stone_chips(shade(c, 1.15)), 4, 8))
    head = m.style("head", cracks(c, RUNE[tier]) if tier == "netherite" else metal(c), 8, 8)
    return head, m.style("dark", metal(shade(c, 0.78)), 8, 8), m.style("edge", edge(c), 4, 8)


def handle(m, tier, top, bottom=-3.2, half=0.65):
    w = m.style("handle", wood(DARK_WOOD if tier == "netherite" else WOOD), 4, 16)
    trim = m.style("trim", metal(TRIM[tier]), 4, 4)
    grip = m.style("grip", wrap(LEATHER, WRAP), 4, 8)
    m.box((8 - half, bottom, 8 - half), (8 + half, top, 8 + half), w)
    m.box((8 - half - 0.15, bottom + 0.8, 8 - half - 0.15), (8 + half + 0.15, bottom + 4.2, 8 + half + 0.15), grip)
    m.box((8 - half - 0.3, bottom - 0.5, 8 - half - 0.3), (8 + half + 0.3, bottom + 0.6, 8 + half + 0.3), trim)
    m.box((8 - half - 0.25, top - 1.4, 8 - half - 0.25), (8 + half + 0.25, top - 0.6, 8 + half + 0.25), trim)
    if GEM[tier]:
        m.box((7.55, bottom - 0.9, 7.55), (8.45, bottom - 0.4, 8.45), m.style("gem", gem(GEM[tier]), 2, 2), glow=tier in RUNE)


def inlay(m, tier, x0, x1, y0, y1, half):
    """a glowing rune strip on both faces of a head (diamond, netherite)"""
    if tier not in RUNE:
        return
    g = m.style("rune", glow_grad(RUNE[tier], shade(RUNE[tier], 0.8)), 2, 8)
    m.box((x0, y0, 8 - half - 0.06), (x1, y1, 8 + half + 0.06), g, glow=True)


def studs(m, tier, pts, half):
    if tier == "wooden":
        s = m.style("rivet", metal((150, 150, 158)), 2, 2)
    elif GEM[tier]:
        s = m.style("gem", gem(GEM[tier]), 2, 2)
    else:
        return
    for (x, y) in pts:
        m.box((x - 0.45, y - 0.45, 8 - half - 0.12), (x + 0.45, y + 0.45, 8 + half + 0.12), s, glow=tier in RUNE)


# ---------------------------------------------------------------- weapons and tools
def sword(tier):
    m = Model(f"{tier}_sword")
    m.dy = 3.5
    blade, edg = blade_style(m, tier)
    ridge = m.style("ridge", flat(shade(METAL[tier], 0.72)), 2, 16)
    trim = m.style("trim", metal(TRIM[tier]), 8, 4)
    grip = m.style("grip", wrap(LEATHER, WRAP), 4, 8)
    legendary = tier in LEGENDARY
    w = 1.25 if legendary else 1.0
    fuller = m.style("fuller", flat(shade(METAL[tier], 0.55), 0.05), 2, 16)
    # the blade tapers in steps toward a long point; the edges are thin, bright bevels on both sides
    segs = [(4.0, 8.0, w), (8.0, 12.0, w - 0.1), (12.0, 15.5, w - 0.25), (15.5, 17.6, w - 0.5), (17.6, 19.0, w - 0.8)]
    for y0, y1, hw in segs:
        m.box((8 - hw, y0, 7.3), (8 + hw, y1, 8.7), blade, side=edg)
        m.box((8 - hw - 0.8, y0 + 0.2, 7.68), (8 - hw, y1, 8.32), edg)
        m.box((8 + hw, y0 + 0.2, 7.68), (8 + hw + 0.8, y1, 8.32), edg)
    m.box((7.6, 19.0, 7.62), (8.4, 20.2, 8.38), edg)
    m.box((7.82, 20.2, 7.78), (8.18, 21.2, 8.22), edg)
    if tier in RUNE:
        rg = m.style("bladerune", glow_grad(RUNE[tier], shade(RUNE[tier], 0.75)), 2, 16)
        m.box((7.7, 5.0, 7.05), (8.3, 16.0, 8.95), rg, glow=True)
    elif tier in ("iron", "golden"):
        # a fuller: a groove down the middle of each face
        m.box((7.72, 4.6, 7.2), (8.28, 14.5, 8.8), fuller)
    else:
        m.box((7.7, 4.8, 7.05), (8.3, 16, 8.95), ridge)
    if legendary:
        for y in (5.0, 6.4):
            m.box((8 - w - 1.5, y, 7.75), (8 - w - 0.9, y + 0.7, 8.25), edg)
            m.box((8 + w + 0.9, y, 7.75), (8 + w + 1.5, y + 0.7, 8.25), edg)
    m.box((4.0, 3.1, 7.0), (12.0, 4.1, 9.0), trim)
    m.box((6.8, 2.4, 6.7), (9.2, 4.7, 9.3), trim)
    if legendary:
        m.box((2.9, 3.4, 7.1), (4.2, 5.8, 8.9), trim, rot=("z", 22.5, [4.0, 3.6, 8]))
        m.box((11.8, 3.4, 7.1), (13.1, 5.8, 8.9), trim, rot=("z", -22.5, [12.0, 3.6, 8]))
    else:
        m.box((3.3, 2.7, 6.8), (4.4, 4.6, 9.2), trim)
        m.box((11.6, 2.7, 6.8), (12.7, 4.6, 9.2), trim)
    if GEM[tier]:
        g = m.style("gem", gem(GEM[tier]), 2, 2)
        size = 1.3 if legendary else 1.0
        m.box((8 - size / 2, 3.55 - size / 2, 6.45), (8 + size / 2, 3.55 + size / 2, 9.55), g, glow=tier in RUNE)
    elif tier == "wooden":
        studs(m, tier, [(5.0, 3.6), (11.0, 3.6)], 1.0)
    m.box((7.35, -1.6, 7.35), (8.65, 2.5, 8.65), grip)
    m.box((6.9, -2.8, 6.9), (9.1, -1.6, 9.1), trim)
    if GEM[tier]:
        m.box((7.55, -3.3, 7.55), (8.45, -2.8, 8.45), m.style("gem", gem(GEM[tier]), 2, 2), glow=tier in RUNE)
    m.write(hand_display(20))


def pickaxe(tier):
    m = Model(f"{tier}_pickaxe")
    handle(m, tier, 13.6)
    head, dark, edg = head_styles(m, tier)
    m.box((6.5, 12.0, 6.85), (9.5, 15.8, 9.15), dark)
    studs(m, tier, [(8, 13.9)], 1.15)
    for sgn in (-1, 1):
        def bx(a, b, y0, y1, half, uv):
            xa, xb = 8 + sgn * a, 8 + sgn * b
            m.bar(min(xa, xb), max(xa, xb), y0, y1, half, uv)
        bx(1.5, 3.8, 12.8, 15.2, 0.9, head)
        bx(3.8, 5.6, 12.0, 14.6, 0.82, head)
        bx(5.6, 6.9, 11.0, 13.7, 0.7, head)
        bx(6.9, 7.7, 10.0, 12.5, 0.55, edg)
        bx(7.7, 8.25, 9.1, 11.0, 0.4, edg)
    inlay(m, tier, 2.5, 13.5, 13.6, 14.2, 0.9)
    m.write(hand_display())


def axe(tier):
    m = Model(f"{tier}_axe")
    handle(m, tier, 14.6)
    head, dark, edg = head_styles(m, tier)
    m.box((6.7, 10.6, 6.95), (9.3, 15.2, 9.05), dark)
    m.bar(9.3, 10.8, 11.0, 14.8, 0.85, head)
    m.bar(10.8, 12.2, 10.0, 15.6, 0.75, head)
    m.bar(12.2, 13.4, 8.8, 16.5, 0.65, head)
    m.bar(13.4, 14.3, 8.1, 17.1, 0.5, edg)
    m.bar(5.1, 6.7, 11.6, 14.2, 0.8, dark)
    if tier in LEGENDARY:
        m.bar(3.4, 5.1, 12.3, 13.5, 0.55, edg)
        m.bar(2.4, 3.4, 12.6, 13.2, 0.35, edg)
    else:
        m.bar(4.4, 5.1, 12.0, 13.8, 0.6, head)
    inlay(m, tier, 10.2, 13.2, 12.4, 13.2, 0.75)
    studs(m, tier, [(8, 12.9)], 1.1)
    m.write(hand_display())


def shovel(tier):
    m = Model(f"{tier}_shovel")
    handle(m, tier, 12.4)
    head, dark, edg = head_styles(m, tier)
    m.box((7.0, 11.0, 7.0), (9.0, 13.2, 9.0), dark)
    m.bar(6.2, 9.8, 13.2, 15.0, 0.55, head)
    m.bar(5.6, 10.4, 15.0, 17.6, 0.5, head)
    m.bar(6.0, 10.0, 17.6, 18.8, 0.45, edg)
    m.bar(7.0, 9.0, 18.8, 19.6, 0.4, edg)
    m.bar(7.6, 8.4, 13.4, 18.4, 0.75, dark)
    inlay(m, tier, 7.75, 8.25, 13.8, 18.0, 0.75)
    studs(m, tier, [(8, 12.1)], 1.05)
    m.write(hand_display())


def hoe(tier):
    m = Model(f"{tier}_hoe")
    handle(m, tier, 14.2)
    head, dark, edg = head_styles(m, tier)
    m.box((6.8, 12.6, 6.9), (9.2, 15.0, 9.1), dark)
    m.bar(9.2, 11.6, 13.0, 14.8, 0.75, head)
    m.bar(11.6, 13.6, 12.2, 14.4, 0.65, head)
    m.bar(13.6, 15.0, 10.8, 13.4, 0.55, edg)
    m.bar(14.4, 15.2, 9.4, 10.8, 0.4, edg)
    m.bar(5.4, 6.8, 13.2, 14.4, 0.65, dark)
    inlay(m, tier, 9.6, 13.4, 13.4, 13.9, 0.75)
    m.write(hand_display())


def torch(name="torch", flame=((255, 246, 170), (245, 130, 30)), core=(255, 252, 220)):
    m = Model(name)
    stick = m.style("stick", wood(shade(WOOD, 1.1)), 4, 12)
    cloth = m.style("cloth", wrap((140, 118, 84), (104, 84, 62)), 4, 4)
    band = m.style("band", metal((110, 110, 118)), 4, 4)
    fl = m.style("flame", glow_grad(*flame), 4, 8)
    cr = m.style("core", flat(core, 0.04), 2, 2)
    m.box((7.25, -3.0, 7.25), (8.75, 8.0, 8.75), stick)
    m.box((7.05, 1.0, 7.05), (8.95, 1.8, 8.95), band)
    m.box((6.8, 7.6, 6.8), (9.2, 10.2, 9.2), cloth)
    m.box((7.0, 10.2, 7.0), (9.0, 11.8, 9.0), fl, glow=True)
    m.box((7.3, 11.8, 7.3), (8.7, 13.0, 8.7), fl, glow=True)
    m.box((7.6, 13.0, 7.6), (8.4, 14.2, 8.4), cr, glow=True)
    m.write(hand_display(-15))


def fishing_rod(cast):
    name = "fishing_rod_cast" if cast else "fishing_rod"
    m = Model(name)
    rod = m.style("rod", wood(shade(WOOD, 1.05)), 4, 16)
    cork = m.style("cork", flat((196, 160, 110)), 4, 4)
    reel = m.style("reel", metal((190, 194, 200)), 4, 4)
    line = m.style("line", flat((235, 235, 235), 0.02), 2, 2)
    bob = m.style("bob", glow_grad((240, 60, 60), (250, 250, 250)), 2, 4)
    m.box((7.4, -3.0, 7.4), (8.6, 1.6, 8.6), cork)
    m.box((7.55, 1.6, 7.55), (8.45, 21.0, 8.45), rod, rot=("x", -22.5, [8, 1.6, 8]) if cast else None)
    m.box((8.6, 1.8, 7.0), (10.2, 3.6, 9.0), reel)
    if not cast:
        for y in (6, 11, 16, 20.4):
            m.box((7.3, y, 7.85), (8.7, y + 0.4, 8.15), reel)
        m.box((7.95, 2.6, 7.95), (8.05, 21.0, 8.05), line)
        m.box((6.6, 15.6, 7.6), (7.4, 16.6, 8.4), bob)
    m.write(hand_display(0), name)


def shears():
    m = Model("shears")
    blade = m.style("blade", metal((220, 222, 228)), 4, 12)
    edg = m.style("edge", edge((220, 222, 228)), 2, 12)
    grip = m.style("grip", flat((176, 40, 40)), 4, 4)
    pin = m.style("pin", metal((236, 190, 60)), 2, 2)
    for sgn in (-1, 1):
        m.box((7.4 + sgn * 0.4, 8.0, 7.4 + sgn * 0.2), (8.6 + sgn * 0.4, 16.0, 8.4 + sgn * 0.2), blade, side=edg,
              rot=("z", sgn * 22.5, [8, 8, 8]))
        m.box((6.6 + sgn * 1.4, 2.0, 7.4), (9.4 + sgn * 1.4, 6.2, 8.6), grip, rot=("z", -sgn * 22.5, [8, 8, 8]))
    m.box((7.5, 7.5, 7.1), (8.5, 8.5, 8.9), pin)
    m.write(hand_display(0))


def flint_and_steel():
    m = Model("flint_and_steel")
    steel = m.style("steel", metal((200, 204, 212)), 8, 4)
    flint = m.style("flint", stone_chips((60, 60, 66)), 4, 4)
    spark = m.style("spark", flat((255, 220, 120), 0.02), 2, 2)
    m.box((4.0, 4.0, 7.3), (10.0, 5.2, 8.7), steel)
    m.box((4.0, 5.2, 7.3), (5.2, 9.8, 8.7), steel)
    m.box((4.0, 9.8, 7.3), (10.0, 11.0, 8.7), steel)
    m.box((9.4, 9.0, 7.5), (10.4, 10.0, 8.5), steel)
    m.box((10.0, 5.0, 6.8), (13.6, 9.0, 9.2), flint)
    m.box((10.6, 8.6, 7.2), (12.8, 10.0, 8.8), flint)
    m.box((9.6, 9.8, 7.8), (10.2, 10.4, 8.2), spark, glow=True)
    m.write(hand_display(0))


def bow(pull):
    """pull: -1 resting, 0..2 drawn further. Upright: the riser in the middle, limbs up and down, string at +x."""
    name = "bow" if pull < 0 else f"bow_pulling_{pull}"
    m = Model(name)
    limb = m.style("limb", wood(DARK_WOOD), 4, 16)
    tip = m.style("tip", metal((236, 190, 60)), 2, 4)
    grip = m.style("grip", wrap(LEATHER, WRAP), 4, 4)
    string = m.style("string", flat((240, 240, 240), 0.02), 2, 2)
    arrow = m.style("arrow", wood((170, 140, 100)), 2, 8)
    head = m.style("head", metal((190, 194, 200)), 2, 2)
    fletch = m.style("fletch", flat((240, 240, 240)), 2, 2)
    gemv = m.style("gem", gem((90, 220, 120)), 2, 2)
    draw = 0 if pull < 0 else 1.2 + pull * 1.2
    flex = 1.0 + (0 if pull < 0 else 0.35 * (pull + 1))
    m.box((6.8, 6.0, 7.1), (8.6, 10.0, 8.9), grip)
    m.box((6.5, 7.5, 7.5), (6.8, 8.5, 8.5), gemv, glow=True)
    # each limb a stepped arc bending away from the string (more when drawn), with recurved gold tips
    steps = [(0.0, 1.6), (-0.35, 1.6), (-0.9, 1.5), (-1.6, 1.5), (-2.5, 1.4)]
    for sgn in (1, -1):
        y = 10.0 if sgn > 0 else 6.0
        for dx, ln in steps:
            x = 7.2 + dx * flex
            y0, y1 = (y, y + ln) if sgn > 0 else (y - ln, y)
            m.box((x, y0, 7.35), (x + 1.2, y1, 8.65), limb)
            y = y1 if sgn > 0 else y0
        tx = 7.2 + steps[-1][0] * flex
        ty0, ty1 = (y, y + 1.6) if sgn > 0 else (y - 1.6, y)
        m.box((tx + 0.6, ty0, 7.5), (tx + 1.5, ty1, 8.5), tip)
    span_top, span_bot = 10.0 + sum(l for _, l in steps) + 1.2, 6.0 - sum(l for _, l in steps) - 1.2
    sx = 7.2 + steps[-1][0] * flex + 1.2 + draw
    m.box((sx, span_bot, 7.95), (sx + 0.15, span_top, 8.05), string)
    if pull >= 0:
        m.box((sx - 13.0, 7.85, 7.85), (sx, 8.15, 8.15), arrow)
        m.box((sx - 14.2, 7.6, 7.6), (sx - 13.0, 8.4, 8.4), head)
        m.box((sx - 1.6, 7.3, 7.95), (sx - 0.2, 8.7, 8.05), fletch)
    d = hand_display(0)
    for k in ("firstperson_righthand", "firstperson_lefthand"):
        s = 1 if "right" in k else -1
        d[k] = {"rotation": [0, -30 * s, 10 * s], "translation": [-1 * s, 2.5, 0], "scale": [0.7] * 3}
    for k in ("thirdperson_righthand", "thirdperson_lefthand"):
        s = 1 if "right" in k else -1
        d[k] = {"rotation": [0, -90 * s, 0], "translation": [0, 2, 1], "scale": [0.8] * 3}
    m.write(d, name)


def crossbow(state):
    name = "crossbow" if state == "standby" else f"crossbow_{state}"
    m = Model(name)
    stock = m.style("stock", wood(DARK_WOOD), 4, 16)
    metalv = m.style("metal", metal((170, 174, 182)), 8, 4)
    limb = m.style("limb", wood(WOOD), 8, 4)
    string = m.style("string", flat((236, 236, 236), 0.02), 2, 2)
    bolt = m.style("bolt", wood((170, 140, 100)), 2, 8)
    gemv = m.style("gem", gem((230, 40, 70)), 2, 2)
    m.box((7.2, -2.0, 7.2), (8.8, 14.0, 8.8), stock)
    m.box((7.0, 9.0, 6.8), (9.0, 14.6, 9.2), metalv)
    m.box((1.0, 12.4, 7.4), (15.0, 13.8, 8.6), limb)
    m.box((0.4, 12.2, 7.2), (1.4, 14.0, 8.8), metalv)
    m.box((14.6, 12.2, 7.2), (15.6, 14.0, 8.8), metalv)
    m.box((7.5, 6.0, 6.4), (8.5, 7.0, 7.2), gemv, glow=True)
    pulled = {"standby": 0, "pulling_0": 1.5, "pulling_1": 3.0, "pulling_2": 4.5}.get(state, 4.8)
    sy = 12.9 - pulled
    m.box((1.2, sy, 7.95), (14.8, sy + 0.15, 8.05), string)
    if state in ("arrow", "firework"):
        m.box((7.85, sy, 7.85), (8.15, 17.0, 8.15), bolt)
        if state == "firework":
            fw = m.style("fw", glow_grad((240, 60, 60), (250, 200, 60)), 2, 4)
            m.box((7.4, 15.6, 7.4), (8.6, 18.0, 8.6), fw, glow=True)
    d = hand_display(0)
    for k in ("firstperson_righthand", "firstperson_lefthand"):
        s = 1 if "right" in k else -1
        d[k] = {"rotation": [-80, 0, -8 * s], "translation": [0, 0, -2], "scale": [0.65] * 3}
    for k in ("thirdperson_righthand", "thirdperson_lefthand"):
        d[k] = {"rotation": [-90, 0, 0], "translation": [0, 3, -1], "scale": [0.8] * 3}
    m.write(d, name)


def trident():
    m = Model("trident_in_hand")
    shaft = m.style("shaft", metal((96, 156, 150)), 4, 16)
    prong = m.style("prong", metal((150, 220, 210)), 4, 8)
    edg = m.style("edge", edge((150, 220, 210)), 2, 8)
    glowc = m.style("glow", glow_grad((160, 255, 245), (60, 200, 200)), 2, 8)
    m.box((7.4, -14.0, 7.4), (8.6, 14.0, 8.6), shaft)
    m.box((6.8, -15.0, 6.8), (9.2, -13.6, 9.2), prong)
    m.box((5.0, 13.4, 7.2), (11.0, 15.0, 8.8), prong)
    for x in (5.0, 7.4, 9.8):
        top = 20.0 + (1.4 if x == 7.4 else 0)
        m.box((x, 15.0, 7.4), (x + 1.2, top, 8.6), prong, side=edg)
        m.box((x + 0.3, top, 7.7), (x + 0.9, top + 1.6, 8.3), edg)
    m.box((7.7, 2.0, 7.15), (8.3, 12.0, 8.85), glowc, glow=True)
    d = hand_display(25, 0.42, 0.7)
    for k in ("firstperson_righthand", "firstperson_lefthand"):
        d[k]["translation"] = [0, 9, -2]
    m.write(d)


def shield(blocking):
    name = "shield_blocking" if blocking else "shield"
    m = Model(name)
    plank = m.style("plank", wood(WOOD), 16, 16)
    rim = m.style("rim", metal((170, 174, 182)), 4, 16)
    boss = m.style("boss", metal((236, 190, 60)), 4, 4)
    strap = m.style("strap", wrap(LEATHER, WRAP), 4, 4)
    gemv = m.style("gem", gem((90, 150, 255)), 2, 2)
    m.box((2.0, 2.0, 7.0), (14.0, 18.0, 8.4), plank)
    m.box((1.4, 1.4, 6.8), (14.6, 2.4, 8.6), rim)
    m.box((1.4, 17.6, 6.8), (14.6, 18.6, 8.6), rim)
    m.box((1.4, 2.4, 6.8), (2.4, 17.6, 8.6), rim)
    m.box((13.6, 2.4, 6.8), (14.6, 17.6, 8.6), rim)
    m.box((6.4, 8.4, 6.2), (9.6, 11.6, 7.0), boss)
    m.box((7.4, 9.4, 5.8), (8.6, 10.6, 6.2), gemv, glow=True)
    m.box((7.0, 5.0, 8.4), (9.0, 15.0, 9.4), strap)
    d = {
        "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [10, 6, -4], "scale": [1, 1, 1]},
        "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [10, 6, 12], "scale": [1, 1, 1]},
        "firstperson_righthand": {"rotation": [0, 180, 5], "translation": [-10, 2, -10], "scale": [1.25] * 3},
        "firstperson_lefthand": {"rotation": [0, 180, 5], "translation": [10, 0, -10], "scale": [1.25] * 3},
        "ground": {"rotation": [0, 0, 0], "translation": [2, 4, 2], "scale": [0.25] * 3},
        "fixed": {"rotation": [0, 180, 0], "translation": [-2, 4, -5], "scale": [0.5] * 3},
        "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65] * 3},
    }
    if blocking:
        d["thirdperson_righthand"] = {"rotation": [45, 135, 0], "translation": [3.51, 11, -2], "scale": [1, 1, 1]}
        d["thirdperson_lefthand"] = {"rotation": [45, 135, 0], "translation": [13.51, 3, 5], "scale": [1, 1, 1]}
        d["firstperson_righthand"] = {"rotation": [0, 180, -5], "translation": [-15, 5, -11], "scale": [1.25] * 3}
        d["firstperson_lefthand"] = {"rotation": [0, 180, -5], "translation": [5, 5, -11], "scale": [1.25] * 3}
    m.write(d, name)


def lantern(name="lantern", flame=((255, 220, 120), (240, 150, 40))):
    m = Model(name)
    frame = m.style("frame", metal((70, 72, 80)), 4, 8)
    glass = m.style("glass", glow_grad(*flame), 8, 8)
    cap = m.style("cap", metal((90, 92, 100)), 8, 4)
    ring = m.style("ring", metal((120, 122, 130)), 2, 4)
    m.box((5.0, 2.0, 5.0), (11.0, 9.0, 11.0), glass, glow=True)
    for x, z in ((4.6, 4.6), (10.4, 4.6), (4.6, 10.4), (10.4, 10.4)):
        m.box((x, 1.6, z), (x + 1.0, 9.4, z + 1.0), frame)
    m.box((4.4, 0.6, 4.4), (11.6, 2.0, 11.6), cap)
    m.box((4.4, 9.0, 4.4), (11.6, 10.4, 11.6), cap)
    m.box((6.0, 10.4, 6.0), (10.0, 11.4, 10.0), cap)
    m.box((7.4, 11.4, 7.6), (8.6, 14.0, 8.4), ring)
    m.box((7.0, 13.6, 7.6), (9.0, 14.4, 8.4), ring)
    d = hand_display(0, 0.55, 0.6)
    for k in ("firstperson_righthand", "firstperson_lefthand"):
        d[k]["rotation"] = [0, d[k]["rotation"][1], 0]
        d[k]["translation"] = [0, 4.5, 0]
    m.write(d)


# ---------------------------------------------------------------- the game's item models, pointed at ours
def item_json(name, base, gui_tex, ovr=None):
    mdir = os.path.join(PACK, "assets", "minecraft", "models", "item")
    os.makedirs(mdir, exist_ok=True)
    d = {"loader": "forge:separate_transforms", "textures": {"particle": gui_tex},
         "base": {"parent": f"{NS}:item3d/{base}"},
         "perspectives": {"gui": {"parent": "minecraft:item/generated", "textures": {"layer0": gui_tex}}}}
    if ovr:
        d["overrides"] = ovr
    with open(os.path.join(mdir, name + ".json"), "w") as f:
        json.dump(d, f, separators=(",", ":"))


def raw_json(name, d):
    mdir = os.path.join(PACK, "assets", "minecraft", "models", "item")
    with open(os.path.join(mdir, name + ".json"), "w") as f:
        json.dump(d, f, separators=(",", ":"))


def link_bow():
    for p in range(3):
        item_json(f"bow_pulling_{p}", f"bow_pulling_{p}", f"minecraft:item/bow_pulling_{p}")
    item_json("bow", "bow", "minecraft:item/bow", [
        {"predicate": {"pulling": 1}, "model": "minecraft:item/bow_pulling_0"},
        {"predicate": {"pulling": 1, "pull": 0.65}, "model": "minecraft:item/bow_pulling_1"},
        {"predicate": {"pulling": 1, "pull": 0.9}, "model": "minecraft:item/bow_pulling_2"}])


def link_crossbow():
    for s in ("pulling_0", "pulling_1", "pulling_2", "arrow", "firework"):
        item_json(f"crossbow_{s}", f"crossbow_{s}", f"minecraft:item/crossbow_{s}")
    item_json("crossbow", "crossbow", "minecraft:item/crossbow_standby", [
        {"predicate": {"pulling": 1}, "model": "minecraft:item/crossbow_pulling_0"},
        {"predicate": {"pulling": 1, "pull": 0.58}, "model": "minecraft:item/crossbow_pulling_1"},
        {"predicate": {"pulling": 1, "pull": 1.0}, "model": "minecraft:item/crossbow_pulling_2"},
        {"predicate": {"charged": 1}, "model": "minecraft:item/crossbow_arrow"},
        {"predicate": {"charged": 1, "firework": 1}, "model": "minecraft:item/crossbow_firework"}])


def link_rod():
    item_json("fishing_rod_cast", "fishing_rod_cast", "minecraft:item/fishing_rod_cast")
    item_json("fishing_rod", "fishing_rod", "minecraft:item/fishing_rod",
              [{"predicate": {"cast": 1}, "model": "minecraft:item/fishing_rod_cast"}])


def link_trident():
    raw_json("trident_in_hand", {"parent": f"{NS}:item3d/trident_in_hand", "textures": {"particle": "minecraft:item/trident"}})


def link_shield():
    # (banner patterns are not shown on this shield)
    raw_json("shield_blocking", {"parent": f"{NS}:item3d/shield_blocking"})
    raw_json("shield", {"parent": f"{NS}:item3d/shield", "overrides": [{"predicate": {"blocking": 1}, "model": "minecraft:item/shield_blocking"}]})


JOBS = {}


def job(name, make, link=None):
    JOBS[name] = (make, link)


for t in TIERS:
    for kind, fn in (("sword", sword), ("pickaxe", pickaxe), ("axe", axe), ("shovel", shovel), ("hoe", hoe)):
        job(f"{t}_{kind}", lambda t=t, fn=fn: fn(t), lambda n=f"{t}_{kind}": item_json(n, n, f"minecraft:item/{n}"))
job("torch", torch, lambda: item_json("torch", "torch", "minecraft:block/torch"))
job("soul_torch", lambda: torch("soul_torch", ((150, 250, 255), (40, 180, 220)), (220, 255, 255)),
    lambda: item_json("soul_torch", "soul_torch", "minecraft:block/soul_torch"))
job("lantern", lantern, lambda: item_json("lantern", "lantern", "minecraft:item/lantern"))
job("soul_lantern", lambda: lantern("soul_lantern", ((150, 250, 255), (40, 180, 220))),
    lambda: item_json("soul_lantern", "soul_lantern", "minecraft:item/soul_lantern"))
job("shears", shears, lambda: item_json("shears", "shears", "minecraft:item/shears"))
job("flint_and_steel", flint_and_steel, lambda: item_json("flint_and_steel", "flint_and_steel", "minecraft:item/flint_and_steel"))
job("fishing_rod", lambda: (fishing_rod(False), fishing_rod(True)), link_rod)
job("bow", lambda: [bow(p) for p in (-1, 0, 1, 2)], link_bow)
job("crossbow", lambda: [crossbow(s) for s in ("standby", "pulling_0", "pulling_1", "pulling_2", "arrow", "firework")], link_crossbow)
job("trident", trident, link_trident)
job("shield", lambda: (shield(False), shield(True)), link_shield)

n = 0
for name, (make, link) in JOBS.items():
    if ONLY and name not in ONLY:
        continue
    make()
    if link:
        link()
    n += 1
print("made", n, "hand-built items")
