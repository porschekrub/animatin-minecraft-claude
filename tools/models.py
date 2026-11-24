#!/usr/bin/env python3
"""Lifelike Motion's 3D items, made the way a pro Minecraft modeler does it in Blockbench: each item is a handful of
well-shaped parts (boxes, some turned), and every face is hand-painted pixel art at Minecraft's own detail (16 pixels
to a block). The painting is done here by rules tuned per material: a small hand-picked palette per material, light
from above, a one-pixel bevel (light top and left rims, dark bottom and right), clean details (a ridge down a blade,
a wrapped grip, gem facets, string round a bottle's neck) and soft shadows painted in wherever parts meet (each texel looks
around for nearby parts).

Writes plain Minecraft item models (assets/lifelikemotion/models/item3d/<name>.json), one texture per item
(assets/lifelikemotion/textures/item/model/<name>.png), and the item's own model (our model in the hand and on the
ground, the usual flat picture in the inventory).        python3 tools/models.py [names...]
"""
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image

PACK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "main", "resources", "resourcepacks",
                    "lifelike_3d_items")
NS = "lifelikemotion"
ANGLES = (-45, -22.5, 0, 22.5, 45)
FACES = ("north", "south", "east", "west", "up", "down")
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0),
          "down": (0, -1, 0)}


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# ---------------------------------------------------------------- materials
class Mat:
    """a material: its palette (dark to light, hand-picked), which palette step is its middle, its kind of surface
    (which decides the pattern) and how strongly it's bevelled"""

    def __init__(self, pal, base=None, kind="plain", bevel=1.0, alpha=255, tint=False, glow=False, grad=1.0, shine=1.0):
        self.pal = [hexc(c) for c in pal]
        self.base = (len(self.pal) - 1) / 2 if base is None else base
        self.kind, self.bevel, self.alpha, self.tint, self.glow, self.grad = kind, bevel, alpha, tint, glow, grad
        self.shine = shine


# ---------------------------------------------------------------- the face painter
LIFT = {"up": 1.0, "down": -1.3, "north": -0.1, "south": 0.15, "east": -0.35, "west": 0.25}


def paint_face(mat, face, w, h, seed, decal=None):
    """one face's pixel art as palette steps (h rows of w; row 0 is the face's top / north edge)"""
    rnd = random.Random(seed)
    side = face not in ("up", "down")
    k = np.full((h, w), mat.base + LIFT[face], float)
    jj, ii = np.mgrid[0:h, 0:w]
    if side and h > 2:
        k += mat.grad * (0.5 - (jj + 0.5) / h) * 1.4                     # lit from above
    if mat.kind == "metal" or mat.kind == "blade":
        d = (ii + jj * 0.8) / max(w + h * 0.8, 1)
        k += mat.shine * (1.5 * np.exp(-((d - 0.3) / 0.08) ** 2) + 0.6 * np.exp(-((d - 0.58) / 0.05) ** 2) - 0.35)
    elif mat.kind == "gem":
        u = (ii + 0.5) / w - 0.5
        v = (jj + 0.5) / h - 0.5
        k += np.where(u + v < 0, 0.9, -0.6)                              # lit facets top-left, shaded bottom-right
        k += np.where((np.abs(u - v) < 0.18) & (u + v < 0), 0.8, 0)
    elif mat.kind == "wood":
        phase = rnd.random() * 6
        streaks = np.sin((ii if side else jj) * 2.1 + phase + 0.6 * np.sin(jj * 0.7 + phase))
        k += np.where(streaks > 0.55, -0.9, np.where(streaks < -0.8, 0.5, 0))
    elif mat.kind == "wrap":
        k += np.where((ii + jj) % 3 == 0, 1.0, np.where((ii + jj) % 3 == 2, -1.0, 0.1))
    elif mat.kind == "organic":
        k += np.array([[0.7 * (rnd.random() < 0.06) - 0.7 * (rnd.random() < 0.05) for _ in range(w)] for _ in range(h)])
    elif mat.kind == "glass":
        k += np.where(ii == 1, 1.5, 0) if w > 3 else 0                   # a tall highlight
    # bevel: a light rim along the top and left, a dark one along the bottom and right
    if mat.bevel and w >= 3 and h >= 3:
        rim = np.zeros((h, w))
        rim[0, :] += 1.0
        rim[-1, :] -= 0.9
        if side:
            soft = 0.15 if mat.kind == "organic" else 1.0
            rim[:, 0] += 0.5 * soft
            rim[:, -1] -= 0.5 * soft
        else:
            rim[:, 0] += 0.5
            rim[:, -1] += 0.3
        k += rim * mat.bevel
    if decal:
        k = decal(k, ii, jj, w, h, face)
    return k


