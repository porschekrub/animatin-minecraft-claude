#!/usr/bin/env python3
"""Batch 12 of Lifelike Motion's 3D items: doors, signs, hanging signs and beds (built with tools/models.py's
parts and painter; run tools/models.py to write them). All are held up in front of you; beds keep the game's own
little bed in the inventory."""
import json
import os

import numpy as np

from models import Mat, Model, upright, IRON, GLASS, PACK, NS
from models_food import shine, stripes, spots
from models_vehicles import WOODS, rivets
from models_discs import ramp, DYES

WOODS = dict(WOODS)
WOODS["crimson"] = ["2a0e1a", "421628", "5c2238", "74304a", "8c405c", "a45670"]
WOODS["warped"] = ["0c2a28", "143e3a", "1e5650", "2a6e66", "36887e", "4ea29a"]
CHAIN = ["1a1c22", "2a2e36", "3e4450", "56606c", "76808c"]
WOOL_WHITE = ["9a968e", "bab6ae", "d6d2ca", "eae6de", "f8f6f0", "ffffff"]
DOOR = dict(scale=0.4, lift=3.0, tilt=5)
SIGN = dict(scale=0.42, lift=4.0, tilt=5)


def grain_v(k, ii, jj, w, h, face):
    """planks standing up: a dark line between boards every few pixels"""
    if face in ("north", "south") and w >= 4:
        k = np.where(ii % 3 == 2, k - 0.8, k)
    return k


# ---------------------------------------------------------------- doors
WINDOWED = {"oak", "birch", "jungle", "acacia", "mangrove", "cherry", "crimson", "warped", "iron"}


def door(wood):
    name = f"{wood}_door"
    iron = wood == "iron"
    pal = IRON if iron else WOODS[wood]
    m = Model(name)
    body = Mat(pal, base=3.4 if iron else 3.0, kind="metal" if iron else "wood", bevel=0.4, shine=0.4)
    frame = Mat(pal, base=2.2 if iron else 1.8, kind="metal" if iron else "wood", bevel=0.4)
    panel = Mat(pal, base=3.8 if iron else 3.4, kind="metal" if iron else "plain", bevel=0.6)
    dark = Mat(CHAIN, base=1.6, kind="metal", bevel=0.3)
    gold = Mat(["3a2a10", "6a4e1c", "a07c2c", "d2a840", "f0d070"], base=3.0, kind="metal", bevel=0.3)
    window = wood in WINDOWED
    split = 8.4 if window else 16
    m.box((4, 0, 7.4), (12, split, 8.6), body, decal=None if iron else grain_v)        # the door leaf
    if window:                                                                         # its window
        m.box((4, split, 7.4), (5.2, 16, 8.6), body)
        m.box((10.8, split, 7.4), (12, 16, 8.6), body)
        m.box((5.2, 14.8, 7.4), (10.8, 16, 8.6), body)
        m.box((5.2, split, 7.9), (10.8, 14.8, 8.1), Mat(GLASS, base=2.4, kind="glass", alpha=120))
        m.box((7.7, split, 7.6), (8.3, 14.8, 8.4), frame, ao=False)                     # glazing bars
        m.box((5.2, 11.3, 7.6), (10.8, 11.9, 8.4), frame, ao=False)
    for z0, z1 in ((8.6, 8.9), (7.1, 7.4)):                                           # the frame, front and back
        m.box((4, 0, z0), (5.0, 16, z1), frame)
        m.box((11.0, 0, z0), (12, 16, z1), frame)
        m.box((5.0, 15.0, z0), (11.0, 16, z1), frame)
        m.box((5.0, 7.6, z0), (11.0, 8.4, z1), frame)
        m.box((5.0, 0, z0), (11.0, 1.0, z1), frame)
        m.box((6.0, 2.0, z0), (10.0, 6.6, z1 - 0.1), panel, decal=rivets if iron else shine)   # a raised panel
        if not window:
            m.box((6.0, 9.4, z0), (10.0, 14.0, z1 - 0.1), panel, decal=rivets if iron else shine)
    for y in (2.4, 12.6):                                                             # hinges
        m.box((3.6, y, 7.3), (4.6, y + 1.2, 8.7), dark, ao=False)
    handle = dark if iron or wood in ("dark_oak", "spruce", "crimson", "warped") else gold
    m.box((10.2, 7.4, 8.9), (10.8, 9.2, 9.5), handle, ao=False)                       # the handle, both sides
    m.box((10.2, 7.4, 6.5), (10.8, 9.2, 7.1), handle, ao=False)
    m.write(upright(**DOOR), translucent=window)


