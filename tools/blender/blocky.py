#!/usr/bin/env python3
"""Blocky 3D items in the Actions & Stuff spirit: each item is built from a few chunky boxes shaped like the real
thing (a squared-off apple with a leaf, a square bottle with a cork, a sword with a real guard and grip), and painted
with its OWN texture: soft colour gradients, a little pixel grain, lighter rims along the box edges. Every texel is one
Minecraft pixel (1/16 block), coloured straight into the mesh, with soft shadows baked in by Blender.

Runs with Blender's Python module:  python3 tools/blender/blocky.py <pack dir> [names...] [--preview out.png]

Models are written in pixels, Minecraft's way: x right, y up, z toward the viewer (south); a box is
(x0, y0, z0, x1, y1, z1, material).
"""
import colorsys
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


# ---------------------------------------------------------------- paints
class Paint:
    """how one material is painted: a ramp of colours along a direction (dark to light), pixel grain, lighter rims,
    and an optional pattern(pixel, normal) -> brightness factor"""

    def __init__(self, ramp, axis=(0, 1, 0), lo=0, hi=16, grain=0.05, rim=0.12, top=0.06, pattern=None,
                 alpha=1.0, tint=-1, glow=False):
        self.ramp = [rgb(c) if isinstance(c, str) else c for c in ramp]
        self.axis, self.lo, self.hi = np.array(axis, float), lo, hi
        self.grain, self.rim, self.top, self.pattern = grain, rim, top, pattern
        self.alpha, self.tint, self.glow = alpha, tint, glow

    def at(self, p, n, edge, rnd):
        t = (np.dot(self.axis, p) - self.lo) / max(self.hi - self.lo, 1e-6)
        t = min(max(t, 0.0), 1.0) * (len(self.ramp) - 1)
        i = min(int(t), len(self.ramp) - 2)
        f = t - i
        c = np.array(self.ramp[i]) * (1 - f) + np.array(self.ramp[i + 1]) * f
        k = 1.0 + (rnd.random() * 2 - 1) * self.grain
        if edge:
            k += self.rim
        if n[1] > 0:
            k += self.top
        if self.pattern:
            k *= self.pattern(p, n)
        return np.clip(c * k, 0, 1)


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
    mats = {}
    for m in names:
        p = paints[m]
        mats[m] = K.mat(m, attr="paint", edge=0.0, alpha=p.alpha, tint=p.tint, glow=p.glow)
    order = list(mats)
    bm = bmesh.new()
    paint = bm.loops.layers.float_color.new("paint")
    clear = {m for m in names if paints[m].alpha < 1}
    s = 1 / 16
    for (x, y, z), m in grid.items():
        for d in DIRS:
            nb = (x + d[0], y + d[1], z + d[2])
            other = grid.get(nb)
            # a face shows where there's nothing next to it, or something see-through (but not glass to glass)
            if other is not None and not (other in clear and m not in clear):
                continue
            # rim texels: at the edge of this face (a tangent neighbour is missing or another material)
            tang = [t for t in DIRS if t != d and t != tuple(-v for v in d)]
            edge = any(grid.get((x + t[0], y + t[1], z + t[2])) != m or
                       grid.get((x + t[0] + d[0], y + t[1] + d[1], z + t[2] + d[2])) is not None for t in tang)
            centre = np.array([x + 0.5, y + 0.5, z + 0.5])
            col = paints[m].at(centre, d, edge, rnd)
            # the face's corners, in pixels
            ax = [i for i in range(3) if d[i] == 0]
            fc = centre + 0.5 * np.array(d)
            corners = []
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                q = fc.copy()
                q[ax[0]] += 0.5 * a
                q[ax[1]] += 0.5 * b
                corners.append(q)
            # Minecraft (x, y up, z south) -> Blender (x, 1 - z, y)
            vs = [bm.verts.new((q[0] * s, 1 - q[2] * s, q[1] * s)) for q in corners]
            f = bm.faces.new(vs)
            f.normal_update()
            want = (d[0], -d[2], d[1])
            if f.normal.dot(want) < 0:
                f.normal_flip()
            f.material_index = order.index(m)
            f.smooth = False
            lin = tuple(np.where(col <= 0.04045, col / 12.92, ((col + 0.055) / 1.055) ** 2.4))
            for loop in f.loops:
                loop[paint] = (*lin, 1.0)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    ob = K.obj_from_bm(name, bm, mats[order[0]], smooth=False)
    for m in order[1:]:
        ob.data.materials.append(mats[m])
    return ob, bool(clear)


