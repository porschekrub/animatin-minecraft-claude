#!/usr/bin/env python3
"""Lifelike Motion's 3D items: real chunky models of the actual things (in the spirit of Actions & Stuff), not the
game's flat item pictures made thick. Built from small blocks at HALF a Minecraft pixel (32 to a block), so shapes
can be round and detailed while still reading as blocky. Each item is painted by hand-tuned rules: colours flowing
smoothly across the model, crisp details where they matter (a wrapped grip, gem facets, a light streak across a
blade, speckles on an apple, a label on a bottle), light rims on top edges, darker undersides; Blender bakes soft
shadows on top. Weapons and tools are made to look cool; food, bottles and buckets to look beautiful.

Runs with Blender's Python module:  python3 tools/blender/blocky.py <pack dir> [names...] [--preview out.png]

Coordinates are in half-pixels, Minecraft's way: x right, y up, z toward the viewer (south); the block is 0..32 on
each axis, its middle at 16. Writes, for every item: the OBJ model, its item3d model (how it's held) and the item's
own model (3D in the hand and on the ground, the usual flat picture in the inventory).
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

RES = 32  # blocks per... model units per block (two to a Minecraft pixel)
DIRS = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]


def rgb(h):
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)) if isinstance(h, str) else tuple(h)


def lerp_ramp(ramp, t):
    t = min(max(t, 0.0), 1.0) * (len(ramp) - 1)
    i = min(int(t), len(ramp) - 2)
    f = t - i
    return np.array(ramp[i]) * (1 - f) + np.array(ramp[i + 1]) * f


def sq(x, z, p=4.0, cx=16, cz=16):
    """distance from the middle on a rounded square (p=2 a circle, higher = squarer with rounded corners):
    round things get big clean flat sides with bevelled corners, like a well-made block model"""
    return (abs(x - cx) ** p + abs(z - cz) ** p) ** (1 / p)


def hash01(*k):
    return random.Random(hash(k)).random()


# ---------------------------------------------------------------- paints
class Paint:
    """how one material is painted.
    ramp: colours (dark to light) flowing smoothly along `axis` from lo to hi (model units)
    rim / under: how much lighter the top edges / darker the bottom edges of each block are
    faces: tops a little lighter, undersides a little darker
    detail(p, n): per small face (p = its centre, n = its normal) -> None, a brightness factor, or (colour, amount)
                  to mix toward: the crisp, deliberate details
    shine(q, n) -> 0..1 of a soft white highlight, per corner (smooth)"""

    def __init__(self, ramp, axis=(0, 1, 0), lo=0, hi=32, rim=0.2, under=0.15, faces=0.1, detail=None,
                 shine=None, alpha=1.0, tint=-1, glow=False, round=None):
        self.ramp = [rgb(c) for c in ramp]
        self.axis, self.lo, self.hi = np.array(axis, float), lo, hi
        self.rim, self.under, self.faces = rim, under, faces
        self.detail, self.shine = detail, shine
        self.alpha, self.tint, self.glow = alpha, tint, glow
        self.round = round  # round(q, face normal) -> the smooth surface normal there (shading of round things)

    def corner(self, q, n, rim_kind, det):
        t = (np.dot(self.axis, q) - self.lo) / max(self.hi - self.lo, 1e-6)
        c = lerp_ramp(self.ramp, t)
        c = c * (1 + self.faces * n[1] + 0.05 * n[2] - 0.04 * n[0])
        if isinstance(det, tuple):
            col, a = det
            c = c * (1 - a) + np.array(rgb(col)) * a
        elif det is not None:
            c = c * det
        if rim_kind == "up":
            c = c + (1 - c) * self.rim
        elif rim_kind == "side":
            c = c + (1 - c) * self.rim * 0.45
        elif rim_kind == "down":
            c = c * (1 - self.under)
        if self.shine:
            c = c + (1 - c) * self.shine(q, n)
        return np.clip(c, 0, 1)


# ---------------------------------------------------------------- shapes
class Grid(dict):
    """voxels: (x, y, z) -> material"""

    def box(self, x0, y0, z0, x1, y1, z1, m):
        for x in range(x0, x1):
            for y in range(y0, y1):
                for z in range(z0, z1):
                    self[(x, y, z)] = m

    def where(self, pred, m, lo=(0, 0, 0), hi=(RES, RES, RES)):
        """every voxel whose centre passes pred(x, y, z) (centres are at +0.5)"""
        for x in range(lo[0], hi[0]):
            for y in range(lo[1], hi[1]):
                for z in range(lo[2], hi[2]):
                    if pred(x + 0.5, y + 0.5, z + 0.5):
                        self[(x, y, z)] = m

    def ring(self, y0, y1, r_in, r_out, m, cx=16, cz=16):
        self.where(lambda x, y, z: r_in <= math.hypot(x - cx, z - cz) <= r_out, m, (0, y0, 0), (RES, y1, RES))

    def disc(self, y0, y1, r, m, cx=16, cz=16):
        self.ring(y0, y1, -1, r, m, cx, cz)


def build(name, grid, paints):
    names = sorted({m for m in grid.values()})
    mats = {m: K.mat(m, attr="paint", edge=0.0, alpha=paints[m].alpha, tint=paints[m].tint, glow=paints[m].glow)
            for m in names}
    order = list(mats)
    bm = bmesh.new()
    paint = bm.loops.layers.float_color.new("paint")
    nrm = bm.loops.layers.float_color.new("nrm")
    clear = {m for m in names if paints[m].alpha < 1}
    s = 1 / RES
    for (x, y, z), m in grid.items():
        pm = paints[m]
        for d in DIRS:
            other = grid.get((x + d[0], y + d[1], z + d[2]))
            # a face shows where there's nothing next to it, or something see-through (but not glass to glass)
            if other is not None and not (other in clear and m not in clear):
                continue
            centre = np.array([x + 0.5, y + 0.5, z + 0.5])
            ax = [i for i in range(3) if d[i] == 0]
            open_side = {}
            for i in ax:
                for sgn in (-1, 1):
                    t = [0, 0, 0]
                    t[i] = sgn
                    beside = grid.get((x + t[0], y + t[1], z + t[2]))
                    over = grid.get((x + t[0] + d[0], y + t[1] + d[1], z + t[2] + d[2]))
                    open_side[(i, sgn)] = beside != m or over is not None
            fc = centre + 0.5 * np.array(d)
            det = pm.detail(fc, d) if pm.detail else None
            corners, cols, norms = [], [], []
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                q = fc.copy()
                q[ax[0]] += 0.5 * a
                q[ax[1]] += 0.5 * b
                kind = None
                for i, sgn in ((ax[0], a), (ax[1], b)):
                    if open_side[(i, sgn)]:
                        k = "up" if (i == 1 and sgn > 0) else "down" if (i == 1 and sgn < 0) else "side"
                        if kind is None or k == "up" or (k == "side" and kind == "down"):
                            kind = k
                if d[1] > 0 and kind == "side":
                    kind = "up"
                corners.append(q)
                sn = np.array(d, float)
                if pm.round:
                    v = np.array(pm.round(q, np.array(d, float)), float)
                    sn = v / (np.linalg.norm(v) or 1.0)
                    kind = None if kind != "up" or d[1] < 0.5 else kind
                norms.append(sn)
                cols.append(pm.corner(q, sn, kind, det))
            vs = [bm.verts.new((q[0] * s, 1 - q[2] * s, q[1] * s)) for q in corners]  # MC -> Blender axes
            f = bm.faces.new(vs)
            f.normal_update()
            if f.normal.dot((d[0], -d[2], d[1])) < 0:
                f.normal_flip()
            f.material_index = order.index(m)
            f.smooth = False
            for loop in f.loops:
                co = loop.vert.co
                qq = np.array([co.x / s, co.z / s, (1 - co.y) / s])
                j = int(np.argmin([np.sum((qq - c_) ** 2) for c_ in corners]))
                c = cols[j]
                lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
                loop[paint] = (*lin, 1.0)
                sn = norms[j]
                loop[nrm] = (sn[0], -sn[2], sn[1], 1.0)  # MC -> Blender axes
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    ob = K.obj_from_bm(name, bm, mats[order[0]], smooth=True)
    for m in order[1:]:
        ob.data.materials.append(mats[m])
    # each corner's shading normal: its face's own, or the smooth round surface's for round things
    me = ob.data
    buf = np.zeros(len(me.loops) * 4, dtype=np.float32)
    me.color_attributes["nrm"].data.foreach_get("color", buf)
    me.normals_split_custom_set([tuple(v) for v in buf.reshape(-1, 4)[:, :3]])
    me.color_attributes.remove(me.color_attributes["nrm"])
    return ob, bool(clear)


def ball(cx, cy, cz, rx, ry, rz, flat=0.35):
    """the smooth normal of a roundish body (ellipsoid), a little of each face's own kept so the blocks still read"""
    def f(q, n):
        v = np.array([(q[0] - cx) / rx ** 2, (q[1] - cy) / ry ** 2, (q[2] - cz) / rz ** 2])
        v = v / (np.linalg.norm(v) or 1.0)
        return v + flat * n
    return f