# ---------------------------------------------------------------- signs
def board_face(k, ii, jj, w, h, face):
    """boards across the sign, and three lines of writing on its face"""
    if face in ("north", "south"):
        k = np.where(jj % 4 == 3, k - 0.7, k)
        if face == "south" and w >= 8:
            line = {2: (3, w - 4), 4: (2, w - 3), 6: (4, w - 6)}
            writing = np.zeros_like(k, bool)
            for row, (a, b) in line.items():
                writing |= (jj == row) & (ii >= a) & (ii <= b) & ((ii * 7 + row * 3) % 6 != 0)
            k = np.where(writing, k - 1.3, k)
    return k


def sign(wood):
    name = f"{wood}_sign"
    pal = WOODS[wood]
    m = Model(name)
    board = Mat(pal, base=3.0, bevel=0.6)
    post = Mat(pal, base=2.2, kind="wood", bevel=0.5)
    m.box((7.25, 0, 7.25), (8.75, 8, 8.75), post)
    m.box((1, 7.5, 7.3), (15, 15, 8.7), board, decal=board_face)
    m.box((0.8, 7.3, 7.6), (15.2, 7.7, 8.4), post)                                   # a rim along the bottom
    m.write(upright(**SIGN))


def chain_links(m, x, y0, y1, z=8):
    link = Mat(CHAIN, base=3.0, kind="metal", bevel=0.3)
    y, n = y1, 0
    while y - 1.4 >= y0 - 0.01:
        if n % 2 == 0:
            m.box((x - 0.6, y - 1.4, z - 0.15), (x + 0.6, y, z + 0.15), link, ao=False)
        else:
            m.box((x - 0.15, y - 1.4, z - 0.6), (x + 0.15, y, z + 0.6), link, ao=False)
        y -= 1.1
        n += 1


def hanging_sign(wood):
    name = f"{wood}_hanging_sign"
    pal = WOODS[wood]
    m = Model(name)
    board = Mat(pal, base=3.2, bevel=0.6)
    beam = Mat(pal, base=2.0, kind="wood", bevel=0.6)
    m.box((1, 14.5, 7), (15, 16.5, 9), beam)                                          # the beam it hangs from
    chain_links(m, 4, 9.5, 14.5)
    chain_links(m, 12, 9.5, 14.5)
    m.box((2, 2, 7.25), (14, 9.5, 8.75), board, decal=board_face)
    m.box((1.8, 9.3, 7.5), (14.2, 9.8, 8.5), beam)                                    # a rail along its top
    m.write(upright(**SIGN))


# ---------------------------------------------------------------- beds
BED_WOOD = ["3a2412", "553519", "714822", "8c5c2c", "a87238", "c08a48"]


# ---------------------------------------------------------------- blankets: a design of its own for every colour
# Each design paints palette steps: 0..5 are the colour's own shades (3 its true colour), 6 and 7 two accent
# colours of its own. The face's light is added to the shades (never to the accents). On the cover's top, ii runs
# from the pillows to the foot and jj across the bed, so little pictures are drawn upright for someone looking at
# the side of the bed, as it's held (their rows run across the bed, along jj).
def _tile(mask, every_u, every_v, shift=0):
    """a little picture (rows of 0/1/2...) repeated across the cover, every other row shifted"""
    mask = np.array(mask)
    mh, mw = mask.shape

    def at(ii, jj):
        row = jj // every_v
        u = (ii + row * shift) % every_u
        v = jj % every_v
        inside = (u < mw) & (v < mh)
        return np.where(inside, mask[np.minimum(v, mh - 1), np.minimum(u, mw - 1)], 0)
    return at


HEART = _tile([[1, 0, 1], [1, 1, 1], [0, 1, 0]], 5, 5, shift=2)
FLOWER_M = _tile([[0, 1, 0], [1, 2, 1], [0, 1, 0]], 5, 4, shift=2)
TREE = _tile([[0, 1, 0], [1, 1, 1], [1, 1, 1], [0, 2, 0]], 5, 5, shift=2)
CLOUD = _tile([[0, 1, 1, 0, 0], [1, 1, 1, 1, 0]], 6, 4, shift=3)
MOON = _tile([[0, 1, 1], [1, 0, 0], [1, 0, 0], [0, 1, 1]], 99, 99)
STARS = _tile([[0, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 2, 0], [0, 0, 0, 0, 0, 0],
               [0, 0, 0, 2, 0, 0], [2, 0, 0, 0, 0, 1]], 6, 6, shift=3)


