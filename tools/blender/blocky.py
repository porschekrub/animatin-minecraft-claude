#!/usr/bin/env python3
"""Lifelike Motion's 3D items: real chunky models built from boxes (in the spirit of Actions & Stuff), not the
game's flat item pictures made thick. Each item is painted by hand-tuned rules, SMOOTHLY: colours flow across the
model (a colour per corner, blended by the game), with soft light rims along the top edges of every block, darker
undersides, a gentle shine on round things, and only a few deliberate pixel details (a wrapped grip, a groove, a
sparkle). Soft shadows are baked in by Blender. Weapons and tools are made to look cool; food, bottles and buckets
to look beautiful.

Runs with Blender's Python module:  python3 tools/blender/blocky.py <pack dir> [names...] [--preview out.png]

Models are written in pixels, Minecraft's way: x right, y up, z toward the viewer (south); a box is
(x0, y0, z0, x1, y1, z1, material). Writes, for every item: the OBJ model, its item3d model (how it's held) and the
item's own model (3D in the hand and on the ground, the usual flat picture in the inventory).
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import items as K  # noqa: E402  (loads Blender)
import bpy  # noqa: E402
import bmesh  # noqa: E402

DIRS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def lerp_ramp(ramp, t):
    t = min(max(t, 0.0), 1.0) * (len(ramp) - 1)
    i = min(int(t), len(ramp) - 2)
    f = t - i
    return np.array(ramp[i]) * (1 - f) + np.array(ramp[i + 1]) * f


# ---------------------------------------------------------------- paints
class Paint:
    """how one material is painted.
    ramp: colours (dark to light) flowing smoothly along `axis` from lo to hi (in pixels)
    rim / under: how much lighter the top edges / darker the bottom edges of each block are (fading over a pixel)
    faces: tops a little lighter, undersides a little darker
    wave: a very soft, wide colour drift (organic things)
    pattern(face centre, normal) -> brightness factor for that one pixel (deliberate details)
    shine(corner, normal) -> 0..1 of a soft white highlight
    sparkle: chance of a single bright pixel (gems)"""

    def __init__(self, ramp, axis=(0, 1, 0), lo=0, hi=16, rim=0.22, under=0.18, faces=0.08, wave=0.0,
                 pattern=None, shine=None, sparkle=0.0, alpha=1.0, tint=-1, glow=False, seed=0):
        self.ramp = [rgb(c) if isinstance(c, str) else c for c in ramp]
        self.axis, self.lo, self.hi = np.array(axis, float), lo, hi
        self.rim, self.under, self.faces, self.wave = rim, under, faces, wave
        self.pattern, self.shine, self.sparkle = pattern, shine, sparkle
        self.alpha, self.tint, self.glow, self.seed = alpha, tint, glow, seed

    def soft(self, q):
        """slow value noise in [-1, 1] (patches several pixels wide)"""
        p = np.array(q) / 4.0
        i = np.floor(p).astype(int)
        f = p - i
        f = f * f * (3 - 2 * f)
        out = 0.0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (f[0] if dx else 1 - f[0]) * (f[1] if dy else 1 - f[1]) * (f[2] if dz else 1 - f[2])
                    out += w * (random.Random(hash((self.seed, i[0] + dx, i[1] + dy, i[2] + dz))).random() * 2 - 1)
        return out

    def corner(self, q, centre, n, rim_kind, face_k):
        t = (np.dot(self.axis, q) - self.lo) / max(self.hi - self.lo, 1e-6)
        c = lerp_ramp(self.ramp, t)
        k = face_k * (1 + self.faces * n[1] + 0.04 * n[2] - 0.03 * n[0])
        if self.wave:
            k *= 1 + self.wave * self.soft(q)
        c = c * k
        if rim_kind == "up":
            c = c + (1 - c) * self.rim
        elif rim_kind == "side":
            c = c + (1 - c) * self.rim * 0.45
        elif rim_kind == "down":
            c = c * (1 - self.under)
        if self.shine:
            s = self.shine(q, n)
            c = c + (1 - c) * s
        return np.clip(c, 0, 1)


# ---------------------------------------------------------------- building
def voxels(boxes):
    grid = {}
    for (x0, y0, z0, x1, y1, z1, m) in boxes:
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    grid[(x, y, z)] = m
    return grid


def build(name, boxes, paints, seed=1):
    grid = voxels(boxes)
    rnd = random.Random(seed)
    names = sorted({m for m in grid.values()})
    mats = {m: K.mat(m, attr="paint", edge=0.0, alpha=paints[m].alpha, tint=paints[m].tint, glow=paints[m].glow)
            for m in names}
    order = list(mats)
    bm = bmesh.new()
    paint = bm.loops.layers.float_color.new("paint")
    clear = {m for m in names if paints[m].alpha < 1}
    s = 1 / 16
    for (x, y, z), m in grid.items():
        pm = paints[m]
        for d in DIRS:
            other = grid.get((x + d[0], y + d[1], z + d[2]))
            # a face shows where there's nothing next to it, or something see-through (but not glass to glass)
            if other is not None and not (other in clear and m not in clear):
                continue
            centre = np.array([x + 0.5, y + 0.5, z + 0.5])
            ax = [i for i in range(3) if d[i] == 0]
            # which sides of this pixel lie on an outer edge of the block (a rim)
            open_side = {}
            for i in ax:
                for sgn in (-1, 1):
                    t = [0, 0, 0]
                    t[i] = sgn
                    beside = grid.get((x + t[0], y + t[1], z + t[2]))
                    over = grid.get((x + t[0] + d[0], y + t[1] + d[1], z + t[2] + d[2]))
                    open_side[(i, sgn)] = beside != m or over is not None
            face_k = pm.pattern(centre, d) if pm.pattern else 1.0
            if pm.sparkle and rnd.random() < pm.sparkle:
                face_k *= 1.7
            corners, cols = [], []
            fc = centre + 0.5 * np.array(d)
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                q = fc.copy()
                q[ax[0]] += 0.5 * a
                q[ax[1]] += 0.5 * b
                kind = None
                for i, sgn in ((ax[0], a), (ax[1], b)):
                    if open_side[(i, sgn)]:
                        k = "up" if (i == 1 and sgn > 0) else "down" if (i == 1 and sgn < 0) else "side"
                        # strongest rim wins: up > side > down
                        if kind is None or (k == "up") or (k == "side" and kind == "down"):
                            kind = k
                if d[1] > 0 and kind == "side":
                    kind = "up"  # the outer edge of a top face catches the light too
                corners.append(q)
                cols.append(pm.corner(q, centre, d, kind, face_k))
            vs = [bm.verts.new((q[0] * s, 1 - q[2] * s, q[1] * s)) for q in corners]  # MC -> Blender axes
            f = bm.faces.new(vs)
            f.normal_update()
            if f.normal.dot((d[0], -d[2], d[1])) < 0:
                f.normal_flip()
                # flipping reverses the loop order: keep each colour with its corner
            f.material_index = order.index(m)
            f.smooth = False
            for loop in f.loops:
                co = loop.vert.co
                q = np.array([co.x / s, co.z / s, (1 - co.y) / s])
                j = int(np.argmin([np.sum((q - c) ** 2) for c in corners]))
                c = cols[j]
                lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
                loop[paint] = (*lin, 1.0)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    ob = K.obj_from_bm(name, bm, mats[order[0]], smooth=False)
    for m in order[1:]:
        ob.data.materials.append(mats[m])
    return ob, bool(clear)


def mirror_x(boxes, cx=16):
    """the same boxes again on the other side (x -> cx - x)"""
    return boxes + [(cx - x1, y0, z0, cx - x0, y1, z1, m) for (x0, y0, z0, x1, y1, z1, m) in boxes]


def blob(centre, radius, strength=0.55):
    """a soft round highlight (for shine): 0..strength, fading out over `radius` pixels"""
    c = np.array(centre, float)
    def f(q, n):
        d = np.linalg.norm(np.array(q) - c)
        return strength * max(0.0, 1 - d / radius) ** 1.6
    return f


# ---------------------------------------------------------------- beautiful things
def apple():
    """a squared-off apple, every side bevelled in a step, a stem in a little hollow, a leaf"""
    R = "skin"
    boxes = [
        (4, 2, 4, 12, 10, 12, R),
        (3, 3, 5, 13, 9, 11, R), (5, 3, 3, 11, 9, 13, R),
        (5, 10, 5, 11, 11, 11, R), (5, 1, 5, 11, 2, 11, R),
        (7, 10, 7, 9, 11, 9, "dip"),
        (7, 11, 7, 8, 14, 8, "stem"), (8, 13, 7, 9, 14, 8, "stem"),
        (8, 12, 8, 12, 13, 9, "leaf"), (9, 13, 8, 11, 14, 9, "leaf"),
    ]
    paints = {
        R: Paint(["5e0910", "9a121b", "cf1f26", "e8362e", "f2643c", "f7a052"], lo=1.5, hi=11.5, rim=0.18, wave=0.05,
                 shine=blob((5.5, 8.5, 12.5), 4.0, 0.6), seed=1),
        "dip": Paint(["4c0a0e", "731410"], rim=0.0, under=0.0),
        "stem": Paint(["3a2412", "6e4a24"], lo=11, hi=14, rim=0.25),
        "leaf": Paint(["2d6a1e", "4f9c2c", "86cf4e"], axis=(1, 0, 0), lo=8, hi=12, rim=0.3, seed=3),
    }
    return boxes, paints, "food"


def potion():
    """a glass bottle you can see the potion through (coloured by the game: blue for water), a neck tied with
    string, a lip and a cork"""
    boxes = [
        (5, 1, 5, 11, 8, 11, "glass"),
        (6, 2, 6, 10, 6, 10, "potion"),
        (7, 8, 7, 9, 10, 9, "glass"), (6, 10, 6, 10, 11, 10, "glass"),
        (6, 8, 6, 10, 9, 10, "string"),
        (7, 10, 7, 9, 13, 9, "cork"),
    ]
    paints = {
        "glass": Paint([(0.66, 0.82, 0.93), (0.86, 0.95, 1.0)], lo=1, hi=11, rim=0.75, under=0.1, alpha=0.38),
        "potion": Paint([(0.52, 0.52, 0.52), (0.8, 0.8, 0.8), (1.0, 1.0, 1.0)], lo=2, hi=6, rim=0.35, tint=0,
                        shine=blob((6.5, 5.5, 10), 2.5, 0.5)),
        "string": Paint(["b89c6a", "e3cfa0"], lo=8, hi=9, rim=0.2),
        "cork": Paint(["8a5a30", "b5834a", "d9b07a"], lo=10, hi=13, rim=0.25, wave=0.08, seed=6),
    }
    return boxes, paints, "food"


def water_bucket():
    """an iron bucket with thin walls, a darker band, little side lugs, and clear blue water with a shine"""
    walls = []
    for (x0, z0, x1, z1) in ((3, 3, 13, 4), (3, 12, 13, 13), (3, 4, 4, 12), (12, 4, 13, 12)):
        walls.append((x0, 1, z0, x1, 11, z1, "iron"))
    boxes = walls + [
        (4, 1, 4, 12, 2, 12, "iron"),                     # the bottom
        (4, 2, 4, 12, 9, 12, "water"),
        (2, 8, 7, 3, 11, 9, "lug"), (13, 8, 7, 14, 11, 9, "lug"),
    ]
    def band(p, n):
        return 0.8 if 4 <= p[1] < 5 and abs(n[1]) < 0.5 else 1.0
    paints = {
        "iron": Paint(["5c5f63", "8c8f94", "b8bbbf", "dcdee1"], lo=1, hi=11, rim=0.35, pattern=band),
        "lug": Paint(["6f7276", "a7aaae"], lo=8, hi=11, rim=0.3),
        "water": Paint(["1b4fb8", "2f74e0", "5aa0f4"], lo=2, hi=9, rim=0.0, wave=0.12,
                       shine=blob((6, 9, 6), 3.2, 0.55), seed=12),
    }
    return boxes, paints, "food"


# ---------------------------------------------------------------- cool things
DIAMOND = ["0b332c", "0e3f36", "15634f", "1e8a77", "2bc7ac", "33ebcb", "a4fdf0"]


def diamond_sword():
    """standing up: a glowing pommel stone, a wrapped grip, a guard with raised tips and a stone on each face, a blade
    with a groove down the middle, bright sharp edges and a point"""
    boxes = [
        (6, 0, 7, 10, 2, 9, "stone"), (7, 0, 6, 9, 2, 10, "stone"),
        (7, 2, 7, 9, 7, 9, "grip"),
        (3, 7, 6, 13, 9, 10, "guard"),
        (2, 8, 7, 3, 11, 9, "guard"), (13, 8, 7, 14, 11, 9, "guard"),
        (7, 8, 5, 9, 10, 6, "stone"), (7, 8, 10, 9, 10, 11, "stone"),
        (6, 9, 7, 10, 22, 9, "blade"),
        (5, 9, 7, 6, 20, 9, "edge"), (10, 9, 7, 11, 20, 9, "edge"),
        (6, 22, 7, 10, 24, 9, "blade"), (7, 24, 7, 9, 26, 9, "blade"),
        (5, 20, 7, 6, 21, 9, "edge"), (10, 20, 7, 11, 21, 9, "edge"),
    ]
    def wrap(p, n):
        return 0.72 if int(p[1]) % 2 == 0 else 1.0
    def groove(p, n):
        return 0.68 if 7 <= p[0] < 9 and abs(n[2]) > 0 and 10 <= p[1] < 21 else 1.0
    paints = {
        "blade": Paint(DIAMOND[2:], lo=9, hi=26, rim=0.3, pattern=groove),
        "edge": Paint(["7fefdc", "c9fff6", "f2fffd"], lo=9, hi=21, rim=0.2),
        "guard": Paint(DIAMOND[:5], lo=7, hi=11, rim=0.35),
        "stone": Paint(["33ebcb", "a4fdf0", "ffffff"], lo=0, hi=11, rim=0.4, glow=True),
        "grip": Paint(["2a1a0b", "4a3018", "6e4c25"], lo=2, hi=7, rim=0.2, pattern=wrap),
    }
    return boxes, paints, "blade"


def diamond_axe():
    """a wooden handle wrapped at the grip, a diamond head: a socket, a wide fanned blade with a bright cutting edge,
    and a short spike on the back"""
    boxes = [
        (7, 0, 7, 9, 19, 9, "wood"),
        (6, 1, 6, 10, 6, 10, "wrap"),
        (6, 13, 6, 10, 19, 10, "head"),                    # socket round the handle
        (10, 13, 7, 12, 19, 9, "head"),                    # cheek
        (12, 11, 7, 14, 20, 9, "head"),                    # blade fanning out
        (14, 10, 7, 15, 21, 9, "head"),
        (15, 10, 7, 16, 21, 9, "edge"), (16, 11, 7, 17, 20, 9, "edge"),
        (3, 15, 7, 6, 17, 9, "head"), (2, 15, 7, 3, 16, 9, "edge"),  # the back spike
        (7, 19, 7, 9, 20, 9, "stone"),                     # a stone capping the handle
    ]
    def grain(p, n):
        return 0.86 if (int(p[0]) * 5 + int(p[2]) * 3 + int(p[1] / 5)) % 4 == 0 and abs(n[1]) < 0.5 else 1.0
    def wrapband(p, n):
        return 0.75 if int(p[1]) % 2 == 0 else 1.0
    paints = {
        "wood": Paint(["3b2611", "5a3d1c", "7a5428", "966a35"], lo=0, hi=19, rim=0.15, pattern=grain),
        "wrap": Paint(["2c1a0e", "4d2f18", "6b4424"], lo=1, hi=6, rim=0.25, pattern=wrapband),
        "head": Paint(DIAMOND[1:6], axis=(1, 0, 0), lo=3, hi=15, rim=0.35),
        "edge": Paint(["8ff5e4", "d6fff8", "ffffff"], lo=10, hi=21, rim=0.15),
        "stone": Paint(["33ebcb", "a4fdf0"], rim=0.4, glow=True),
    }
    return boxes, paints, "tool"


ITEMS = {
    "diamond_sword": diamond_sword, "diamond_axe": diamond_axe,
    "apple": apple, "potion": potion, "water_bucket": water_bucket,
}
# the item's flat inventory picture: its vanilla layers
GUI_LAYERS = {"potion": ["minecraft:item/potion_overlay", "minecraft:item/potion"]}


def upright(scale=0.42, lift=4.5, side=-0.5, toward=-1.0, turn=-35, tilt=12):
    """round things held standing up and facing you (turned a little, top tipped a little toward you)"""
    fp = lambda sx: {"rotation": [tilt, turn * sx, 0], "translation": [side, lift, toward], "scale": [scale] * 3}
    return {
        "thirdperson_righthand": {"rotation": [0, -35, 0], "translation": [0, 2.5, 1.5], "scale": [scale * 1.05] * 3},
        "thirdperson_lefthand": {"rotation": [0, 35, 0], "translation": [0, 2.5, 1.5], "scale": [scale * 1.05] * 3},
        "firstperson_righthand": fp(1), "firstperson_lefthand": fp(-1),
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
        "fixed": {"rotation": [0, 180, 0], "scale": [0.9, 0.9, 0.9]},
        "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }


def display(kind, name):
    """held so the whole model shows in first person, roughly where Minecraft holds its own items"""
    if kind == "blade":
        return K.hand_display(20, scale=0.36, lift=0.0)
    if kind == "tool":
        return K.hand_display(45, scale=0.42, lift=-0.5)
    return upright(**HELD.get(name, {}))


# per item: how big it's held (things wider than an apple a bit smaller)
HELD = {"water_bucket": {"scale": 0.34, "lift": 6.0}, "potion": {"scale": 0.44, "lift": 7.0}}


def item_model(name):
    """the item's own model: our 3D model everywhere except the inventory, which keeps the usual flat picture"""
    layers = GUI_LAYERS.get(name, [f"minecraft:item/{name}"])
    model = {"loader": "forge:separate_transforms", "textures": {"particle": f"minecraft:item/{name}"},
             "base": {"parent": f"{K.NS}:item3d/{name}"},
             "perspectives": {"gui": {"parent": "minecraft:item/generated",
                                      "textures": {f"layer{i}": t for i, t in enumerate(layers)}}}}
    p = os.path.join(K.PACK, "assets", "minecraft", "models", "item")
    os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, name + ".json"), "w") as f:
        json.dump(model, f, separators=(",", ":"))


if __name__ == "__main__":
    K.configure(sys.argv)
    K.white_texture()
    os.makedirs(os.path.join(K.PACK, "assets", K.NS, "models", "item3d"), exist_ok=True)
    pics = []
    for name in (sorted(K.ONLY) if K.ONLY else list(ITEMS)):
        K.reset()
        boxes, paints, kind = ITEMS[name]()
        ob, clear = build(name, boxes, paints)
        K.bake_and_export(ob, name, display(kind, name), clear, particle=f"minecraft:item/{name}", soft=0.2)
        item_model(name)
        print("made", name, len(ob.data.polygons), "faces")
        if K.PREVIEW:
            p = f"/tmp/claude-0/blocky_{name}.png"
            K.render_preview(ob, p)
            pics.append(p)
    if K.PREVIEW and pics:
        ims = [Image.open(p).convert("RGB") for p in pics]
        sheet = Image.new("RGB", (420 * len(ims), 420))
        for i, im in enumerate(ims):
            sheet.paste(im, (420 * i, 0))
        sheet.save(K.PREVIEW)