# ---------------------------------------------------------------- models
class Model:
    def __init__(self, name):
        self.name = name
        self.els = []

    def box(self, frm, to, mat, rot=None, faces=None, decal=None, ao=True):
        """a part from frm to to (pixels, 16 a block); rot = (angle, axis, origin); decal(k, i, j, w, h, face) -> k"""
        if rot:
            assert rot[0] in ANGLES, rot
        self.els.append({"frm": list(frm), "to": list(to), "mat": mat, "rot": rot, "faces": faces, "decal": decal,
                         "ao": ao})

    # -------------------------------------------------- soft shadows where parts meet
    def occlusion(self, ei, face, w, h):
        """per texel of one face: how much of the space just in front of it is filled by other parts (0..1)"""
        e = self.els[ei]
        frm, to = np.array(e["frm"], float), np.array(e["to"], float)
        n = np.array(NORMAL[face], float)
        # the face's corner and its two in-plane directions (texel i across, j down), matching the uv layout
        if face == "north":
            o, U, V = np.array([to[0], to[1], frm[2]]), (-1, 0, 0), (0, -1, 0)
        elif face == "south":
            o, U, V = np.array([frm[0], to[1], to[2]]), (1, 0, 0), (0, -1, 0)
        elif face == "east":
            o, U, V = np.array([to[0], to[1], to[2]]), (0, 0, -1), (0, -1, 0)
        elif face == "west":
            o, U, V = np.array([frm[0], to[1], frm[2]]), (0, 0, 1), (0, -1, 0)
        elif face == "up":
            o, U, V = np.array([frm[0], to[1], frm[2]]), (1, 0, 0), (0, 0, 1)
        else:
            o, U, V = np.array([frm[0], frm[1], to[2]]), (1, 0, 0), (0, 0, -1)
        U, V = np.array(U, float), np.array(V, float)
        su = abs(np.dot(to - frm, np.abs(U))) / w
        sv = abs(np.dot(to - frm, np.abs(V))) / h
        others = [(np.array(x["frm"], float), np.array(x["to"], float)) for k, x in enumerate(self.els)
                  if k != ei and not x["rot"] and x["mat"].alpha == 255]
        if e["rot"] or not others:
            return np.zeros((h, w))
        dirs = []
        rnd = random.Random(7)
        for _ in range(24):
            a, b = rnd.random() * 2 * math.pi, math.sqrt(rnd.random())
            t1 = np.cross(n, [0.3, 1, 0.2] if abs(n[1]) < 0.9 else [1, 0.2, 0.3])
            t1 /= np.linalg.norm(t1)
            t2 = np.cross(n, t1)
            dirs.append(b * math.cos(a) * t1 + b * math.sin(a) * t2 + math.sqrt(1 - b * b) * n)
        dirs = np.array(dirs)
        out = np.zeros((h, w))
        for j in range(h):
            for i in range(w):
                p = o + U * (i + 0.5) * su + V * (j + 0.5) * sv + n * 0.02
                hits = 0.0
                for d in dirs:
                    inv = 1.0 / np.where(np.abs(d) < 1e-9, 1e-9, d)
                    best = None
                    for (lo, hi) in others:
                        t0, t1_ = (lo - p) * inv, (hi - p) * inv
                        tn, tf = np.max(np.minimum(t0, t1_)), np.min(np.maximum(t0, t1_))
                        if tf >= max(tn, 0) and tn < 2.5:
                            best = tn if best is None else min(best, tn)
                    if best is not None:
                        hits += 1 - max(best, 0) / 2.5
                out[j, i] = hits / len(dirs)
        return out

    def write(self, display, translucent=False, particle=None, gui_light=None):
        dims = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}
        pieces = []
        for ei, e in enumerate(self.els):
            size = [abs(e["to"][a] - e["frm"][a]) for a in range(3)]
            for face, (a, b) in dims.items():
                if e["faces"] and face not in e["faces"]:
                    continue
                w, h = max(1, math.ceil(size[a] - 1e-6)), max(1, math.ceil(size[b] - 1e-6))
                pieces.append((ei, face, w, h))
        for T in (16, 32, 64, 128):
            place, x, y, shelf, ok = {}, 0, 0, 0, True
            for ei, face, w, h in sorted(pieces, key=lambda p: (-p[3], -p[2])):
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
        for ei, e in enumerate(self.els):
            mat = e["mat"]
            el = {"from": e["frm"], "to": e["to"], "faces": {}}
            if e["rot"]:
                el["rotation"] = {"angle": e["rot"][0], "axis": e["rot"][1], "origin": list(e["rot"][2])}
            for face in FACES:
                if (ei, face) not in place:
                    continue
                x, y, w, h = place[(ei, face)]
                k = paint_face(mat, face, w, h, seed=ei * 31 + FACES.index(face), decal=e["decal"])
                occ = self.occlusion(ei, face, w, h) if e["ao"] else np.zeros((h, w))
                pal = mat.pal
                for j in range(h):
                    for i in range(w):
                        idx = int(round(min(max(k[j, i], 0), len(pal) - 1)))
                        c = np.array(pal[idx], float) * (1 - 0.55 * occ[j, i])
                        a = mat.alpha
                        if mat.kind == "glass" and (i == 1 or j == 0) and w > 3:
                            a = min(255, a + 60)
                        tex.putpixel((x + i, y + j), (*[int(round(v)) for v in c], a))
                f = {"uv": [x * 16 / T, y * 16 / T, (x + w) * 16 / T, (y + h) * 16 / T], "texture": "#0"}
                if mat.tint:
                    f["tintindex"] = 0
                el["faces"][face] = f
            if mat.glow:
                el["forge_data"] = {"block_light": 15, "sky_light": 15}
            els.append(el)
        tp = os.path.join(PACK, "assets", NS, "textures", "item", "model", self.name + ".png")
        os.makedirs(os.path.dirname(tp), exist_ok=True)
        tex.save(tp)
        model = {"textures": {"0": f"{NS}:item/model/{self.name}", "particle": particle or vanilla_layers(self.name)[-1]},
                 "elements": els, "display": display}
        if gui_light:
            model["gui_light"] = gui_light
        if translucent:
            model["render_type"] = "minecraft:translucent"
        mp = os.path.join(PACK, "assets", NS, "models", "item3d", self.name + ".json")
        os.makedirs(os.path.dirname(mp), exist_ok=True)
        with open(mp, "w") as fh:
            json.dump(model, fh, separators=(",", ":"))
        return T