def can(cx=16, cz=16, flat=0.35, up=0.0):
    """the smooth normal of an upright round body (a bottle, a bucket): out from its middle (in, for inside walls)"""
    def f(q, n):
        r = np.array([q[0] - cx, 0.0, q[2] - cz])
        r = r / (np.linalg.norm(r) or 1.0)
        if abs(n[1]) > 0.5:
            return np.array(n) + 0.35 * r
        if np.dot(r, n) < 0:
            r = -r
        return r + flat * n + np.array([0, up, 0])
    return f


def blob(centre, radius, strength=0.55, core=0.0):
    """a soft round highlight: up to `strength`, fading out over `radius`; `core` adds a hard bright middle"""
    c = np.array(centre, float)
    def f(q, n):
        d = np.linalg.norm(np.array(q) - c)
        v = strength * max(0.0, 1 - d / radius) ** 1.5
        if core and d < radius * 0.28:
            v = max(v, core)
        return v
    return f


def streak(every=22, width=3, slope=0.7, amount=0.4, colour="ffffff", faces_only=None):
    """diagonal light streaks (polished metal, gems, glass)"""
    def f(p, n):
        if faces_only is not None and abs(n[faces_only]) < 0.5:
            return None
        v = (p[0] + p[1] * slope) % every
        return (colour, amount) if v < width else None
    return f


