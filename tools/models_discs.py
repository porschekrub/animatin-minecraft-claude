#!/usr/bin/env python3
"""Batch 9 of Lifelike Motion's 3D items: music discs (and the disc fragment), spawn eggs and dyes (built with
tools/models.py's parts and painter; run tools/models.py to write them). All are held up facing you.

Records are built from slices, each one pixel tall, so their outline is a clean pixel circle, and their faces are
painted from where each texel sits in the circle (grooves, the sheen across them, the label)."""
import colorsys
import math
import re
import zipfile

import numpy as np

from models import Mat, Model, upright, item_model, hexc, JAR
from models_food import spots, stripes
from models_drops import STRING

HELD = dict(scale=0.42, lift=6.5)
VINYL = ["08080a", "111114", "1a1a1f", "24242b", "30303a", "46465a", "7a7a92", "b4b4c8"]
TINT_LIGHT = ["8a8a8a", "a6a6a6", "c2c2c2", "dadada", "eeeeee", "ffffff"]   # coloured by the game


def ramp(hx, n=6):
    """a palette (dark to light) from one colour: deepened below it, lifted toward white above"""
    r, g, b = (c / 255 for c in hexc(hx))
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    out = []
    for t in np.linspace(0, 1, n):
        if t < 0.6:                                      # darker: less value, a little more saturation
            k = t / 0.6
            vv, ss = v * (0.38 + 0.62 * k), min(1, s * (1.15 - 0.15 * k))
        else:                                            # lighter: toward white
            k = (t - 0.6) / 0.4
            vv, ss = v + (1 - v) * 0.55 * k, s * (1 - 0.55 * k)
        rr, gg, bb = colorsys.hsv_to_rgb(h, ss, vv)
        out.append("%02x%02x%02x" % tuple(int(round(c * 255)) for c in (rr, gg, bb)))
    return out


# ---------------------------------------------------------------- round plates
def circle_rows(r, cy, step=1.0):
    """a pixel circle as rows (y0, y1, half width), equal rows merged"""
    rows = []
    for i in range(int(round(2 * r / step))):
        y0 = cy - r + i * step
        dy = abs(y0 + step / 2 - cy)
        hw = round(2 * math.sqrt(max(r * r - dy * dy, 0))) / 2
        if hw <= 0:
            continue
        if rows and rows[-1][2] == hw and abs(rows[-1][1] - y0) < 1e-6:
            rows[-1] = (rows[-1][0], y0 + step, hw)
        else:
            rows.append((y0, y0 + step, hw))
    return rows


def face_paint(cx, cy, x0, x1, y0, y1, paint, edge=None):
    """a decal that paints a box's front and back from where each texel sits (radius and angle about cx, cy)"""
    def f(k, ii, jj, w, h, face):
        if face in ("north", "south"):
            fx = (ii + 0.5) / w
            x = x0 + fx * (x1 - x0) if face == "south" else x1 - fx * (x1 - x0)
            y = y1 - (jj + 0.5) / h * (y1 - y0)
            return paint(np.hypot(x - cx, y - cy), np.arctan2(y - cy, x - cx), k, x, y)
        return k if edge is None else np.full_like(k, edge)
    return f


def round_plate(m, mat, r, z0, z1, paint, cx=8.0, cy=8.0, edge=None, keep=None):
    """a flat round plate standing up, facing you; keep(y0, y1, hw) -> (x0, x1) or None trims rows (a shard)"""
    for (y0, y1, hw) in circle_rows(r, cy):
        x0, x1 = cx - hw, cx + hw
        if keep:
            kept = keep(y0, y1, hw)
            if not kept:
                continue
            x0, x1 = kept
        m.box((x0, y0, z0), (x1, y1, z1), mat, decal=face_paint(cx, cy, x0, x1, y0, y1, paint, edge), ao=False)


def boxes(m, mat, parts, decal=None):
    """parts given round the centre: ((x0, y0, z0), (x1, y1, z1)) with x and z relative to 8"""
    for (a, b) in parts:
        m.box((8 + a[0], a[1], 8 + a[2]), (8 + b[0], b[1], 8 + b[2]), mat, decal=decal)


# ---------------------------------------------------------------- music discs
DISCS = {   # label colour, inner ring colour
    "13": ("ffd800", "c89a00"), "cat": ("4cff00", "1f6800"), "blocks": ("e2543b", "f3a32a"),
    "chirp": ("ff0004", "7f0002"), "far": ("b6ff00", "00c870"), "mall": ("9a75ff", "4800ff"),
    "mellohi": ("b200ff", "e8b0ff"), "stal": ("3a3a3a", "e8e8e8"), "strad": ("f4f4f4", "9a9a9a"),
    "ward": ("2a9a3a", "8ec600"), "11": ("3a3a3a", "6a6a6a"), "wait": ("638ecb", "c8dcf4"),
    "otherside": ("31a2f2", "5fc546"), "5": ("009295", "29dfeb"), "pigstep": ("854242", "f0d040"),
    "relic": ("88e6ff", "905041"),
}