# ---------------------------------------------------------------- the items
def mirror_x(boxes, cx=16):
    """the same boxes again on the other side (x -> cx - x)"""
    return boxes + [(cx - x1, y0, z0, cx - x0, y1, z1, m) for (x0, y0, z0, x1, y1, z1, m) in boxes]


def apple():
    """a squared-off apple: a chunky core with every side bevelled in a step, a stem and a leaf"""
    R = "skin"
    boxes = [
        (4, 2, 4, 12, 10, 12, R),        # core
        (3, 3, 5, 13, 9, 11, R), (5, 3, 3, 11, 9, 13, R),  # sides stepped in
        (5, 10, 5, 11, 11, 11, R), (5, 1, 5, 11, 2, 11, R),  # top and bottom
        (7, 10, 7, 9, 11, 9, "dip"),      # the hollow round the stem
        (7, 11, 7, 8, 14, 8, "stem"), (8, 13, 7, 9, 14, 8, "stem"),
        (8, 12, 8, 12, 13, 9, "leaf"), (9, 13, 8, 11, 14, 9, "leaf"),
    ]
    def blush(p, n):
        # a sunny blush on the upper front, darker underneath
        return 1.0 + 0.12 * max(0.0, (p[1] - 6) / 5) * (1 if p[2] > 8 else 0.4)
    paints = {
        R: Paint(["7a0c12", "b5161f", "e02b2f", "f0553a", "f78a4a"], lo=1, hi=11, grain=0.045, rim=0.1, pattern=blush),
        "dip": Paint(["5a0a0e", "7a1410"], grain=0.03, rim=0),
        "stem": Paint(["3b2410", "6b4520"], lo=11, hi=14, grain=0.04, rim=0.08),
        "leaf": Paint(["2f6b1c", "5aa62e", "8ad04a"], axis=(1, 0, 0), lo=8, hi=12, grain=0.05, rim=0.12),
    }
    return boxes, paints, "food"


def potion():
    """a square bottle: glass you can see the coloured potion through, a neck, a lip and a cork"""
    boxes = [
        (5, 1, 5, 11, 8, 11, "glass"),
        (6, 2, 6, 10, 6, 10, "potion"),   # the potion inside (coloured by the game)
        (7, 8, 7, 9, 10, 9, "glass"), (6, 10, 6, 10, 11, 10, "glass"),
        (7, 10, 7, 9, 13, 9, "cork"),
    ]
    paints = {
        "glass": Paint([(0.72, 0.86, 0.95), (0.9, 0.96, 1.0)], lo=1, hi=11, grain=0.02, rim=0.18, alpha=0.42),
        "potion": Paint([(0.62, 0.62, 0.62), (1.0, 1.0, 1.0)], lo=2, hi=6, grain=0.04, rim=0.1, tint=0),
        "cork": Paint(["8a5a30", "b88350", "d8a970"], lo=10, hi=13, grain=0.07, rim=0.1),
    }
    return boxes, paints, "food"