def combine(*fs):
    def f(p, n):
        out = None
        for g in fs:
            v = g(p, n)
            if v is not None:
                out = v
        return out
    return f


# ---------------------------------------------------------------- cool things
DIAMOND = ["082a24", "0e3f36", "15634f", "1e8a77", "2bc7ac", "33ebcb", "8ff5e4", "c8fff6"]
GOLD = ["6b4208", "a86f12", "e0a624", "f6d25a", "fff2b0"]


def gem_detail(p, n):
    """a cut gem: lit top-left facets, shadowed bottom-right, a white glint"""
    u = p[0] - p[1] if abs(n[2]) > 0.5 else p[2] - p[1]
    v = int(p[0] + p[1] + p[2]) % 3
    if v == 0:
        return ("ffffff", 0.55)
    return 0.8 if u > 0 else 1.15


def diamond_sword():
    g = Grid()
    # pommel: a round metal knob holding a gem that shows on both faces
    g.where(lambda x, y, z: ((x - 16) / 4.6) ** 2 + ((y - 4) / 4.2) ** 2 + ((z - 16) / 4.6) ** 2 <= 1, "fit",
            (8, 0, 8), (24, 9, 24))
    g.box(14, 2, 10, 18, 6, 22, "gem")
    g.box(13, 7, 13, 19, 9, 19, "gold")                              # collar
    g.box(13, 9, 13, 19, 19, 19, "grip")                             # wrapped grip
    # crossguard: a heavy middle, wings, tips sweeping up with gold caps, a gem on each face
    g.box(9, 19, 12, 23, 25, 20, "guard")
    g.box(3, 20, 13, 29, 24, 19, "guard")
    g.box(1, 22, 13, 5, 29, 19, "guard"), g.box(27, 22, 13, 31, 29, 19, "guard")
    g.box(1, 29, 14, 5, 31, 18, "gold"), g.box(27, 29, 14, 31, 31, 18, "gold")
    g.box(14, 20, 11, 18, 24, 21, "gem")
    # blade: a raised middle ridge, flats, bright sharp edges, tapering to a point
    for y in range(25, 58):
        w = 7 if y < 45 else round(7 * (58 - y) / 13)
        for x in range(16 - w, 16 + w):
            dx = abs(x + 0.5 - 16)
            m = "edge" if dx > w - 1.01 or w <= 1 else "blade"
            z0, z1 = (14, 18) if dx < 2 and w > 2 else (15, 17)
            for z in range(z0, z1):
                g[(x, y, z)] = m
    def blade_detail(p, n):
        dx = abs(p[0] - 16)
        if abs(n[2]) > 0.5 and dx < 0.6:
            return ("e8fffb", 0.55)                                  # the ridge's bright spine
        if abs(n[2]) > 0.5 and 26 <= p[1] <= 33 and dx in (3.5, 4.5) and int(p[1]) % 2 == 0:
            return ("0b332c", 0.6)                                   # small runes near the guard
        return streak(26, 4, 0.8, 0.45, "e8fffb", faces_only=2)(p, n)
    def wrap(p, n):
        side = p[0] if abs(n[2]) > 0.5 else p[2]
        return 0.62 if int((p[1] + side) / 2) % 2 == 0 else 1.05
    paints = {
        "blade": Paint(DIAMOND[2:], lo=25, hi=58, rim=0.25, detail=blade_detail),
        "edge": Paint(["7fefdc", "c9fff6", "ffffff"], lo=25, hi=58, rim=0.15),
        "guard": Paint(DIAMOND[:5], lo=19, hi=31, rim=0.38, detail=streak(18, 2, 0.4, 0.3, "8ff5e4", faces_only=2)),
        "gold": Paint(GOLD, lo=7, hi=31, rim=0.4),
        "fit": Paint(DIAMOND[:4], lo=0, hi=9, rim=0.35),
        "gem": Paint(["33ebcb", "8ff5e4", "e6fffb"], lo=0, hi=24, rim=0.3, detail=gem_detail, glow=True),
        "grip": Paint(["24150a", "3d2612", "5a3b1e", "6e4c25"], lo=9, hi=19, rim=0.15, detail=wrap),
    }
    return g, paints, "blade"