# ---------------------------------------------------------------- how items sit in the hand
def blade_held(turn=20, scale=0.34, lift=0.0, tp=0.85):
    """a sword or tool standing up in the model, held tilted forward like Minecraft's own"""
    return {
        "thirdperson_righthand": {"rotation": [0, -90, 55 + turn], "translation": [0, 4.0 + lift, 0.5], "scale": [tp] * 3},
        "thirdperson_lefthand": {"rotation": [0, 90, -55 - turn], "translation": [0, 4.0 + lift, 0.5], "scale": [tp] * 3},
        "firstperson_righthand": {"rotation": [0, -90, 25 + turn], "translation": [1.13, 3.2 + lift, 1.13], "scale": [scale] * 3},
        "firstperson_lefthand": {"rotation": [0, 90, -25 - turn], "translation": [1.13, 3.2 + lift, 1.13], "scale": [scale] * 3},
        "ground": {"rotation": [0, 0, turn], "translation": [0, 2, 0], "scale": [0.5] * 3},
        "fixed": {"rotation": [0, 180, turn], "scale": [1, 1, 1]},
        "head": {"rotation": [0, 180, turn], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }


def upright(scale=0.34, lift=4.0, side=-0.5, toward=-1.0, turn=-35, tilt=12):
    """round things held standing up and facing you (turned a little, top tipped a little toward you)"""
    fp = lambda sx: {"rotation": [tilt, turn * sx, 0], "translation": [side, lift, toward], "scale": [scale] * 3}
    return {
        "thirdperson_righthand": {"rotation": [0, -35, 0], "translation": [0, 2.5, 1.5], "scale": [scale * 1.05] * 3},
        "thirdperson_lefthand": {"rotation": [0, 35, 0], "translation": [0, 2.5, 1.5], "scale": [scale * 1.05] * 3},
        "firstperson_righthand": fp(1), "firstperson_lefthand": fp(-1),
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5] * 3},
        "fixed": {"rotation": [0, 180, 0], "scale": [0.9] * 3},
        "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }


