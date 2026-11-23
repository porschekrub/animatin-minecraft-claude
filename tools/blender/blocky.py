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
    """how one material is painted, pixel-art style: a short palette of tones (dark to light). Each pixel picks ONE
    tone from: where it sits along a direction, soft clustered noise (patches of lighter and darker pixels), which way
    its face points (tops lighter, undersides darker), and its place on the box (a light rim along top edges, a dark
    one along bottom edges). Optional sparkles (single bright pixels) and a pattern(pixel, normal) -> tone shift."""

    def __init__(self, ramp, axis=(0, 1, 0), lo=0, hi=16, clusters=0.7, scale=2.5, rim=0.8, faces=0.6,
                 pattern=None, sparkle=0.0, alpha=1.0, tint=-1, glow=False, seed=0):
        self.ramp = [rgb(c) if isinstance(c, str) else c for c in ramp]
        self.axis, self.lo, self.hi = np.array(axis, float), lo, hi
        self.clusters, self.scale, self.rim, self.faces = clusters, scale, rim, faces
        self.pattern, self.sparkle = pattern, sparkle
        self.alpha, self.tint, self.glow, self.seed = alpha, tint, glow, seed

    def noise(self, p):
        """smooth value noise in [-1, 1] over pixel positions: patches a few pixels wide"""
        q = np.array(p) / self.scale
        i = np.floor(q).astype(int)
        f = q - i
        f = f * f * (3 - 2 * f)
        def h(c):
            return random.Random(hash((self.seed, c[0], c[1], c[2]))).random() * 2 - 1
        out = 0.0
        for dx in (0, 1):
            for dy in (0, 1):
                for dz in (0, 1):
                    w = (f[0] if dx else 1 - f[0]) * (f[1] if dy else 1 - f[1]) * (f[2] if dz else 1 - f[2])
                    out += w * h((i[0] + dx, i[1] + dy, i[2] + dz))
        return out

    def at(self, p, n, edges, rnd):
        top = len(self.ramp) - 1
        t = (np.dot(self.axis, p) - self.lo) / max(self.hi - self.lo, 1e-6)
        k = min(max(t, 0.0), 1.0) * top
        k += self.clusters * self.noise(p) * 1.4
        k += self.faces * (n[1] - 0.25 * n[0] + 0.25 * n[2])  # light from above, a little from the front-left
        if "up" in edges:
            k += self.rim
        elif "down" in edges:
            k -= self.rim * 0.7
        elif edges:
            k += self.rim * 0.4
        if self.pattern:
            k += self.pattern(p, n)
        i = int(round(min(max(k, 0), top)))
        c = np.array(self.ramp[i])
        if self.sparkle and rnd.random() < self.sparkle:
            c = np.clip(c * 0.4 + 0.6, 0, 1)
        return c


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
            edges = set()
            for t in tang:
                if grid.get((x + t[0], y + t[1], z + t[2])) != m or \
                        grid.get((x + t[0] + d[0], y + t[1] + d[1], z + t[2] + d[2])) is not None:
                    edges.add("up" if t == (0, 1, 0) else "down" if t == (0, -1, 0) else "side")
            centre = np.array([x + 0.5, y + 0.5, z + 0.5])
            col = paints[m].at(centre, d, edges, rnd)
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
    """a squared-off apple: a chunky core with every side bevelled in a step, a stem in a little hollow, a leaf"""
    R = "skin"
    boxes = [
        (4, 2, 4, 12, 10, 12, R),        # core
        (3, 3, 5, 13, 9, 11, R), (5, 3, 3, 11, 9, 13, R),  # sides stepped in
        (5, 10, 5, 11, 11, 11, R), (5, 1, 5, 11, 2, 11, R),  # top and bottom
        (7, 10, 7, 9, 11, 9, "dip"),
        (7, 11, 7, 8, 14, 8, "stem"), (8, 13, 7, 9, 14, 8, "stem"),
        (8, 12, 8, 12, 13, 9, "leaf"), (9, 13, 8, 11, 14, 9, "leaf"),
    ]
    def shine(p, n):
        # a patch of bright pixels where the light catches the upper front-left
        return 1.6 if (p[1] > 7 and p[0] < 7 and p[2] > 8 and (n[2] > 0 or n[0] < 0 or n[1] > 0)) else 0.0
    paints = {
        R: Paint(["5a0a12", "8c1018", "bd1b22", "dd2c2c", "f04b3a", "ff8566"], lo=1, hi=12, clusters=0.6,
                 pattern=shine, seed=1),
        "dip": Paint(["4a080d", "6e0f12"], clusters=0.2, rim=0, faces=0.3),
        "stem": Paint(["2e1c0c", "4d3218", "6e4c25"], lo=11, hi=14, clusters=0.3, rim=0.5),
        "leaf": Paint(["24501a", "357a22", "4f9e2c", "74c442"], axis=(1, 0, 0), lo=8, hi=12, clusters=0.5, seed=3),
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
        "glass": Paint(["8fb6cf", "b8d8ec", "dcf0fb", "ffffff"], lo=1, hi=11, clusters=0.3, rim=1.2, alpha=0.42),
        "potion": Paint([(0.5, 0.5, 0.5), (0.68, 0.68, 0.68), (0.85, 0.85, 0.85), (1.0, 1.0, 1.0)], lo=2, hi=6,
                        clusters=0.5, tint=0, seed=5),
        "cork": Paint(["6b4524", "8f6133", "b5834a", "d6a86c"], lo=10, hi=13, clusters=0.8, scale=1.5, seed=6),
    }
    return boxes, paints, "food"


