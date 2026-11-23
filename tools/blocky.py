#!/usr/bin/env python3
"""Blocky 3D items, the way Bedrock's Actions & Stuff does them: each item built from a few boxes into its real shape
(an apple with a stem and a leaf, a sword with a guard and grip, a bottle with a cork), and every face of every box
painted with its own pixel art at Minecraft's own pixel size (16 pixels a block) - not the flat item picture.

The painting is done here, pixel by pixel: colours come in hand-tuned ramps that shift hue as they darken (warm
lights, cool shadows, like pixel artists do), faces light from the top-left with a one-pixel bevel (light rim on top,
dark on the bottom), soft clustered noise on organic things, clean streaks on metal, sparkles on gems.

Writes vanilla item models (assets/lifelikemotion/models/item3d/<name>.json) and one small texture per item
(assets/lifelikemotion/textures/item/blocky/<name>.png).    python3 tools/blocky.py [names...]
"""
import colorsys
import json
import math
import os
import random
import sys

from PIL import Image

PACK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources", "resourcepacks",
                    "lifelike_3d_items")
NS = "lifelikemotion"
ANGLES = (-45, -22.5, 0, 22.5, 45)


# ---------------------------------------------------------------- colour
def ramp(rgb, n=7, spread=1.0):
    """a pixel-art colour ramp from dark to light around a base colour (index n//2 is the base): darker shades get
    more saturated and shift cool, lighter ones less saturated and shift warm"""
    r, g, b = (c / 255 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    out = []
    mid = n // 2
    for k in range(n):
        t = (k - mid) / mid * spread  # -1 .. 1
        hh = h + (-0.035 * t if t < 0 else 0.03 * t) * (1 if 0.05 < h < 0.6 else -1)
        hh %= 1.0
        ss = min(1.0, max(0.0, s * (1 - 0.35 * t) if t > 0 else s * (1 - 0.25 * t)))
        vv = min(1.0, max(0.0, v * (1 + 0.42 * t) if t > 0 else v * (1 + 0.55 * t)))
        if t > 0.6 and s < 0.25:
            vv = min(1.0, vv + 0.05)
        out.append(tuple(int(round(c * 255)) for c in colorsys.hsv_to_rgb(hh, ss, vv)))
    return out


def noise2(seed):
    """smooth value noise (clusters a few pixels wide)"""
    rnd = random.Random(seed)
    grid = {}

    def at(ix, iy):
        if (ix, iy) not in grid:
            grid[(ix, iy)] = rnd.random()
        return grid[(ix, iy)]

    def f(x, y, scale):
        x, y = x / scale, y / scale
        ix, iy = math.floor(x), math.floor(y)
        fx, fy = x - ix, y - iy
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a = at(ix, iy) * (1 - fx) + at(ix + 1, iy) * fx
        b = at(ix, iy + 1) * (1 - fx) + at(ix + 1, iy + 1) * fx
        return a * (1 - fy) + b * fy
    return f


class Mat:
    """how a material paints: its ramp, where its base sits on the ramp, and its character"""

    def __init__(self, rgb, kind="organic", noise=0.8, scale=2.2, grad=1.0, bevel=1.0, alpha=255, decal=None,
                 spread=1.0, base=None, tint=False, glow=False):
        self.pal = ramp(rgb, spread=spread)
        self.base = len(self.pal) // 2 if base is None else base
        self.kind, self.noise, self.scale, self.grad, self.bevel = kind, noise, scale, grad, bevel
        self.alpha, self.decal, self.tint, self.glow = alpha, decal, tint, glow


def paint(mat, face, w, h, seed):
    """one face's pixel art (h rows of w pixels; row 0 is the face's top)"""
    nz = noise2(seed)
    rnd = random.Random(seed * 7 + 1)
    side = face in ("north", "south", "east", "west")
    lift = {"up": 0.9, "down": -1.0, "north": 0.0, "south": 0.0, "east": -0.25, "west": 0.15}[face]
    img = []
    for j in range(h):
        row = []
        for i in range(w):
            k = mat.base + lift
            if side and h > 1:
                k += mat.grad * (0.5 - (j + 0.5) / h) * 1.6  # lit from above
            elif not side and w > 1:
                k += mat.grad * 0.5 * (0.5 - (i + 0.5) / w)
            if mat.kind == "organic":
                k += mat.noise * (nz(i + seed % 7, j, mat.scale) - 0.5) * 2.2
                if rnd.random() < 0.06 * mat.noise:
                    k += rnd.choice((-1, 1))
            elif mat.kind == "metal":
                # a bright diagonal streak and a quieter echo
                d = (i + j * 0.9) / max(w + h * 0.9, 1)
                k += 1.6 * math.exp(-((d - 0.32) / 0.07) ** 2) + 0.7 * math.exp(-((d - 0.62) / 0.05) ** 2) - 0.3
                k += mat.noise * (nz(i, j, mat.scale) - 0.5)
            elif mat.kind == "gem":
                cx = (i + 0.5) / w - 0.5
                k += 1.2 - 3.0 * abs(cx) if w >= 3 else 0.6
                k += 0.8 * (nz(i * 2, j, 1.5) - 0.5)
                if rnd.random() < 0.05:
                    k += 2.5  # a sparkle
            elif mat.kind == "wood":
                k += 0.9 * math.sin((i + 2.5 * nz(i, j, 3.0)) * 1.9) * 0.6 + mat.noise * (nz(i, j * 0.3, 2) - 0.5)
            elif mat.kind == "wrap":
                k += 1.1 if (i + j) % 3 == 0 else (-0.6 if (i + j) % 3 == 2 else 0.2)
            elif mat.kind == "glass":
                k += 0.4 * (nz(i, j, 2.5) - 0.5)
            # bevel: light rim along the top and left, dark along the bottom and right
            if mat.bevel and w >= 3 and h >= 3:
                if j == 0 or (i == 0 and side):
                    k += 1.0 * mat.bevel
                elif j == h - 1 or (i == w - 1 and side):
                    k -= 0.9 * mat.bevel
                elif not side and (i == 0 or i == w - 1):
                    k += 0.5 * mat.bevel
            if mat.decal:
                k = mat.decal(k, i, j, w, h, face, rnd)
            idx = int(round(max(0, min(len(mat.pal) - 1, k))))
            a = mat.alpha
            if mat.kind == "glass" and (j == 0 or i == 0) and w >= 2 and h >= 2:
                a = min(255, a + 70)
            row.append((*mat.pal[idx], a))
        img.append(row)
    return img


# ---------------------------------------------------------------- models
class Model:
    def __init__(self, name):
        self.name = name
        self.els = []
        self.translucent = False

    def box(self, frm, to, mat, rot=None, faces=None, seed=None):
        """a box from frm to to (in pixels, 16 a block); rot = (angle, axis, origin)"""
        if rot:
            assert rot[0] in ANGLES, rot
        self.els.append((list(frm), list(to), mat, rot, faces, seed if seed is not None else len(self.els) * 31 + 5))
        if mat.alpha < 255:
            self.translucent = True

    def write(self, display):
        # every face's size in texture pixels
        dims = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}
        pieces = []
        for ei, (frm, to, mat, rot, faces, seed) in enumerate(self.els):
            size = [abs(to[a] - frm[a]) for a in range(3)]
            for face, (a, b) in dims.items():
                if faces and face not in faces:
                    continue
                w, h = max(1, math.ceil(size[a] - 1e-6)), max(1, math.ceil(size[b] - 1e-6))
                pieces.append((ei, face, w, h))
        # shelf-pack the faces into the smallest square texture they fit
        for T in (16, 32, 64, 128):
            place, x, y, shelf = {}, 0, 0, 0
            ok = True
            for ei, face, w, h in sorted(pieces, key=lambda p: -p[3]):
                if x + w > T:
                    x, y, shelf = 0, y + shelf, 0
                if y + h > T or w > T:
                    ok = False
                    break
                place[(ei, face)] = (x, y, w, h)
                x += w
                shelf = max(shelf, h)
            if ok:
                break
        tex = Image.new("RGBA", (T, T), (0, 0, 0, 0))
        els = []
        tname = f"{NS}:item/blocky/{self.name}"
        for ei, (frm, to, mat, rot, faces, seed) in enumerate(self.els):
            e = {"from": frm, "to": to, "faces": {}}
            if rot:
                e["rotation"] = {"angle": rot[0], "axis": rot[1], "origin": list(rot[2])}
            for face in dims:
                if (ei, face) not in place:
                    continue
                x, y, w, h = place[(ei, face)]
                img = paint(mat, face, w, h, seed + hash(face) % 97)
                for j in range(h):
                    for i in range(w):
                        tex.putpixel((x + i, y + j), img[j][i])
                f = {"uv": [x * 16 / T, y * 16 / T, (x + w) * 16 / T, (y + h) * 16 / T], "texture": "#0"}
                if mat.tint:
                    f["tintindex"] = 0
                e["faces"][face] = f
            if mat.glow:
                e["forge_data"] = {"block_light": 15, "sky_light": 15}
            els.append(e)
        tp = os.path.join(PACK, "assets", NS, "textures", "item", "blocky", self.name + ".png")
        os.makedirs(os.path.dirname(tp), exist_ok=True)
        tex.save(tp)
        model = {"textures": {"0": tname, "particle": f"minecraft:item/{self.name}"}, "elements": els, "display": display}
        if self.translucent:
            model["render_type"] = "minecraft:translucent"
        with open(os.path.join(PACK, "assets", NS, "models", "item3d", self.name + ".json"), "w") as fh:
            json.dump(model, fh, separators=(",", ":"))
        return T