def _diamonds(ii, jj, w, h):                      # white: a classic quilt, stitched in diamonds, puffed between
    line = ((ii + jj) % 4 == 0) | ((ii - jj) % 4 == 0)
    return np.where(line, 2.4, np.where(((ii + jj) % 4 == 2) & ((ii - jj) % 4 == 2), 5, 4))


def _sunset(ii, jj, w, h):                        # orange: sunset stripes, cream between
    return np.array([2, 3, 4, 3, 6])[ii % 5] + 0 * jj


def _flowers(ii, jj, w, h):                       # magenta: little flowers with gold hearts
    f = FLOWER_M(ii, jj)
    return np.where(f == 2, 6, np.where(f == 1, 5, 3))


def _clouds(ii, jj, w, h):                        # light blue: white clouds drifting over the sky
    return np.where(CLOUD(ii, jj) == 1, 6, np.where((jj % 4 == 2) & (ii % 7 == 5), 4, 3))


def _gingham(ii, jj, w, h):                       # yellow: gingham checks with white
    a, b = (ii // 2) % 2, (jj // 2) % 2
    return np.where(a & b, 2.0, np.where(a | b, 3.4, 6))


def _chevron(ii, jj, w, h):                       # lime: zigzags
    z = (jj + np.abs(ii % 4 - 2)) % 4
    return np.where(z == 0, 1.6, np.where(z == 2, 5, 3))


def _hearts(ii, jj, w, h):                        # pink: red hearts
    return np.where(HEART(ii, jj) == 1, 7, np.where((ii + jj) % 2 == 0, 3.3, 3))


def _knit(ii, jj, w, h):                          # gray: a chunky knit, with a pale band near the foot
    k = np.where((ii % 2) == (jj % 2), 3.6, 2.6)
    return np.where((ii >= w - 3) & (ii <= w - 2), 6, k)


def _pinstripe(ii, jj, w, h):                     # light gray: pinstripes with one navy stripe
    return np.where(ii % 6 == 4, 6, np.where(ii % 3 == 1, 2.0, 3.6))


def _waves(ii, jj, w, h):                         # cyan: rolling waves with white crests
    z = (jj + np.array([0, 1, 2, 2, 1, 0])[ii % 6]) % 4                # rows of waves rolling along the bed
    return np.where(z == 0, 6, np.where(z == 1, 4.4, np.where(z == 2, 2.6, 3.2)))


def _night(ii, jj, w, h):                         # purple: a night sky of gold stars
    s = STARS(ii, jj)
    return np.where(s == 1, 6, np.where(s == 2, 5, np.where((ii * 3 + jj * 5) % 11 == 0, 3, 1.8)))


def _tartan(ii, jj, w, h):                        # blue: a dark tartan, with fine green and pale blue lines
    n = (ii % 5 < 2).astype(int) + (jj % 5 < 2).astype(int)
    k = np.where(n == 2, 1.0, np.where(n == 1, 2.2, 3.2))
    return np.where(ii % 5 == 3, 6, np.where(jj % 5 == 3, 4.6, k))


def _patchwork(ii, jj, w, h):                     # brown: patchwork of different cloths, stitched together
    pid = (ii // 3) * 7 + (jj // 3) * 3
    patch = np.array([2.2, 6, 3.6, 7, 4.4, 1.6, 6.0])[pid % 7]
    dots = (patch == 6) & ((ii + jj) % 2 == 0)
    k = np.where(dots, 3.0, patch)
    return np.where((ii % 3 == 0) | (jj % 3 == 0), 1.0, k)


def _forest(ii, jj, w, h):                        # green: a forest of little pine trees
    t = TREE(ii, jj)
    return np.where(t == 2, 6, np.where(t == 1, 1.4, 4))


def _buffalo(ii, jj, w, h):                       # red: buffalo check, red and black
    a, b = (ii // 3) % 2, (jj // 3) % 2
    return np.where(a & b, 6, np.where(a | b, 1.8, 3.4))


def _starry(ii, jj, w, h):                        # black: stars and a crescent moon
    s = STARS(ii + 2, jj + 1)
    moon = MOON(ii - 6, jj - 1) == 1                                      # and a crescent moon
    return np.where(moon, 7, np.where(s == 1, 6, np.where(s == 2, 4, 0.8)))


BLANKETS = {   # colour: (design, accent colours)
    "white": (_diamonds, ["fbfcfc", "e4e8ec"]), "orange": (_sunset, ["fff0d0", "f8c070"]),
    "magenta": (_flowers, ["f8d840", "ffffff"]), "light_blue": (_clouds, ["f8fcff", "ffffff"]),
    "yellow": (_gingham, ["fffdf0", "ffffff"]), "lime": (_chevron, ["f0ffd0", "ffffff"]),
    "pink": (_hearts, ["fff4f8", "d8304c"]), "gray": (_knit, ["c8ccd0", "ffffff"]),
    "light_gray": (_pinstripe, ["2c3a68", "ffffff"]), "cyan": (_waves, ["eafffc", "ffffff"]),
    "purple": (_night, ["ffe070", "ffffff"]), "blue": (_tartan, ["1e5a36", "ffffff"]),
    "brown": (_patchwork, ["e8d8b0", "8a2a20"]), "green": (_forest, ["5a3a1c", "ffffff"]),
    "red": (_buffalo, ["1a1416", "ffffff"]), "black": (_starry, ["fff8d8", "f0d070"]),
}


def blanket(colour, cushion=False):
    """the cover's decal: its colour's own design on top, carried down the sides where it hangs (with soft folds)
    to a hem; the face's light shades the colour's own steps"""
    design, _ = BLANKETS[colour]

    def f(k, ii, jj, w, h, face):
        if face == "down":
            return k
        light = k - 3.0
        if face == "up" or cushion:
            p = design(ii, jj, w, h).astype(float)
        else:                                                             # the sides: the design runs on down
            p = design(ii, jj + 3, w, h).astype(float)
            p = np.where((ii % 3 == 1) & (p < 6), p - 0.5, p)              # folds where it hangs
            p = np.where(jj == h - 1, 4.6, p)                              # the hem
        return np.where(p >= 6, p, np.clip(p + 0.7 * light, 0, 5))
    return f


def pillow(k, ii, jj, w, h, face):
    """a plump pillow: a seam round its edge and a soft sheen"""
    if face == "up":
        k = np.where((ii == 0) | (ii == w - 1) | (jj == 0) | (jj == h - 1), k - 0.7, k)
        k = np.where((ii == 1) & (jj >= 1) & (jj <= 2), 99, k)
    elif face != "down" and h >= 2:
        k = np.where(jj == h // 2, k - 0.8, k)                             # the seam along its side
    return k


def panel(k, ii, jj, w, h, face):
    """a framed wooden panel: a darker frame round a raised middle"""
    if face in ("east", "west") and w >= 4 and h >= 4:
        inner = (ii >= 1) & (ii <= w - 2) & (jj >= 1) & (jj <= h - 2)
        k = np.where(inner, k + 0.6, k - 0.4)
        k = np.where((ii == 1) & inner, k + 0.8, k)
        k = np.where((jj == h - 2) & inner, k - 0.7, k)
    return k


def bed(colour):
    """a proper bed: a wooden bedstead with tall capped posts and a panelled headboard, a white mattress, a cover
    in the bed's colour and its own design (hearts, tartan, clouds...) draping over the sides with the top sheet
    turned down over it, two plump pillows and a little cushion to match the cover"""
    name = f"{colour}_bed"
    m = Model(name)
    pal = ["7a7e84", "9ea2a6", "bfc3c6", "dadcde", "eceeef", "fbfcfc"] if colour == "white" else ramp(DYES[colour])
    cloth = pal + BLANKETS[colour][1]                                  # its shades, then its two accents
    wood = Mat(BED_WOOD, base=3.0, kind="wood", bevel=0.5)
    trim = Mat(BED_WOOD, base=1.8, kind="wood", bevel=0.4)
    cap = Mat(BED_WOOD, base=4.0, bevel=0.5)
    sheet = Mat(WOOL_WHITE, base=3.4, bevel=0.3)
    cover = Mat(cloth, base=3.0, bevel=0)
    soft = Mat(WOOL_WHITE, base=3.8, bevel=0)
    for (x0, x1, top) in ((0, 1.5, 9.5), (14.5, 16, 6.2)):                           # the four posts, capped
        for (z0, z1) in ((3.2, 4.7), (11.3, 12.8)):
            m.box((x0, 0, z0), (x1, top, z1), wood)
            m.box((x0 - 0.2, top, z0 - 0.2), (x1 + 0.2, top + 0.6, z1 + 0.2), cap)
            m.box((x0 + 0.35, top + 0.6, z0 + 0.35), (x1 - 0.35, top + 1.1, z1 - 0.35), cap)
    m.box((0.25, 2.2, 4.7), (1.25, 8.6, 11.3), wood, decal=panel)                    # the headboard
    m.box((0.05, 8.6, 4.7), (1.45, 9.2, 11.3), trim)
    m.box((0.15, 9.2, 6.4), (1.35, 9.9, 9.6), trim)                                   # its raised crest
    m.box((14.75, 2.2, 4.7), (15.75, 5.2, 11.3), wood, decal=panel)                  # the footboard
    m.box((14.55, 5.2, 4.7), (15.95, 5.8, 11.3), trim)
    for (z0, z1) in ((3.35, 4.55), (11.45, 12.65)):                                   # side rails
        m.box((1.5, 1.8, z0), (14.5, 3.0, z1), trim)
    m.box((1.5, 2.0, 4.55), (14.5, 2.9, 11.45), trim)                                 # the slats under it
    m.box((1.3, 2.9, 4.4), (14.6, 4.7, 11.6), sheet,                                  # mattress, in its sheet
          decal=lambda k, ii, jj, w, h, face: np.where((face != "up") & (face != "down") & (jj == 1), k - 0.8, k))
    m.box((5.6, 2.7, 3.95), (14.62, 5.5, 12.05), cover, decal=blanket(colour))        # the cover, in its design
    m.box((5.1, 5.45, 3.9), (7.0, 5.75, 12.1), soft, ao=False)                       # top sheet turned down
    m.box((5.1, 2.7, 3.9), (5.6, 5.45, 4.0), soft, ao=False)                         # and hanging at the sides
    m.box((5.1, 2.7, 12.0), (5.6, 5.45, 12.1), soft, ao=False)
    m.box((6.55, 5.47, 3.85), (6.85, 5.78, 12.15), Mat(pal, base=4.0, bevel=0), ao=False)   # a band along it
    for (z0, z1) in ((4.8, 7.85), (8.15, 11.2)):                                     # two plump pillows,
        lean = (22.5, "z", (3.0, 4.7, (z0 + z1) / 2))                                 # leaning on the headboard
        m.box((1.6, 4.7, z0), (4.4, 6.5, z1), sheet, decal=pillow, rot=lean)
        m.box((1.9, 6.5, z0 + 0.3), (4.1, 6.9, z1 - 0.3), sheet, decal=shine, rot=lean)
    m.box((3.6, 4.7, 6.7), (5.3, 6.9, 9.3), Mat(cloth, base=3.0, bevel=0), rot=(-22.5, "z", (4.4, 4.7, 8)),
          decal=blanket(colour, cushion=True))                                         # a cushion to match
    m.write(upright(scale=0.42, lift=6.0, tilt=28))
    # the inventory keeps the game's own little bed, drawn by the game
    model = {"loader": "forge:separate_transforms", "textures": {"particle": f"minecraft:block/{colour}_wool"},
             "base": {"parent": f"{NS}:item3d/{name}"},
             "perspectives": {"gui": {"parent": "minecraft:item/template_bed",
                                      "textures": {"particle": f"minecraft:block/{colour}_wool"}}}}
    with open(os.path.join(PACK, "assets", "minecraft", "models", "item", name + ".json"), "w") as fh:
        json.dump(model, fh, separators=(",", ":"))
    return False


SIGN_WOODS = ("oak", "spruce", "birch", "jungle", "acacia", "dark_oak", "mangrove", "cherry", "bamboo", "crimson",
              "warped")
BLOCKS = {}
for _w in SIGN_WOODS + ("iron",):
    BLOCKS[f"{_w}_door"] = (lambda w=_w: door(w))
for _w in SIGN_WOODS:
    BLOCKS[f"{_w}_sign"] = (lambda w=_w: sign(w))
    BLOCKS[f"{_w}_hanging_sign"] = (lambda w=_w: hanging_sign(w))
for _c in DYES:
    BLOCKS[f"{_c}_bed"] = (lambda c=_c: bed(c))