def sword():
    """standing up: a pommel stone, a wrapped grip, a guard with raised tips, a blade with bright edges and a point"""
    boxes = [
        (6, 0, 7, 10, 2, 9, "gem"), (7, 0, 6, 9, 2, 10, "gem"),       # pommel
        (7, 2, 7, 9, 7, 9, "grip"),
        (3, 7, 6, 13, 9, 10, "guard"),
        (2, 8, 7, 3, 11, 9, "guard"), (13, 8, 7, 14, 11, 9, "guard"),  # raised tips
        (7, 8, 5, 9, 10, 6, "gem"), (7, 8, 10, 9, 10, 11, "gem"),     # a stone on each face of the guard
        (6, 9, 7, 10, 22, 9, "blade"),
        (5, 9, 7, 6, 20, 9, "edge"), (10, 9, 7, 11, 20, 9, "edge"),
        (6, 22, 7, 10, 24, 9, "blade"), (7, 24, 7, 9, 26, 9, "blade"), (5, 20, 7, 6, 21, 9, "edge"),
        (10, 20, 7, 11, 21, 9, "edge"),
    ]
    def wrap(p, n):
        return -1.2 if int(p[1]) % 2 == 0 else 0.0
    def groove(p, n):
        return -1.5 if 7 <= p[0] < 9 and abs(n[2]) > 0 and p[1] < 21 else 0.0
    paints = {
        "blade": Paint(["0e3f36", "15634f", "1e8a77", "2bc7ac", "33ebcb", "a4fdf0"], lo=9, hi=26, clusters=0.5,
                       pattern=groove, sparkle=0.04, seed=7),
        "edge": Paint(["4fd9c0", "a4fdf0", "e6fffb"], lo=9, hi=21, clusters=0.3, rim=0.3, sparkle=0.05),
        "guard": Paint(["0a2e28", "0e3f36", "15634f", "1e8a77", "2bc7ac"], lo=7, hi=11, clusters=0.5, seed=8),
        "gem": Paint(["1e8a77", "33ebcb", "a4fdf0", "ffffff"], lo=0, hi=11, clusters=0.4, sparkle=0.08),
        "grip": Paint(["2e1c0c", "4a3018", "68481f", "8a6630"], lo=2, hi=7, clusters=0.4, pattern=wrap, rim=0.4),
    }
    return boxes, paints, "blade"


def pickaxe():
    """a wooden handle with an iron cap, an iron block holding the head, and two arms stepping down to points"""
    head = [
        (10, 14, 7, 13, 17, 9, "iron"), (13, 13, 7, 15, 16, 9, "iron"), (15, 11, 7, 17, 14, 9, "iron"),
        (16, 9, 7, 17, 11, 9, "tip"),
    ]
    boxes = [
        (7, 0, 7, 9, 18, 9, "wood"),
        (6, 0, 6, 10, 1, 10, "iron"),
        (6, 14, 6, 10, 18, 10, "iron"),
    ] + mirror_x(head, 16)
    def grain(p, n):
        # streaks running along the handle
        return -1.0 if (int(p[0]) * 7 + int(p[2]) * 3 + int(p[1] / 4)) % 4 == 0 and abs(n[1]) < 0.5 else 0.0
    paints = {
        "wood": Paint(["3b2611", "553a1a", "6e4c25", "8a6332", "a47a40"], lo=0, hi=18, clusters=0.4, pattern=grain,
                      seed=9),
        "iron": Paint(["44464a", "65686c", "8a8d91", "aeb1b4", "cfd1d3", "eceeef"], lo=9, hi=18, clusters=0.45,
                      seed=10),
        "tip": Paint(["8a8d91", "cfd1d3", "f6f7f8"], lo=9, hi=11, clusters=0.3),
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