def diamond_axe():
    g = Grid()
    g.box(14, 0, 14, 18, 52, 18, "wood")                             # handle
    g.box(13, 0, 13, 19, 3, 19, "gold")                              # end cap
    g.box(13, 5, 13, 19, 20, 19, "wrap")                             # leather grip
    g.box(13, 20, 13, 19, 22, 19, "gold")
    g.box(12, 35, 12, 20, 50, 20, "head")                            # socket
    g.box(13, 33, 13, 19, 35, 19, "gold")                            # ring under the head
    g.box(14, 50, 14, 18, 54, 18, "gem")                             # a gem capping the handle
    g.box(14, 40, 11, 18, 44, 21, "gold")                            # a rivet through the socket
    g.box(20, 37, 13, 26, 48, 19, "head")                            # neck
    # the blade fans out to a long, curved, bright cutting edge
    for x in range(26, 44):
        t = (x - 26) / 17
        h = 5.5 + 12 * t ** 0.85
        c = 42.5 + 1.5 * t
        thick = (14, 18) if x < 33 else (15, 17)
        for y in range(int(c - h), int(c + h) + 1):
            if not (0 <= y < 64):
                continue
            m = "edge" if x >= 40 else "head"
            for z in range(*thick):
                g[(x, y, z)] = m
    # the back spike
    for x in range(3, 12):
        h = 0.5 + 2.5 * (x - 3) / 8
        for y in range(int(42.5 - h), int(42.5 + h) + 1):
            for z in range(15, 17):
                g[(x, y, z)] = "edge" if x < 5 else "head"
    def grain(p, n):
        if abs(n[1]) > 0.5:
            return None
        side = p[0] if abs(n[2]) > 0.5 else p[2]
        return 0.8 if (int(side) * 7 + int(p[1] / 6)) % 5 == 0 else None
    def wrap(p, n):
        side = p[0] if abs(n[2]) > 0.5 else p[2]
        return 0.62 if int((p[1] - side) / 2) % 2 == 0 else 1.05
    def head_detail(p, n):
        if abs(n[2]) > 0.5 and 36 <= p[0] < 40:
            return ("8ff5e4", 0.35)                                  # a bevel before the edge
        return streak(24, 4, -0.9, 0.4, "e8fffb", faces_only=2)(p, n)
    paints = {
        "wood": Paint(["3b2611", "5a3d1c", "7a5428", "966a35"], lo=0, hi=52, rim=0.18, detail=grain),
        "wrap": Paint(["24150a", "3d2612", "5a3b1e"], lo=5, hi=20, rim=0.15, detail=wrap),
        "gold": Paint(GOLD, lo=0, hi=54, rim=0.4),
        "head": Paint(DIAMOND[1:7], axis=(1, 0, 0), lo=3, hi=42, rim=0.35, detail=head_detail),
        "edge": Paint(["8ff5e4", "d6fff8", "ffffff"], axis=(1, 0, 0), lo=36, hi=44, rim=0.15),
        "gem": Paint(["33ebcb", "8ff5e4", "e6fffb"], lo=50, hi=54, rim=0.3, detail=gem_detail, glow=True),
    }
    return g, paints, "tool"