# ---------------------------------------------------------------- how items sit in the hand
def held_upright(turn=20, lift=2.0, scale=0.68, tp=0.85):
    """long things built standing up (swords, tools): turned onto the usual diagonal"""
    return {
        "thirdperson_righthand": {"rotation": [0, -90, 55 + turn], "translation": [0, 4.0, 0.5], "scale": [tp] * 3},
        "thirdperson_lefthand": {"rotation": [0, 90, -55 - turn], "translation": [0, 4.0, 0.5], "scale": [tp] * 3},
        "firstperson_righthand": {"rotation": [0, -90, 25 + turn], "translation": [1.13, 3.2 + lift, 1.13], "scale": [scale] * 3},
        "firstperson_lefthand": {"rotation": [0, 90, -25 - turn], "translation": [1.13, 3.2 + lift, 1.13], "scale": [scale] * 3},
        "ground": {"rotation": [0, 0, turn], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, turn], "scale": [1, 1, 1]},
        "head": {"rotation": [0, 180, turn], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }


def held_small(scale=1.0, lift=0.0):
    """small things (food, bottles) held up in the palm"""
    s = 0.5 * scale
    return {
        "thirdperson_righthand": {"rotation": [10, -30, 0], "translation": [0, 3, 1], "scale": [0.55 * scale] * 3},
        "thirdperson_lefthand": {"rotation": [10, 30, 0], "translation": [0, 3, 1], "scale": [0.55 * scale] * 3},
        "firstperson_righthand": {"rotation": [0, -60, 10], "translation": [1.5, 5.0 + lift, 0.5], "scale": [s] * 3},
        "firstperson_lefthand": {"rotation": [0, 60, -10], "translation": [1.5, 5.0 + lift, 0.5], "scale": [s] * 3},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
        "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }


# ---------------------------------------------------------------- the items
def spot(cx, cy, r, amount, faces=("north", "south", "east", "west")):
    """a decal: a soft highlight (or shadow) around a point of a face (as fractions of the face)"""
    def f(k, i, j, w, h, face, rnd):
        if face in faces:
            d = math.hypot((i + 0.5) / w - cx, (j + 0.5) / h - cy)
            if d < r:
                k += amount * (1 - d / r) * 1.6
        return k
    return f


def both(*decals):
    def f(k, i, j, w, h, face, rnd):
        for d in decals:
            k = d(k, i, j, w, h, face, rnd)
        return k
    return f


def apple(name="apple", body=(208, 32, 40), leaf=(92, 160, 52), stem=(110, 70, 36)):
    m = Model(name)
    skin = Mat(body, noise=0.55, scale=2.5, decal=both(spot(0.3, 0.28, 0.28, 1.4), spot(0.75, 0.9, 0.4, -0.9)))
    skin_up = Mat(body, noise=0.4, base=4, decal=spot(0.5, 0.5, 0.35, -1.2, faces=("up",)))
    m.box((4, 1, 4), (12, 9, 12), skin)
    m.box((3, 2, 5), (13, 8, 11), skin, seed=11)
    m.box((5, 2, 3), (11, 8, 13), skin, seed=12)
    m.box((5, 9, 5), (11, 10, 11), skin_up, seed=13)
    m.box((5, 0, 5), (11, 1, 11), skin, seed=14)
    m.box((7.5, 9, 7.5), (8.5, 12.5, 8.5), Mat(stem, noise=0.3, bevel=0), rot=(-22.5, "z", (8, 9, 8)))
    m.box((8.5, 11, 7.5), (12.5, 11.75, 10), Mat(leaf, noise=0.5, scale=1.5,
                                                 decal=lambda k, i, j, w, h, f_, r: k + (1.2 if j == h // 2 else 0)),
          rot=(22.5, "z", (8.5, 11, 8)))
    return m.write(held_small(1.0, lift=1.0))


def cooked_chicken():
    m = Model("cooked_chicken")
    meat = Mat((196, 112, 46), noise=0.9, scale=1.8, decal=spot(0.3, 0.25, 0.3, 1.2))
    crisp = Mat((176, 92, 34), noise=1.0, scale=1.4, base=4)
    bone = Mat((236, 226, 200), noise=0.25, spread=0.6)
    m.box((2, 1, 4), (10, 7, 12), meat)
    m.box((3, 7, 5), (9, 8.5, 11), crisp, seed=21)
    m.box((1, 2, 5), (2, 6, 11), meat, seed=22)
    m.box((10, 2.5, 6), (12, 5.5, 10), meat, seed=23)
    m.box((12, 3, 7), (15, 5, 9), bone)
    m.box((14.5, 2.5, 6.5), (16.5, 5.5, 9.5), bone, seed=24)
    return m.write(held_small(1.0, lift=0.5))


def diamond_sword():
    m = Model("diamond_sword")
    blade = Mat((70, 222, 210), kind="gem", base=3, decal=lambda k, i, j, w, h, f, r: k + (0.9 if j < 2 else 0))
    edge = Mat((150, 245, 236), kind="gem", base=4, bevel=0.6)
    guard = Mat((26, 130, 120), kind="metal", noise=0.3, base=3)
    grip = Mat((92, 58, 30), kind="wrap", base=3, bevel=0.4)
    gem = Mat((120, 250, 240), kind="gem", base=5, bevel=0, glow=True)
    m.box((6.5, 0, 6.5), (9.5, 2.5, 9.5), guard, seed=31)            # pommel
    m.box((7, 2.5, 7), (9, 8, 9), grip)                                 # wrapped grip
    m.box((3, 8, 6.5), (13, 10, 9.5), guard)                            # crossguard
    m.box((1.5, 9, 7), (3, 12, 9), guard, seed=32)                      # its tips, curling up toward the blade
    m.box((13, 9, 7), (14.5, 12, 9), guard, seed=33)
    m.box((7, 8.25, 6), (9, 9.75, 10), gem)                             # a gem set through it
    m.box((6, 10, 7.25), (10, 21, 8.75), blade)                         # the blade
    m.box((7.25, 10, 6.75), (8.75, 20, 9.25), edge, seed=34)            # its raised middle ridge
    m.box((6.75, 21, 7.5), (9.25, 23, 8.5), blade, seed=35)             # the point, in steps
    m.box((7.5, 23, 7.75), (8.5, 24.5, 8.25), edge, seed=36)
    return m.write(held_upright(20, lift=2.0))


def potion():
    m = Model("potion")
    liquid = Mat((236, 236, 236), noise=0.3, base=4, spread=0.7, tint=True, bevel=0.5)
    glass = Mat((200, 230, 245), kind="glass", alpha=110, base=4, spread=0.6, bevel=0.6)
    cork = Mat((176, 126, 76), noise=0.7, scale=1.2)
    m.box((5.5, 1.5, 5.5), (10.5, 6, 10.5), liquid)
    m.box((7.25, 10.5, 7.25), (8.75, 12.75, 8.75), cork)
    m.box((5, 1, 5), (11, 7, 11), glass)
    m.box((6, 7, 6), (10, 8, 10), glass, seed=41)
    m.box((7, 8, 7), (9, 10.5, 9), glass, seed=42)
    m.box((6.5, 10.5, 6.5), (9.5, 11.25, 9.5), glass, seed=43)
    return m.write(held_small(1.0, lift=0.5))


ITEMS = {"apple": apple, "cooked_chicken": cooked_chicken, "diamond_sword": diamond_sword, "potion": potion}

if __name__ == "__main__":
    want = sys.argv[1:] or list(ITEMS)
    for n in want:
        print(n, "texture", ITEMS[n](), "px")