# ---------------------------------------------------------------- palettes (dark -> light), hand-picked
DIAMOND = ["0b2f2a", "11463d", "17695a", "1f9180", "2bc2a8", "4ee6cb", "9ef7e6", "e4fffa"]
DIAMOND_DARK = ["06211d", "0b2f2a", "11463d", "17695a", "1f9180", "2bc2a8"]
GOLD = ["5c3a06", "8f5f0d", "c48b19", "e8b631", "f9d969", "fff3bd"]
LEATHER = ["1c1007", "2e1c0d", "452b15", "5e3c1f", "77502b"]
WOOD = ["2e1d0c", "45301a", "5f4325", "7a5830", "936b3c"]
IRON = ["3d4045", "5a5e64", "7d8187", "a1a5aa", "c4c7cb", "e2e4e6", "fbfbfc"]
APPLE = ["4a060b", "6e0b12", "98111a", "c01b22", "dd2e2b", "ef5236", "f9874f", "ffc58a"]
LEAF = ["1f4a14", "2c661c", "3f8a27", "58ad35", "7fcf4e", "aee77a"]
STEM = ["24160a", "3a2512", "54391d", "6f4f2b"]
CORK = ["5e3a1c", "7d5229", "9e6d3b", "be8c52", "d9ad72"]
GLASS = ["5f8aa6", "86b2cc", "b4d7e9", "e0f3fc", "ffffff"]
WATER = ["123b8c", "1a52b8", "2468d6", "3c84ea", "62a3f5", "a9d2ff", "e6f3ff"]
TINTED = ["5a5a5a", "7a7a7a", "9a9a9a", "bcbcbc", "dcdcdc", "f4f4f4"]  # coloured by the game (the potion)
STRING = ["6e5a36", "9a8152", "c4ab78", "e3cfa0"]


# ---------------------------------------------------------------- cool things
class Tier:
    """one tool tier's materials: the head (blade), its bright edge, the darker metal round it (guard, socket), trims
    (caps, collars, guard tips), the gem set in it (if any), the grip and the handle"""

    def __init__(self, head, hb, dark, db, trim, tb, gem=None, grip="leather", handle=None, edge_b=None,
                 shine=0.7, edge=None):
        self.head = Mat(head, base=hb, kind="blade", shine=shine)
        self.metal = Mat(head, base=hb - 0.6, kind="metal", shine=shine)
        self.edge = Mat(head, base=edge_b if edge_b is not None else len(head) - 1.8, kind="blade", bevel=0.4) \
            if edge is None else Mat(edge, base=len(edge) - 2.6, kind="blade", bevel=0.3, glow=True)
        self.dark = Mat(dark, base=db, kind="metal")
        self.trim = Mat(trim, base=tb, kind="metal")
        self.gem = Mat(gem, base=len(gem) - 2.5, kind="gem", bevel=0.3, glow=True) if gem else None
        self.grip = Mat(STRING, base=1.8, kind="wrap", bevel=0.4) if grip == "twine" else \
            Mat(LEATHER, base=2.0, kind="wrap", bevel=0.5)
        self.wood = Mat(handle or WOOD, base=2.2, kind="wood", bevel=0.6)