# ---------------------------------------------------------------- beautiful things
def apple():
    g = Grid()
    def inside(x, y, z):
        r = sq(x, z, 3.0)
        if r > 12.6:
            return False
        k = max(0.0, 1 - (r / 12.6) ** 3) ** (1 / 3)                  # flat-ish top and bottom, rounded shoulders
        top = 14 + 11 * k - 3.0 * math.exp(-(r / 3.4) ** 2)          # dimpled where the stem grows
        bot = 14 - 10.5 * k + 1.6 * math.exp(-(r / 2.6) ** 2)
        return bot <= y <= top
    g.where(inside, "skin")
    # a little star of dried flower at the bottom
    g.where(lambda x, y, z: y < 6 and math.hypot(x - 16, z - 16) < 2.2, "calyx", (0, 2, 0), (32, 6, 32))
    # a curved stem
    for y in range(19, 31):
        cx = 16 + int(round(3.2 * ((y - 19) / 11) ** 2))
        g.box(cx - 1, y, 15, cx + 1, y + 1, 17, "stem")
    # a leaf with a fold down the middle, lifting at the tip
    for u in range(0, 10):
        w = 4.4 * math.sin(math.pi * (u + 0.5) / 10) ** 0.8
        x = 18 + u
        yb = 27 + int(round(0.25 * u + 0.02 * u * u))
        for z in range(int(round(16 - w)), int(round(16 + w))):
            fold = int(abs(z + 0.5 - 16) > 1.6 and abs(z + 0.5 - 16) > w * 0.6)
            g[(x, yb + fold, z)] = "leaf"
    def skin_detail(p, n):
        ang = math.atan2(p[2] - 16, p[0] - 16)
        if hash01("dot", int(p[0]), int(p[1]), int(p[2]), tuple(n)) < 0.015 and p[1] > 6 and abs(n[1]) < 0.5:
            return ("ffd9b0", 0.5)                                    # speckles
        st = math.sin(ang * 9 + 0.6 * math.sin(p[1] * 0.4)) * 0.5 + 0.5
        if st > 0.72 and p[1] > 9:
            return ("f7a052", 0.22 * (st - 0.72) / 0.28 + 0.1)        # streaks of sun colour
        return None
    def leaf_detail(p, n):
        if abs(p[2] - 16) < 0.6:
            return ("b8f27a", 0.45)                                   # the vein
        return 0.85 if abs(p[2] - 16) > 2.5 else None
    paints = {
        "skin": Paint(["5e0910", "8e1018", "c41c24", "e1302c", "e9412f", "f06a3c"], lo=3, hi=25, rim=0.05,
                      under=0.05, detail=skin_detail, shine=blob((9, 20, 27), 8, 0.5, core=0.72),
                      round=ball(16, 14, 16, 12.6, 11, 12.6)),
        "calyx": Paint(["3d2a12", "6b5a26"], rim=0.1),
        "stem": Paint(["2e1c0c", "5a3a1c", "7a5530"], lo=19, hi=31, rim=0.3),
        "leaf": Paint(["2a6a1c", "45962a", "6fc244", "96df62"], axis=(1, 0, 0), lo=18, hi=28, rim=0.3,
                      detail=leaf_detail),
    }
    return g, paints, "food"