def vinyl(cracked=False):
    def paint(r, ang, k, x, y):
        k = np.full_like(r, 2.0)
        k = k + 1.1 * (np.floor(r * 1.3) % 2)                              # grooves
        k = np.where(r > 6.0, 3.4, k)                                       # the outer lip
        sheen = np.abs(np.sin(ang - math.pi / 4)) < 0.22                    # a sheen across it, corner to corner
        k = np.where(sheen & (r > 2.8), k + 1.9, k)
        if cracked:                                                         # a jagged crack, rim to label
            crack = np.abs((x - 8) - 0.55 * (y - 8) - 0.8 * np.sign(np.sin(y * 2.2))) < 0.5
            k = np.where(crack & (y > 8.5), 6.2, k)
        return k
    return paint


def label_paint(r, a, k, x, y):
    return np.where((r > 2.0) & (np.abs(np.sin(a)) > 0.3), 2.2, np.where((x < 7.6) & (y > 8.6), 4.6, 3.2))


def music_disc(name, label, ring, cracked=False):
    m = Model(name)
    disc = Mat(VINYL, base=2, bevel=0, grad=0)
    lab = Mat(ramp(label), base=3.2, bevel=0, grad=0)
    inner = Mat(ramp(ring), base=3.0, bevel=0, grad=0)
    hole = Mat(VINYL, base=0, bevel=0, grad=0)
    round_plate(m, disc, 6.5, 7.5, 8.5, vinyl(cracked), edge=1.5)
    round_plate(m, lab, 2.5, 7.4, 8.6, label_paint, edge=2.0)               # the label, a little raised
    round_plate(m, inner, 1.25, 7.3, 8.7, lambda r, a, k, x, y: np.where(y > 8.3, 3.8, 3.0), edge=2.0)
    m.box((7.6, 7.6, 7.2), (8.4, 8.4, 8.8), hole, ao=False)                 # the hole
    m.write(upright(**HELD), particle=f"minecraft:item/{name}")


def disc_fragment_5():
    """a shard of disc 5: a slice from its lower left, broken jaggedly, with a corner of its teal label"""
    m = Model("disc_fragment_5")
    disc = Mat(VINYL, base=2, bevel=0, grad=0)
    lab = Mat(ramp("009295"), base=3.2, bevel=0, grad=0)

    def keep(y0, y1, hw):                    # a slice from the lower left, its right edge broken jaggedly
        dy = 8 - (y0 + y1) / 2
        if dy <= 0:
            return None
        lo = max(8 - hw, 8 - dy / math.tan(math.radians(12)))
        hi = min(8 + hw, 8 + 0.4 * dy + (0.6 if int(dy) % 2 else -0.2))
        return (lo, hi) if hi - lo >= 0.9 else None
    round_plate(m, disc, 6.5, 7.5, 8.5, vinyl(), edge=1.5, keep=keep)
    round_plate(m, lab, 2.5, 7.4, 8.6, lambda r, a, k, x, y: np.where(x < 7.2, 4.4, 3.2), edge=2.0, keep=keep)
    m.write(upright(scale=0.42, lift=8.5, side=1.0), particle="minecraft:item/disc_fragment_5")


# ---------------------------------------------------------------- spawn eggs (one model for all, tinted by the game)
EGG = (   # tiers (y0, y1, half width, half depth of the cross arms): wide low down, narrowing to the top
    (0.8, 1.6, 2.6, 2.6), (1.6, 3.0, 3.8, 2.3), (3.0, 7.6, 4.3, 2.6), (7.6, 9.8, 3.9, 2.4), (9.8, 11.4, 3.2, 1.9),
    (11.4, 12.5, 2.3, 1.4), (12.5, 13.1, 1.3, 1.3))
EGG_SPOTS = (   # (side, along, y, size): thin spots half sunk into the shell's sides
    ("south", -1.0, 3.8, 1.4), ("south", 1.0, 6.4, 1.1), ("south", -0.6, 9.0, 1.1), ("south", 0.5, 11.0, 0.9),
    ("east", -0.6, 5.4, 1.3), ("east", 1.0, 8.8, 0.9), ("west", 0.6, 4.6, 1.2), ("north", 0.4, 5.2, 1.3),
    ("west", -0.4, 10.2, 0.9),
)


def tiers(m, mat, layers, decal=None):
    """a round body from tiers (y0, y1, half width, half depth of the arms): each a cross of two boxes and a square
    between them (the cross a hair shorter, so no two tops lie in the same plane)"""
    for (y0, y1, r, d) in layers:
        if d >= r:
            m.box((8 - r, y0, 8 - r), (8 + r, y1, 8 + r), mat, decal=decal)
            continue
        q = (r + d) / 2 + 0.25
        m.box((8 - q, y0, 8 - q), (8 + q, y1, 8 + q), mat, decal=decal)
        m.box((8 - r, y0 + 0.03, 8 - d), (8 + r, y1 - 0.03, 8 + d), mat, decal=decal)
        m.box((8 - d, y0 + 0.06, 8 - r), (8 + d, y1 - 0.06, 8 + r), mat, decal=decal)