PLANKS = ["3f2c14", "5c421f", "7d5c2c", "9c7739", "b8914a", "d1ac62"]
STONE = ["2c2c2e", "434346", "5e5e61", "7c7c7f", "9b9b9e", "bdbdbf"]
NETHERITE = ["0e0b0c", "171214", "221b1e", "2f2529", "3f3337", "54454a", "6e5d62"]
EMBER = ["5a1405", "9c2a08", "d9531a", "ff8a3a", "ffc27a", "fff0d0"]
RUBY = ["4a0510", "7d0c1c", "b5172c", "e2324a", "ff7a8a", "ffd0d6"]
IRON_GEM = ["2a3a55", "3f5c8a", "5f86c2", "9cc0ee", "dceaff"]

TIERS = {
    "wooden": Tier(PLANKS, 3.0, WOOD, 2.0, WOOD, 2.6, grip="twine", edge_b=4.6, shine=0.3),
    "stone": Tier(STONE, 3.0, STONE, 1.6, WOOD, 2.6, grip="twine", edge_b=4.6, shine=0.4),
    "iron": Tier(IRON, 3.8, IRON, 1.6, IRON, 2.4, grip="leather", edge_b=5.6),
    "golden": Tier(GOLD, 3.0, GOLD, 1.6, GOLD, 1.8, gem=RUBY, grip="leather", edge_b=4.6),
    "diamond": Tier(DIAMOND, 4.2, DIAMOND_DARK, 3.0, GOLD, 3.0, gem=DIAMOND, grip="leather", edge_b=6.2),
    "netherite": Tier(NETHERITE, 3.6, NETHERITE, 1.4, GOLD, 3.0, gem=EMBER, grip="leather", edge=EMBER),
}
FANCY = {"golden", "diamond", "netherite"}  # gems and trims


def ridge(k, ii, jj, w, h, face):
    """a bright spine up the middle of a blade"""
    if face in ("north", "south") and w >= 3:
        mid = (w - 1) / 2
        k = np.where(np.abs(ii - mid) < 0.6, k + 1.6, k)
    return k


def bevel_right(k, ii, jj, w, h, face):
    """a lighter bevel band just before a cutting edge on the right"""
    if face in ("north", "south"):
        k = np.where(ii >= w - 2, k + 1.2, k)
    return k


def bevel_up(k, ii, jj, w, h, face):
    """a lighter bevel band along the top"""
    if face in ("north", "south", "east", "west"):
        k = np.where(jj <= 1, k + 1.2, k)
    return k


def handle(m, t, top, fancy):
    """a wooden handle with a wrapped grip (and, for fancy tiers, a trimmed end cap and grip ring)"""
    m.box((7, 0, 7), (9, top, 9), t.wood)
    m.box((6.75, 1.5, 6.75), (9.25, 6, 9.25), t.grip)
    if fancy:
        m.box((6.5, 0, 6.5), (9.5, 1, 9.5), t.trim)
        m.box((6.75, 6, 6.75), (9.25, 6.5, 9.25), t.trim)


def sword(tier):
    t, fancy = TIERS[tier], tier in FANCY
    m = Model(f"{tier}_sword")
    m.box((6.5, 0, 6.5), (9.5, 2, 9.5), t.dark)                          # pommel
    if t.gem:
        m.box((7.5, 0.5, 6.25), (8.5, 1.5, 9.75), t.gem, ao=False)
    m.box((7, 2, 7), (9, 7.5, 9), t.grip)                                # wrapped grip
    m.box((6.75, 7, 6.75), (9.25, 7.5, 9.25), t.trim)                    # collar
    m.box((5, 7.5, 6.5), (11, 9.5, 9.5), t.dark)                         # guard: heavy middle
    m.box((2.5, 8, 7), (13.5, 9, 9), t.dark)                             # wings
    m.box((1.5, 8, 7), (2.5, 10.5, 9), t.trim), m.box((13.5, 8, 7), (14.5, 10.5, 9), t.trim)  # tips sweeping up
    if t.gem:
        m.box((7.25, 7.75, 6.25), (8.75, 9.25, 9.75), t.gem, ao=False)
    m.box((6, 9.5, 7.5), (10, 21, 8.5), t.head, decal=ridge)             # blade
    m.box((5.5, 10, 7.6), (6, 20, 8.4), t.edge), m.box((10, 10, 7.6), (10.5, 20, 8.4), t.edge)
    m.box((6.5, 21, 7.5), (9.5, 23, 8.5), t.head, decal=ridge)
    m.box((7, 23, 7.55), (9, 24.5, 8.45), t.edge)
    m.box((7.5, 24.5, 7.6), (8.5, 26, 8.4), t.edge)                       # the point
    m.write(blade_held(20, 0.34, 0.0))