def potion():
    """a round glass bottle you can see the potion through (coloured by the game: blue for water), a paper label,
    string round the neck and a cork"""
    g = Grid()
    def R(y):
        if y < 3:
            return 7.6
        if y < 17:
            return 9.0
        if y < 23:
            return 3.6 + 5.4 * math.cos((y - 17) / 6 * math.pi / 2)
        return 3.6
    def glass_at(x, y, z):
        r = sq(x, z, 3.0) if y < 23 else math.hypot(x - 16, z - 16)
        if y < 2 or y > 30:
            return False
        if y > 28:
            return r <= 4.6 and r > 2.6                               # the lip
        return r <= R(y) and (r > R(y) - 1.1 or y < 3)
    g.where(lambda x, y, z: sq(x, z, 3.0) <= R(y) - 1.4 and 3 <= y <= 15, "potion")
    g.where(glass_at, "glass")
    # a paper label on the front
    g.where(lambda x, y, z: 7 <= y <= 13 and z > 16 and glass_at(x, y, z) and abs(x - 16) < 6.5, "label")
    g.disc(27, 37, 2.9, "cork")
    g.disc(35, 37, 3.4, "cork")
    g.ring(24, 26, 3.4, 4.7, "string")
    g.box(20, 19, 15, 21, 25, 17, "string")                           # its loose end
    def label_detail(p, n):
        dx, dy = p[0] - 16, p[1] - 10
        if abs(dy) > 2.6 or abs(dx) > 5.2:
            return ("8a6a3c", 0.45)                                   # the border
        if (dx / 1.4) ** 2 + ((dy + 0.4) / 1.7) ** 2 < 1 or (abs(dx) < 0.6 and 0.6 < dy < 2.2):
            return ("2f74e0", 0.85)                                   # a drop
        return None
    def liquid_detail(p, n):
        if n[1] > 0.5:
            return ("ffffff", 0.35)                                   # the surface
        if hash01("bub", int(p[0]), int(p[1]), int(p[2])) < 0.05 and p[1] < 14:
            return ("ffffff", 0.5)                                    # bubbles
        return None
    def glass_detail(p, n):
        ang = math.atan2(p[2] - 16, p[0] - 16)
        if 2.0 < ang < 2.45 and p[1] > 4:
            return ("ffffff", 0.75)                                   # a tall highlight down the front-left
        return None
    paints = {
        "glass": Paint(["9fc4dc", "c8e4f4", "eef9ff"], lo=2, hi=31, rim=0.25, under=0.0, alpha=0.36,
                       detail=glass_detail, round=can()),
        "potion": Paint([(0.48, 0.48, 0.48), (0.75, 0.75, 0.75), (0.95, 0.95, 0.95)], lo=3, hi=16, rim=0.2, tint=0,
                        detail=liquid_detail, round=can()),
        "label": Paint(["e8d8b0", "f7eed2"], lo=7, hi=14, rim=0.15, detail=label_detail, round=can(flat=0.6)),
        "string": Paint(["a8874e", "d8bf88"], rim=0.25),
        "cork": Paint(["7a4f28", "a87545", "d0a36a"], lo=27, hi=37, rim=0.3,
                      detail=lambda p, n: 0.82 if hash01("ck", int(p[0]), int(p[1]), int(p[2])) < 0.25 else None),
    }
    return g, paints, "food"