def spawn_egg():
    m = Model("spawn_egg")
    shell = Mat(TINT_LIGHT, base=3.4, bevel=0.3, tint=True, tint_index=0)
    spot = Mat(TINT_LIGHT, base=3.6, bevel=0.2, tint=True, tint_index=1)

    def gloss(k, ii, jj, w, h, face):
        if face in ("south", "west") and w >= 4 and h >= 3:
            k = np.where((jj == 1) & (ii == 1), 99, k)
        return k
    tiers(m, shell, EGG, decal=gloss)
    for side, a, y, sz in EGG_SPOTS:
        _, _, r, d = next(t for t in EGG if t[0] <= y < t[1])
        a = 8 + max(-(d - sz / 2 - 0.1), min(d - sz / 2 - 0.1, a))         # kept on the arm's face
        c = 8 + (r if side in ("south", "east") else -r)
        if side in ("south", "north"):
            m.box((a - sz / 2, y - sz / 2, c - 0.1), (a + sz / 2, y + sz / 2, c + 0.1), spot, ao=False)
        else:
            m.box((c - 0.1, y - sz / 2, a - sz / 2), (c + 0.1, y + sz / 2, a + sz / 2), spot, ao=False)
    m.write(upright(**HELD), particle="minecraft:item/spawn_egg")
    with zipfile.ZipFile(JAR) as z:
        eggs = sorted(n.split("/")[-1][:-5] for n in z.namelist()
                      if re.match(r"assets/minecraft/models/item/.*_spawn_egg\.json$", n))
    for egg in eggs:   # every spawn egg shares the one model; the game colours it
        item_model(egg, base="spawn_egg", layers=["minecraft:item/spawn_egg", "minecraft:item/spawn_egg_overlay"])
    return False


# ---------------------------------------------------------------- dyes: a little pouch of coloured powder
DYES = {"white": "f9fffe", "orange": "f9801d", "magenta": "c74ebd", "light_blue": "3ab3da", "yellow": "fed83d",
        "lime": "80c71f", "pink": "f38baa", "gray": "474f52", "light_gray": "9d9d97", "cyan": "169c9c",
        "purple": "8932b8", "blue": "3c44aa", "brown": "835432", "green": "5e7c16", "red": "b02e26",
        "black": "1d1d21"}
POUCH = ((1.0, 2.2, 2.6, 1.6), (2.2, 6.2, 3.9, 2.4), (6.2, 7.4, 3.0, 1.8), (7.4, 8.8, 1.5, 1.5))


def dye(colour):
    name = f"{colour}_dye"
    pal = ramp(DYES[colour])
    m = Model(name)
    cloth = Mat(pal, base=3.0, kind="organic", bevel=0.4)
    powder = Mat(pal, base=4.0, kind="organic", bevel=0.3)
    tie = Mat(STRING, base=2.2, kind="wrap", bevel=0.3)
    tiers(m, cloth, POUCH, decal=stripes(3, -0.7, axis="v"))                    # the bag, gathered in pleats
    flap = stripes(2, -0.8, axis="v")
    for (frm, to, rot) in (((6.3, 8.4, 9.2), (9.7, 10.8, 9.8), (22.5, "x", (8, 8.4, 9.5))),     # its mouth, four
                           ((6.3, 8.4, 6.2), (9.7, 10.8, 6.8), (-22.5, "x", (8, 8.4, 6.5))),    # flaps flaring
                           ((9.2, 8.4, 6.3), (9.8, 10.8, 9.7), (-22.5, "z", (9.5, 8.4, 8))),    # open
                           ((6.2, 8.4, 6.3), (6.8, 10.8, 9.7), (22.5, "z", (6.5, 8.4, 8)))):
        m.box(frm, to, cloth, rot=rot, decal=flap, ao=False)
    m.box((6.9, 8.8, 6.9), (9.1, 9.9, 9.1), powder, decal=spots(0.3, 99, seed=colour))   # powder peeking out
    m.box((6.3, 7.6, 6.3), (9.7, 8.3, 9.7), tie, ao=False)                      # the string round its neck
    m.box((7.5, 7.1, 9.6), (8.5, 8.8, 10.0), tie, ao=False)                     # and its knot
    m.write(upright(**HELD), particle=f"minecraft:item/{name}")


MISC = {f"music_disc_{d}": (lambda d=d, c=c: music_disc(f"music_disc_{d}", c[0], c[1], cracked=d == "11"))
        for d, c in DISCS.items()}
MISC["disc_fragment_5"] = disc_fragment_5
MISC["spawn_egg"] = spawn_egg
MISC.update({f"{c}_dye": (lambda c=c: dye(c)) for c in DYES})