def axe(tier):
    t, fancy = TIERS[tier], tier in FANCY
    m = Model(f"{tier}_axe")
    handle(m, t, 17, fancy)
    m.box((6.5, 11, 6.5), (9.5, 16.5, 9.5), t.dark)                     # socket
    if t.gem:
        m.box((7.25, 16.5, 7.25), (8.75, 17.5, 8.75), t.gem, ao=False)  # a gem capping the handle
    m.box((7.5, 13, 6.25), (8.5, 14, 9.75), t.trim, ao=False)           # rivet
    m.box((9.5, 11.5, 7.25), (12, 16, 8.75), t.metal)                   # cheek
    m.box((12, 10, 7.5), (14.5, 17.5, 8.5), t.head, decal=bevel_right)  # blade
    m.box((14.5, 9.5, 7.6), (15.5, 18, 8.4), t.edge)                    # cutting edge
    m.box((12.5, 9, 7.6), (14.5, 10, 8.4), t.metal)                     # beard
    m.box((3.5, 12.5, 7.5), (6.5, 14.5, 8.5), t.dark)                   # back spike
    m.box((2.5, 13, 7.6), (3.5, 14, 8.4), t.edge)
    m.write(blade_held(45, 0.4, -0.5))


def pickaxe(tier):
    t, fancy = TIERS[tier], tier in FANCY
    m = Model(f"{tier}_pickaxe")
    handle(m, t, 16, fancy)
    m.box((6.5, 13.5, 6.5), (9.5, 17, 9.5), t.dark)                     # the block holding the head
    if t.gem:
        m.box((7.25, 14.5, 6.25), (8.75, 16, 9.75), t.gem, ao=False)
    for side in (-1, 1):                                                 # two arms curving down to points
        def X(a, b):
            return (8 + side * a, 8 + side * b) if side > 0 else (8 + side * b, 8 + side * a)
        x0, x1 = X(1.5, 5)
        m.box((x0, 14, 7.25), (x1, 16.5, 8.75), t.metal, decal=bevel_up)
        x0, x1 = X(5, 6.5)
        m.box((x0, 12.5, 7.4), (x1, 15.5, 8.6), t.head)
        x0, x1 = X(6, 7.5)
        m.box((x0, 11, 7.5), (x1, 13, 8.5), t.head)
        x0, x1 = X(6.5, 7.5)
        m.box((x0, 9.5, 7.6), (x1, 11, 8.4), t.edge)                     # the point
    m.box((7, 17, 7), (9, 17.5, 9), t.trim)                              # a cap on top
    m.write(blade_held(45, 0.4, -0.5))


def shovel(tier):
    t, fancy = TIERS[tier], tier in FANCY
    m = Model(f"{tier}_shovel")
    handle(m, t, 13, fancy)
    m.box((6.75, 12, 6.75), (9.25, 14, 9.25), t.dark)                   # collar
    if t.gem:
        m.box((7.5, 12.5, 6.5), (8.5, 13.5, 9.5), t.gem, ao=False)
    m.box((5.5, 14, 7.4), (10.5, 19, 8.6), t.head, decal=ridge)         # the blade
    m.box((6, 19, 7.5), (10, 20.5, 8.5), t.head, decal=ridge)
    m.box((6.75, 20.5, 7.6), (9.25, 21.5, 8.4), t.edge)                  # its rounded tip
    m.box((5, 15, 7.6), (5.5, 19, 8.4), t.edge), m.box((10.5, 15, 7.6), (11, 19, 8.4), t.edge)
    m.write(blade_held(45, 0.4, -0.5))


