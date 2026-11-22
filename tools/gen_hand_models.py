#!/usr/bin/env python3
"""Hand-built 3D models for the items you hold most: real shapes (a sword with a ridged blade, crossguard, wrapped grip
and pommel; tool heads forged in shape; a torch that is a stick with a glowing end), each with its own pixel-art
texture made here. Written over the auto-generated models of the same items in the "Lifelike 3D Items" pack.

Models are built standing up (handle down, tip up) and turned 45° by their display transforms, so the parts can use
their own rotations.

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
TEX = 64  # texture size (pixels); model UV 0..16 spans it

TIERS = {
    "wooden": (150, 108, 60), "stone": (136, 136, 136), "iron": (222, 222, 222), "golden": (250, 212, 70),
    "diamond": (70, 226, 210), "netherite": (78, 66, 72),
}
WOOD = (122, 86, 48)
DARK_WOOD = (84, 58, 32)
LEATHER = (92, 52, 34)
WRAP = (60, 40, 30)
GOLD = (236, 190, 60)
GEMS = {"wooden": (80, 200, 90), "stone": (200, 60, 60), "iron": (90, 140, 230), "golden": (220, 60, 90),
        "diamond": (240, 240, 255), "netherite": (170, 80, 230)}


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Painter:
    """Hands out small regions of the texture, each painted in a style; parts map their faces onto a region."""

    def __init__(self, seed):
        self.img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
        self.x = self.y = 0
        self.row = 0
        self.rng = random.Random(seed)

    def region(self, w, h, paint):
        if self.x + w > TEX:
            self.x = 0
            self.y += self.row
            self.row = 0
        x, y = self.x, self.y
        self.x += w
        self.row = max(self.row, h)
        for j in range(h):
            for i in range(w):
                self.img.putpixel((x + i, y + j), paint(i, j, w, h, self.rng) + (255,))
        # UV in model units (0..16)
        s = 16 / TEX
        return [x * s, y * s, (x + w) * s, (y + h) * s]


# ---- styles: (i, j, w, h, rng) -> colour
def metal(c):
    hi, lo = shade(c, 1.25), shade(c, 0.62)

    def f(i, j, w, h, r):
        t = i / max(w - 1, 1)
        base = lerp(hi, c, min(t * 1.6, 1)) if t < 0.5 else lerp(c, lo, (t - 0.5) * 2)
        return shade(base, 0.94 + r.random() * 0.1)
    return f


def edge(c):
    hi = lerp(shade(c, 1.35), (255, 255, 255), 0.35)

    def f(i, j, w, h, r):
        return shade(hi, 0.95 + r.random() * 0.08)
    return f


def flat(c, noise=0.08):
    def f(i, j, w, h, r):
        return shade(c, 1 - noise / 2 + r.random() * noise)
    return f


def stripes(a, b, n=4):
    def f(i, j, w, h, r):
        k = (j * n // h) % 2
        base = a if k == 0 else b
        # a diagonal wrap line
        if (i + j) % 4 == 0:
            base = shade(base, 0.8)
        return shade(base, 0.95 + r.random() * 0.08)
    return f


def wood(c):
    def f(i, j, w, h, r):
        grain = 0.88 + 0.12 * math.sin(i * 1.7 + r.random() * 0.4)
        return shade(c, grain * (0.95 + r.random() * 0.08))
    return f


def gem(c):
    def f(i, j, w, h, r):
        hl = 1.35 if i < w / 2 and j < h / 2 else 1.0 if i < w / 2 or j < h / 2 else 0.7
        return shade(c, hl)
    return f


def glow(a, b):
    def f(i, j, w, h, r):
        return lerp(a, b, j / max(h - 1, 1))
    return f


# ---- model building
class Model:
    def __init__(self, name):
        self.name = name
        self.p = Painter(hash(name) & 0xffff)
        self.els = []
        self.cache = {}
        self.dy = 0  # moves every part along the length (toward the tip)

    def style(self, key, paint, w=8, h=8):
        if key not in self.cache:
            self.cache[key] = self.p.region(w, h, paint)
        return self.cache[key]

    def box(self, frm, to, uv, rot=None, side_uv=None, end_uv=None, shade_faces=True, light=False):
        """A box; front/back faces use uv, the sides side_uv (default uv), the ends end_uv (default side)."""
        side_uv = side_uv or uv
        end_uv = end_uv or side_uv
        faces = {
            "north": {"uv": uv, "texture": "#t"}, "south": {"uv": uv, "texture": "#t"},
            "east": {"uv": side_uv, "texture": "#t"}, "west": {"uv": side_uv, "texture": "#t"},
            "up": {"uv": end_uv, "texture": "#t"}, "down": {"uv": end_uv, "texture": "#t"},
        }
        frm = (frm[0], frm[1] + self.dy, frm[2])
        to = (to[0], to[1] + self.dy, to[2])
        if rot:
            rot = (rot[0], rot[1], [rot[2][0], rot[2][1] + self.dy, rot[2][2]])
        e = {"from": [round(v, 3) for v in frm], "to": [round(v, 3) for v in to], "faces": faces}
        if not shade_faces:
            e["shade"] = False
        if rot:
            axis, angle, origin = rot
            e["rotation"] = {"angle": angle, "axis": axis, "origin": origin}
        if light:
            e["light_emission"] = 15
        self.els.append(e)

    def write(self, display):
        tex_name = f"item/hand/{self.name}"
        p = os.path.join(PACK, "assets", NS, "textures", tex_name + ".png")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        self.p.img.save(p)
        model = {"gui_light": "front", "textures": {"t": f"{NS}:{tex_name}", "particle": f"{NS}:{tex_name}"},
                 "display": display, "elements": self.els}
        mp = os.path.join(PACK, "assets", NS, "models", "item3d", self.name + ".json")
        with open(mp, "w") as f:
            json.dump(model, f, separators=(",", ":"))


def hand_display(turn=45):
    """The game's hand-held display, with the standing model turned onto the usual diagonal."""
    d = {
        "thirdperson_righthand": {"rotation": [0, -90, 55], "translation": [0, 4.0, 0.5], "scale": [0.85, 0.85, 0.85]},
        "thirdperson_lefthand": {"rotation": [0, 90, -55], "translation": [0, 4.0, 0.5], "scale": [0.85, 0.85, 0.85]},
        "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
        "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 3.2, 1.13], "scale": [0.68, 0.68, 0.68]},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
        "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }
    for k, v in d.items():
        r = v["rotation"]
        # left-hand displays are mirrored: turn the other way
        v["rotation"] = [r[0], r[1], r[2] + (-turn if "left" in k else turn)]
    return d


# ---------------------------------------------------------------- the items
def sword(tier, turn=20):
    c = TIERS[tier]
    m = Model(f"{tier}_sword")
    m.dy = 3.5  # the hilt sits in the hand, the blade reaches further out
    blade = m.style("blade", metal(c), 8, 16)
    edg = m.style("edge", edge(c), 4, 16)
    ridge = m.style("ridge", flat(shade(c, 0.78)), 2, 16)
    guard_c = GOLD if tier in ("diamond", "netherite") else shade(TIERS[tier], 0.8) if tier != "wooden" else DARK_WOOD
    guard = m.style("guard", metal(guard_c), 8, 4)
    grip = m.style("grip", stripes(LEATHER, WRAP, 6), 4, 8)
    gemuv = m.style("gem", gem(GEMS[tier]), 4, 4)
    pom = m.style("pommel", metal(guard_c), 4, 4)
    z0, z1 = 7.3, 8.7
    # blade: core, bevelled edges, a raised ridge, a tapered tip
    m.box((7, 4, z0), (9, 17, z1), blade, side_uv=edg)
    m.box((6.2, 4.4, 7.65), (7, 16.2, 8.35), edg)
    m.box((9, 4.4, 7.65), (9.8, 16.2, 8.35), edg)
    m.box((7.7, 4.8, 7.05), (8.3, 16, 8.95), ridge)
    m.box((7.2, 17, 7.45), (8.8, 18.4, 8.55), blade, side_uv=edg)
    m.box((7.6, 18.4, 7.65), (8.4, 19.6, 8.35), edg)
    m.box((7.85, 19.6, 7.8), (8.15, 20.3, 8.2), edg)
    # crossguard with flared ends and a gem in the middle
    m.box((4.2, 3.1, 7.0), (11.8, 4.1, 9.0), guard)
    m.box((3.3, 2.7, 6.8), (4.4, 4.6, 9.2), guard)
    m.box((11.6, 2.7, 6.8), (12.7, 4.6, 9.2), guard)
    m.box((6.9, 2.5, 6.7), (9.1, 4.6, 9.3), guard)
    m.box((7.5, 3.0, 6.5), (8.5, 4.0, 9.5), gemuv)
    # wrapped grip and pommel
    m.box((7.35, -1.6, 7.35), (8.65, 2.5, 8.65), grip)
    m.box((6.9, -2.7, 6.9), (9.1, -1.6, 9.1), pom)
    m.box((7.6, -3.1, 7.6), (8.4, -2.7, 8.4), gemuv)
    m.write(hand_display(turn))


def handle(m, top, bottom=-3.2):
    w = m.style("handle", wood(WOOD), 4, 16)
    band = m.style("band", metal(shade(WOOD, 0.6)), 4, 4)
    m.box((7.35, bottom, 7.35), (8.65, top, 8.65), w)
    m.box((7.15, bottom - 0.4, 7.15), (8.85, bottom + 0.6, 8.85), band)


def pickaxe(tier):
    c = TIERS[tier]
    m = Model(f"{tier}_pickaxe")
    handle(m, 13.6)
    head = m.style("head", metal(c), 8, 8)
    dark = m.style("dark", metal(shade(c, 0.8)), 8, 8)
    edg = m.style("edge", edge(c), 4, 8)
    # the socket, then each arm curving down in steps to a sharp point
    m.box((6.6, 12.2, 6.9), (9.4, 15.6, 9.1), dark)
    for sgn in (-1, 1):
        def bx(x0, x1, y0, y1, z, uv):
            a, b = (8 + sgn * x0, 8 + sgn * x1)
            m.box((min(a, b), y0, 8 - z), (max(a, b), y1, 8 + z), uv)
        bx(1.4, 3.8, 12.8, 15.1, 0.85, head)
        bx(3.8, 5.6, 12.0, 14.5, 0.8, head)
        bx(5.6, 6.9, 11.0, 13.6, 0.7, head)
        bx(6.9, 7.7, 10.0, 12.4, 0.55, edg)
        bx(7.7, 8.2, 9.2, 11.0, 0.4, edg)
    m.write(hand_display())


def axe(tier):
    c = TIERS[tier]
    m = Model(f"{tier}_axe")
    handle(m, 14.6)
    head = m.style("head", metal(c), 8, 8)
    dark = m.style("dark", metal(shade(c, 0.8)), 8, 8)
    edg = m.style("edge", edge(c), 4, 8)
    # socket, a broad blade widening toward a bright edge (bearded below), a short poll behind
    m.box((6.7, 10.6, 6.95), (9.3, 15.2, 9.05), dark)
    m.box((9.3, 11.0, 7.15), (10.8, 14.8, 8.85), head)
    m.box((10.8, 10.0, 7.25), (12.2, 15.6, 8.75), head)
    m.box((12.2, 8.8, 7.35), (13.4, 16.4, 8.65), head)
    m.box((13.4, 8.2, 7.5), (14.3, 16.9, 8.5), edg)
    m.box((5.1, 11.6, 7.2), (6.7, 14.2, 8.8), dark)
    m.box((4.4, 12.0, 7.4), (5.1, 13.8, 8.6), head)
    m.write(hand_display())


def torch():
    m = Model("torch")
    stick = m.style("stick", wood(shade(WOOD, 1.1)), 4, 12)
    wrap = m.style("wrap", stripes((130, 110, 80), (100, 80, 60), 4), 4, 4)
    ember = m.style("ember", glow((255, 240, 150), (240, 120, 30)), 4, 4)
    core = m.style("core", flat((255, 250, 210), 0.04), 2, 2)
    m.box((7.2, -2.0, 7.2), (8.8, 9.0, 8.8), stick)
    m.box((6.9, 8.0, 6.9), (9.1, 10.2, 9.1), wrap)
    m.box((7.0, 10.2, 7.0), (9.0, 12.2, 9.0), ember, shade_faces=False, light=True)
    m.box((7.5, 12.2, 7.5), (8.5, 13.6, 8.5), core, shade_faces=False, light=True)
    m.write(hand_display())


JOBS = {}
for t in TIERS:
    JOBS[f"{t}_sword"] = lambda t=t: sword(t)
    JOBS[f"{t}_pickaxe"] = lambda t=t: pickaxe(t)
    JOBS[f"{t}_axe"] = lambda t=t: axe(t)
JOBS["torch"] = torch

TURN_TEST = {}
if os.environ.get("TURN_TEST"):
    for n, tt in TURN_TEST.items():
        JOBS[n] = lambda n=n, tt=tt: sword(n.split("_")[0], tt)

for name, job in JOBS.items():
    if ONLY and name not in ONLY:
        continue
    job()
    print("made", name)