def water_bucket():
    """a round iron bucket, wider at the top, with a rolled rim, two bands and rivets, side lugs, a curved carry
    handle with a wooden grip, and clear water with ripples"""
    g = Grid()
    def r_out(y):
        return 11.8  # straight walls: clean sides
    g.where(lambda x, y, z: sq(x, z) <= r_out(y) and (sq(x, z) > r_out(y) - 1.6 or y < 4), "iron",
            (0, 2, 0), (32, 22, 32))
    g.where(lambda x, y, z: sq(x, z) <= r_out(y) - 1.6, "water", (0, 4, 0), (32, 18, 32))
    g.where(lambda x, y, z: r_out(y) - 2.2 < sq(x, z) <= r_out(y) + 1.0, "rim", (0, 21, 0), (32, 23, 32))
    for y0 in (5, 14):
        g.where(lambda x, y, z: r_out(y) - 1.6 < sq(x, z) <= r_out(y) + 0.7, "band", (0, y0, 0), (32, y0 + 2, 32))
    # rivets on the bands, front and sides
    for y0 in (5, 14):
        for (x, z) in ((11, 28), (21, 28), (4, 16), (28, 16)):
            for xx in range(x - 1, x + 1):
                for zz in range(z - 1, z + 1):
                    if sq(xx + 0.5, zz + 0.5) > r_out(y0) - 0.5:
                        g.box(xx, y0, zz, xx + 1, y0 + 2, zz + 1, "rivet")
    # lugs and the carry handle arching over the top
    g.box(1, 17, 15, 5, 22, 17, "rim"), g.box(27, 17, 15, 31, 22, 17, "rim")
    for k in range(0, 181, 2):
        a = math.radians(k)
        x, y = 16 + 13.5 * math.cos(a), 20 + 15 * math.sin(a)
        grip = 65 <= k <= 115
        m = "grip" if grip else "handle"
        w = 2 if grip else 1
        g.box(int(x) - (w - 1), int(y) - (w - 1), 16 - w, int(x) + 1, int(y) + 1, 16 + w, m)
    def iron_detail(p, n):
        r = math.hypot(p[0] - 16, p[2] - 16)
        if abs(n[1]) < 0.5 and (n[0] * (p[0] - 16) + n[2] * (p[2] - 16)) < 0:
            return 0.62                                               # inside walls, in shade
        if n[2] > 0.5 and 9 <= p[0] <= 11:
            return ("ffffff", 0.4)                                    # a bright reflection running down the front
        return None
    def water_detail(p, n):
        if n[1] < 0.5:
            return None
        r = sq(p[0], p[2], 2.5)
        if 2.5 < r < 3.5 or 6.0 < r < 7.0:
            return ("cfe9ff", 0.45)                                   # ripples
        return None
    paints = {
        "iron": Paint(["6c7076", "9a9ea4", "c4c7cb", "e6e8ea"], lo=2, hi=23, rim=0.2, detail=iron_detail,
                      round=can()),
        "rim": Paint(["8f9399", "c9ccd0", "e6e8ea"], lo=17, hi=23, rim=0.2, round=can(flat=0.6)),
        "band": Paint(["4c5056", "6e7278", "8a8e94"], lo=5, hi=16, rim=0.25, round=can(flat=0.6)),
        "rivet": Paint(["c9ccd0", "ffffff"], rim=0.3),
        "handle": Paint(["5a5e64", "8e9298", "b6b9bd"], lo=20, hi=36, rim=0.3),
        "grip": Paint(["6b4424", "8f6133", "b5834a"], lo=32, hi=36, rim=0.3),
        "water": Paint(["1b4fb8", "2f74e0", "5aa0f4"], lo=4, hi=18, rim=0.0, detail=water_detail,
                       shine=blob((12, 18, 13), 5, 0.5)),
    }
    return g, paints, "food"


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
        return K.hand_display(20, scale=0.34, lift=0.0)
    if kind == "tool":
        return K.hand_display(45, scale=0.4, lift=-0.5)
    return upright(**HELD.get(name, {}))


# per item: how big it's held (things wider than an apple a bit smaller)
HELD = {"apple": {"scale": 0.34, "lift": 4.0}, "water_bucket": {"scale": 0.3, "lift": 5.0},
        "potion": {"scale": 0.34, "lift": 5.0}}


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
        grid, paints, kind = ITEMS[name]()
        ob, clear = build(name, grid, paints)
        K.bake_and_export(ob, name, display(kind, name), clear, particle=f"minecraft:item/{name}", ao_blur=2.5 / RES)
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