def hoe(tier):
    t, fancy = TIERS[tier], tier in FANCY
    m = Model(f"{tier}_hoe")
    handle(m, t, 17, fancy)
    m.box((6.5, 14.5, 6.5), (9.5, 17, 9.5), t.dark)                     # socket
    if t.gem:
        m.box((7.25, 15, 6.25), (8.75, 16.5, 9.75), t.gem, ao=False)
    m.box((9.5, 15, 7.4), (13, 16.75, 8.6), t.metal, decal=bevel_up)    # neck reaching out
    m.box((12, 11.5, 7.5), (14.5, 16.75, 8.5), t.head)                  # the blade, hanging down
    m.box((12, 10.5, 7.6), (14.5, 11.5, 8.4), t.edge)                    # its edge
    m.box((5, 15.25, 7.5), (6.5, 16.5, 8.5), t.dark)                    # a short back knob
    m.write(blade_held(45, 0.4, -0.5))


# ---------------------------------------------------------------- beautiful things
TOOLS = {"sword": sword, "pickaxe": pickaxe, "axe": axe, "shovel": shovel, "hoe": hoe}
ITEMS = {f"{tier}_{kind}": (lambda f=f, tier=tier: f(tier)) for tier in TIERS for kind, f in TOOLS.items()}
GUI_LAYERS = {"potion": ["minecraft:item/potion_overlay", "minecraft:item/potion"]}


JAR = os.environ.get("MC_JAR", "/tmp/mcjar/client.jar")


def vanilla_layers(name):
    """the item's flat picture layers, as the game's own item model has them"""
    import zipfile
    try:
        with zipfile.ZipFile(JAR) as z:
            tex = json.loads(z.read(f"assets/minecraft/models/item/{name}.json")).get("textures", {})
    except (OSError, KeyError):
        return [f"minecraft:item/{name}"]
    layers = [tex[f"layer{i}"] for i in range(4) if f"layer{i}" in tex]
    return [t if ":" in t else "minecraft:" + t for t in layers] or [f"minecraft:item/{name}"]


def vanilla_overrides(name):
    """the game's own override list for an item (bow pulling, compass angle, clock time...)"""
    import zipfile
    with zipfile.ZipFile(JAR) as z:
        ov = json.loads(z.read(f"assets/minecraft/models/item/{name}.json")).get("overrides", [])
    for o in ov:
        if ":" not in o["model"]:
            o["model"] = "minecraft:" + o["model"]
    return ov


def item_model(name, base=None, layers=None, overrides=None):
    """the item's own model: ours (item3d/<base>) everywhere except the inventory, which keeps the usual flat
    picture; overrides switch it between states the way the game's own model does"""
    layers = layers or GUI_LAYERS.get(name) or vanilla_layers(name)
    model = {"loader": "forge:separate_transforms", "textures": {"particle": layers[-1]},
             "base": {"parent": f"{NS}:item3d/{base or name}"},
             "perspectives": {"gui": {"parent": "minecraft:item/generated",
                                      "textures": {f"layer{i}": t for i, t in enumerate(layers)}}}}
    if overrides:
        model["overrides"] = overrides
    p = os.path.join(PACK, "assets", "minecraft", "models", "item")
    os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, name + ".json"), "w") as fh:
        json.dump(model, fh, separators=(",", ":"))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import models_food  # noqa: E402  (batch 2: food)
    import models_vessels  # noqa: E402  (batch 3: bottles and buckets)
    import models_materials  # noqa: E402  (batch 4: gems and materials)
    import models_drops  # noqa: E402  (batch 5: mob drops and crafting bits)
    ITEMS.update(models_food.FOOD)
    ITEMS.update(models_vessels.VESSELS)
    ITEMS.update(models_materials.MATERIALS)
    ITEMS.update(models_drops.DROPS)
    only = set(sys.argv[1:])
    import models_special  # noqa: E402  (batch 6: special items, each writes its own item models)
    import models_armor  # noqa: E402  (batch 7: armour with trims, torches, lanterns, candles, chain)
    ITEMS.update(models_armor.LIGHTS)
    for name, make in list(ITEMS.items()) + list(models_special.SPECIAL.items()) + list(models_armor.ARMOR.items()):
        if only and name not in only:
            continue
        if make() is not False:   # special items write their own item models and return False
            item_model(name)
        print("made", name)