def sword():
    """standing up: a pommel, a wrapped grip, a guard with raised tips, a blade with a thicker middle and a point"""
    boxes = [
        (6, 0, 7, 10, 2, 9, "gem"), (7, 0, 6, 9, 2, 10, "gem"),       # pommel
        (7, 2, 7, 9, 7, 9, "grip"),
        (3, 7, 6, 13, 9, 10, "guard"),
        (2, 8, 7, 3, 11, 9, "guard"), (13, 8, 7, 14, 11, 9, "guard"),  # raised tips
        (7, 8, 5, 9, 10, 6, "gem"), (7, 8, 10, 9, 10, 11, "gem"),     # a stone on each face of the guard
        (6, 9, 7, 10, 22, 9, "blade"),                                  # blade: 4 wide, 2 thick
        (5, 9, 7, 6, 20, 9, "edge"), (10, 9, 7, 11, 20, 9, "edge"),   # its sharp edges
        (6, 22, 7, 10, 24, 9, "blade"), (7, 24, 7, 9, 26, 9, "blade"), (5, 20, 7, 6, 21, 9, "edge"),
        (10, 20, 7, 11, 21, 9, "edge"),
    ]
    def wrap(p, n):
        return 0.78 if int(p[1]) % 2 == 0 else 1.0
    def fuller(p, n):
        # a darker groove down the middle of each face
        return 0.82 if 7 <= p[0] < 9 and abs(n[2]) > 0 and p[1] < 20 else 1.0
    paints = {
        "blade": Paint(["1e8a77", "2bc7ac", "33ebcb", "a4fdf0"], lo=9, hi=26, grain=0.04, rim=0.08, pattern=fuller),
        "edge": Paint(["8ff5e4", "c8fff6"], lo=9, hi=21, grain=0.03, rim=0.0),
        "guard": Paint(["0e3f36", "15634f", "1e8a77"], lo=7, hi=11, grain=0.05, rim=0.15),
        "gem": Paint(["2bc7ac", "a4fdf0"], lo=0, hi=11, grain=0.03, rim=0.2),
        "grip": Paint(["3d2812", "68481f", "8a6630"], lo=2, hi=7, grain=0.05, rim=0.05, pattern=wrap),
    }
    return boxes, paints, "blade"


def pickaxe():
    """a wooden handle with an iron cap, an iron head block and two arms curving down to points"""
    head = [
        (10, 14, 7, 13, 17, 9, "iron"), (13, 13, 7, 15, 16, 9, "iron"), (15, 11, 7, 17, 14, 9, "iron"),
        (16, 9, 7, 17, 11, 9, "tip"),
    ]
    boxes = [
        (7, 0, 7, 9, 18, 9, "wood"),
        (6, 0, 6, 10, 1, 10, "iron"),
        (6, 14, 6, 10, 18, 10, "iron"),       # the block that holds the head on
    ] + mirror_x(head, 16)
    def grain(p, n):
        return 0.85 if (int(p[0]) + int(p[2])) % 3 == 0 and abs(n[1]) < 0.5 else 1.0
    paints = {
        "wood": Paint(["4a3318", "6e4c25", "8c6634"], lo=0, hi=18, grain=0.05, rim=0.06, pattern=grain),
        "iron": Paint(["5e6064", "8f9296", "b9bcc0", "d4d6d9"], lo=9, hi=18, grain=0.035, rim=0.12),
        "tip": Paint(["8f9296", "c9cbce"], lo=9, hi=11, grain=0.03, rim=0.1),
    }
    return boxes, paints, "tool"


ITEMS = {"diamond_sword": sword, "iron_pickaxe": pickaxe, "apple": apple, "potion": potion}


def display(kind):
    """held so the whole model shows in first person, roughly where Minecraft holds its own items"""
    if kind == "blade":
        return K.hand_display(20, scale=0.44, lift=0.5)
    if kind == "tool":
        return K.hand_display(45, scale=0.48, lift=-0.5)
    return K.food_display(0.8)


if __name__ == "__main__":
    K.configure(sys.argv)
    K.white_texture()
    pics = []
    for name in (sorted(K.ONLY) if K.ONLY else list(ITEMS)):
        K.reset()
        boxes, paints, kind = ITEMS[name]()
        ob, clear = build(name, boxes, paints)
        K.bake_and_export(ob, name, display(kind), clear, particle=f"minecraft:item/{name}", soft=0.25)
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
