#!/usr/bin/env python3
"""Batch 7 of Lifelike Motion's 3D items: armour, torches, lanterns, candles and the chain (built with
tools/models.py's parts and painter; run tools/models.py to write them).

Armour: every piece of every tier as a small 3D piece of armour held up facing you, plus a version for each of the
10 trim materials, the trim shown as coloured accents (a brow band and crest, a collar and centre line, a belt and
knee plates, boot cuffs) in that material's own colours, picked up by the game's own trim overrides. Leather is
painted grey and coloured by the game, so dyed leather shows its dye."""
import io
import json
import zipfile

import numpy as np
from PIL import Image

from models import (Mat, Model, upright, blade_held, item_model, vanilla_layers, vanilla_overrides, JAR, WOOD,
                    LEATHER, GOLD, IRON, DIAMOND, DIAMOND_DARK, NETHERITE, EMBER, TINTED, STRING)
from models_food import shine, stripes, spots, chain
from models_drops import STICK

RUBY = ["4a0510", "7d0c1c", "b5172c", "e2324a", "ff7a8a"]
CHAIN = ["2a2c30", "44474c", "62666c", "868a90", "aaaeb4", "d0d3d6"]
TURTLE = ["163a12", "22541a", "307026", "448e34", "5cac48", "86cc6c"]
SCUTE_DARK = ["0e2a0c", "163e12", "22541a"]
INSIDE = ["0e0c0c", "1a1616", "262020"]
TRIMS = ["quartz", "iron", "netherite", "redstone", "copper", "gold", "emerald", "diamond", "lapis", "amethyst"]


def trim_palette(mat):
    """a trim material's colours (dark to light), from the game's own trim palette"""
    with zipfile.ZipFile(JAR) as z:
        im = Image.open(io.BytesIO(z.read(f"assets/minecraft/textures/trims/color_palettes/{mat}.png"))).convert("RGB")
    cols = sorted({im.getpixel((x, 0)) for x in range(im.width)}, key=lambda c: c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11)
    return ["%02x%02x%02x" % c for c in cols]


class Tier:
    """an armour tier: its main material, the accent for trims and edges, and how its surface is patterned"""

    def __init__(self, pal, base, accent, ab, kind="metal", decal=None, tint=False, gem=None, rivets=True):
        self.main = Mat(pal, base=base, kind=kind, bevel=0.8, tint=tint)
        self.dark = Mat(pal, base=max(base - 1.4, 0.5), kind=kind, bevel=0.6, tint=tint)
        self.accent = Mat(accent, base=ab, kind="metal", bevel=0.6)
        self.decal = decal
        self.gem = Mat(gem, base=len(gem) - 2, kind="gem", bevel=0.3, glow=True) if gem else None
        self.rivets = rivets


def links(k, ii, jj, w, h, face):
    """chainmail: rows of little rings"""
    return np.where(((ii + (jj // 2) % 2) % 2 == 0) & (jj % 2 == 0), k + 1.2, k - 0.6)


def stitches(k, ii, jj, w, h, face):
    if face in ("north", "south") and w > 3 and h > 3:
        edge = ((ii == 1) | (ii == w - 2) | (jj == 1) | (jj == h - 2)) & ((ii + jj) % 2 == 0)
        k = np.where(edge & (ii >= 1) & (ii <= w - 2) & (jj >= 1) & (jj <= h - 2), k - 1.3, k)
    return k


TIERS = {
    "leather": Tier(TINTED, 3.2, LEATHER, 2.4, kind="organic", decal=stitches, tint=True, rivets=False),
    "chainmail": Tier(CHAIN, 3.0, IRON, 3.0, decal=links, rivets=False),
    "iron": Tier(IRON, 3.8, IRON, 2.0),
    "golden": Tier(GOLD, 3.0, GOLD, 1.8, gem=RUBY),
    "diamond": Tier(DIAMOND, 4.2, GOLD, 3.0, gem=DIAMOND),
    "netherite": Tier(NETHERITE, 3.6, GOLD, 3.0, gem=EMBER),
}
HELD = dict(scale=0.4, lift=5.5)


def helmet(m, t, acc, turtle=False):
    main, dark = t.main, t.dark
    inside = Mat(INSIDE, base=1.0, bevel=0.1)
    m.box((3.5, 8, 3.5), (12.5, 13, 12.5), main, decal=chain(t.decal, shine) if t.decal else shine)   # the crown
    m.box((4.5, 13, 4.5), (11.5, 14, 11.5), main, decal=t.decal)
    m.box((3, 3, 3.5), (4, 9, 12.5), main, decal=t.decal), m.box((12, 3, 3.5), (13, 9, 12.5), main, decal=t.decal)
    m.box((3.5, 3, 3), (12.5, 9, 4), main, decal=t.decal)                    # the back
    m.box((4, 3.5, 11.9), (12, 8, 12), inside, faces=("south",), ao=False)    # the dark inside, seen through the face
    m.box((3.5, 3, 12), (5.5, 8, 13), main), m.box((10.5, 3, 12), (12.5, 8, 13), main)   # cheek guards
    m.box((3.25, 8, 12.25), (12.75, 9.25, 13.25), acc)                        # the brow band
    if not turtle and t.rivets:
        m.box((7.4, 4.5, 12.5), (8.6, 8, 13.25), main)                        # a nose guard
    m.box((7.5, 13.5, 4), (8.5, 14.75, 12), acc)                              # a crest along the top
    if t.gem:
        m.box((7.4, 8.15, 13.25), (8.6, 9.1, 13.5), t.gem, ao=False)


def chestplate(m, t, acc):
    main, dark = t.main, t.dark
    inside = Mat(INSIDE, base=1.0, bevel=0.1)
    m.box((3, 1, 5.5), (13, 12, 10.5), main, decal=chain(t.decal, shine) if t.decal else shine)   # the body
    m.box((0.5, 8.5, 5), (3.5, 12.5, 11), main, decal=t.decal), m.box((12.5, 8.5, 5), (15.5, 12.5, 11), main,
                                                                      decal=t.decal)            # shoulder plates
    m.box((0.5, 8, 5), (3.5, 8.5, 11), acc), m.box((12.5, 8, 5), (15.5, 8.5, 11), acc)
    m.box((5, 12, 6), (11, 13, 10), acc)                                      # the collar
    m.box((6.5, 12.4, 7), (9.5, 13.05, 9), inside, faces=("up",), ao=False)   # the neck hole
    m.box((7.4, 2, 10.5), (8.6, 11.5, 10.9), acc)                             # a ridge down the middle
    m.box((3, 1, 10.5), (13, 2, 10.75), acc)                                  # and the hem
    if t.rivets:
        for x in (4, 11.4):
            for y in (4, 9):
                m.box((x, y, 10.5), (x + 0.6, y + 0.6, 10.7), dark, faces=("south",), ao=False)
    if t.gem:
        m.box((7.25, 8.5, 10.9), (8.75, 10, 11.2), t.gem, ao=False)


def leggings(m, t, acc):
    main = t.main
    m.box((3, 12, 6), (13, 14.5, 10), acc)                                    # the belt
    m.box((3.25, 9, 6.25), (12.75, 12, 9.75), main, decal=t.decal)            # hips
    m.box((3.25, 0, 6.25), (7.6, 9, 9.75), main, decal=chain(t.decal, shine) if t.decal else shine)   # legs
    m.box((8.4, 0, 6.25), (12.75, 9, 9.75), main, decal=t.decal)
    m.box((3.75, 4, 9.75), (7.1, 6.5, 10.25), acc), m.box((8.9, 4, 9.75), (12.25, 6.5, 10.25), acc)   # knee plates
    if t.gem:
        m.box((7.25, 12.5, 10), (8.75, 14, 10.3), t.gem, ao=False)            # the buckle
    else:
        m.box((7, 12.5, 10), (9, 14, 10.25), Mat(GOLD, base=3, kind="metal", bevel=0.4), ao=False)


def boots(m, t, acc):
    main = t.main
    sole = Mat(INSIDE, base=1.5, bevel=0.3)
    for x0 in (2, 9):
        m.box((x0, 1, 5.5), (x0 + 5, 8, 9.5), main, decal=chain(t.decal, shine) if t.decal else shine)   # shaft
        m.box((x0, 1, 9.5), (x0 + 5, 4, 12.5), main, decal=t.decal)               # the toe
        m.box((x0 - 0.25, 0, 5.25), (x0 + 5.25, 1, 12.75), sole)                   # the sole
        m.box((x0 - 0.25, 8, 5.25), (x0 + 5.25, 9.25, 9.75), acc)                  # the cuff
        m.box((x0, 4, 9.5), (x0 + 5, 4.5, 9.75), acc, faces=("south", "up"), ao=False)


PIECES = {"helmet": helmet, "chestplate": chestplate, "leggings": leggings, "boots": boots}
SCALE = {"helmet": 0.42, "chestplate": 0.36, "leggings": 0.4, "boots": 0.4}


def armor_item(tier, piece):
    name = f"{tier}_{piece}"
    t = TIERS[tier]
    disp = upright(scale=SCALE[piece], lift=5.5)
    m = Model(name)
    PIECES[piece](m, t, t.accent)
    m.write(disp)
    # a version per trim material, the accents in that material's colours
    for o in vanilla_overrides(name):
        variant = o["model"].split("/")[-1]                                     # e.g. iron_helmet_iron_darker_trim
        mat = variant[len(name) + 1:-len("_trim")]
        acc = Mat(trim_palette(mat), base=4.2, kind="metal", bevel=0.6)
        m = Model(variant)
        PIECES[piece](m, t, acc)
        m.write(disp, particle=vanilla_layers(name)[0])
        item_model(variant)
    item_model(name, overrides=vanilla_overrides(name))
    return False


def turtle_helmet():
    t = Tier(TURTLE, 3.0, SCUTE_DARK, 1.6, kind="organic", decal=spots(0.1, -1.2, seed="turtle", add=True),
             rivets=False)
    disp = upright(scale=0.42, lift=5.5)
    m = Model("turtle_helmet")
    helmet(m, t, t.accent, turtle=True)
    m.write(disp)
    for o in vanilla_overrides("turtle_helmet"):
        variant = o["model"].split("/")[-1]
        mat = variant[len("turtle_helmet") + 1:-len("_trim")]
        m = Model(variant)
        helmet(m, t, Mat(trim_palette(mat), base=4.2, kind="metal", bevel=0.6), turtle=True)
        m.write(disp, particle="minecraft:item/turtle_helmet")
        item_model(variant)
    item_model("turtle_helmet", overrides=vanilla_overrides("turtle_helmet"))
    return False


# ---------------------------------------------------------------- torches, lanterns, candles, chain
FLAME = ["e86a10", "f8a02a", "ffd060", "fff0a0", "fffbe0"]
SOUL_FLAME = ["1a8aa0", "2ec0d0", "70e8f0", "c0fcff", "f0ffff"]
REDSTONE_GLOW = ["6a0606", "b01010", "f02a20", "ff7a5a", "ffd0c0"]


FLAME_PAL = ["c8281a", "ec4a1e", "fa7424", "ffa02e", "ffc840", "ffe680"]
SOUL_PAL = ["1a4ab8", "2270d8", "2a9ae8", "40c4f2", "78e2fa", "c0f6ff"]


def blocky_flame(m, pal, y0, lean=0.3):
    """a solid flame built from blocks, glowing evenly (no side shading): a teardrop narrow at the base, widest a
    third of the way up, a golden heart going orange and a red tip that leans a little; a small tongue beside it
    and embers floating above. pal runs tip colour -> heart colour"""
    mats = [Mat(pal, base=b, bevel=0.0, glow=True, grad=0.0, shade=False) for b in range(len(pal))]
    layers = ((0.9, 0.9, 4), (1.3, 1.5, 4), (1.3, 1.4, 4), (1.1, 1.1, 3), (1.0, 0.75, 2), (0.9, 0.45, 1),
              (0.7, 0.2, 0))
    y = y0
    for k, (h, w, c) in enumerate(layers):
        dx = lean * max(0, k - 2)
        m.box((8 - w + dx, y, 8 - w), (8 + w + dx, y + h, 8 + w), mats[c], ao=False)
        y += h
    m.box((6.1, y0 + 1.6, 7.6), (6.9, y0 + 3.2, 8.4), mats[3], ao=False)             # a small tongue beside it
    m.box((6.25, y0 + 3.2, 7.75), (6.75, y0 + 4.0, 8.25), mats[1], ao=False)
    m.box((9.9, y - 1.4, 7.85), (10.25, y - 1.05, 8.2), mats[4], ao=False)           # embers rising
    m.box((7.0, y + 0.6, 7.9), (7.3, y + 0.9, 8.2), mats[3], ao=False)


def torch_like(name, flame_pal=None, ember=FLAME, head=None):
    """a wooden torch with a cloth-wrapped head, glowing embers and a solid, glowing flame"""
    m = Model(name)
    stick = Mat(STICK, base=3.0, kind="wood", bevel=0.5)
    cloth = Mat(["2a2016", "4a3a28", "6e5a40", "927a5a"], base=1.6, kind="wrap", bevel=0.5)
    band = Mat(IRON, base=2.4, kind="metal", bevel=0.4)
    embers = Mat(ember, base=len(ember) - 2, bevel=0.2, glow=True)
    m.box((7.25, -3.0, 7.25), (8.75, 8.0, 8.75), stick)
    m.box((7.05, 1.0, 7.05), (8.95, 1.8, 8.95), band)
    if head:
        m.box((6.9, 8, 6.9), (9.1, 10.2, 9.1), head)                            # a glowing redstone head
        m.box((7.4, 10.2, 7.4), (8.6, 10.8, 8.6), head)
    else:
        m.box((6.8, 7.6, 6.8), (9.2, 10.2, 9.2), cloth, decal=spots(0.18, 99, seed=name))   # charred cloth
        m.box((7.1, 10.2, 7.1), (8.9, 10.5, 8.9), embers, ao=False)            # glowing embers on top
    if flame_pal:
        blocky_flame(m, flame_pal, 10.4)
    m.write(blade_held(-15, 0.5, 2.0), particle=vanilla_layers(name)[0])


def torch():
    torch_like("torch", FLAME_PAL)


def soul_torch():
    torch_like("soul_torch", SOUL_PAL, ember=SOUL_FLAME)


def redstone_torch():
    torch_like("redstone_torch", head=Mat(REDSTONE_GLOW, base=2.4, bevel=0.4, glow=True))


BRASS = ["4a3006", "7a5210", "a8761c", "d09c34", "eac462", "fbe6a4"]
SILVER = ["3a4048", "5a626c", "7e8894", "a6b0ba", "ced6de", "f0f4f8"]


def lantern_like(name, glow_pal, trim_pal):
    """an elegant iron lantern: a stepped base with a trim band, slim corner posts with capped ends, warm glowing
    glass with a light streak, a soft orb of light inside, a stepped roof with a finial and a curved handle"""
    m = Model(name)
    iron = Mat(["1c1d20", "2a2c30", "3c3f45", "53575e", "6e737b"], base=1.8, kind="metal", bevel=0.8)
    trim = Mat(trim_pal, base=3.2, kind="metal", bevel=0.6)
    core = Mat(glow_pal, base=3.0, bevel=0.0, glow=True, grad=0.0, shade=False)
    halo = Mat(glow_pal, base=2.2, bevel=0.0, alpha=80, glow=True, grad=0.0, shade=False)

    def streak(k, ii, jj, w, h, face):
        return np.where((ii == 1) & (jj >= 1) & (jj <= h - 2), k + 2.5, k) if w > 3 else k

    glass = Mat(glow_pal, base=3.6, kind="glass", alpha=34, bevel=0.2, glow=True, shade=False)
    # the light inside: a bright heart in a soft glow (drawn before the glass)
    m.box((6.75, 4.0, 6.75), (9.25, 7.0, 9.25), core, ao=False)
    m.box((7.25, 3.25, 7.25), (8.75, 7.75, 8.75), core, ao=False)
    m.box((6.25, 4.5, 7.25), (9.75, 6.5, 8.75), core, ao=False)
    m.box((7.25, 4.5, 6.25), (8.75, 6.5, 9.75), core, ao=False)
    m.box((5.75, 2.5, 5.75), (10.25, 9.0, 10.25), halo, ao=False)
    # base
    m.box((4.0, 0, 4.0), (12.0, 1.0, 12.0), iron)
    m.box((4.5, 1.0, 4.5), (11.5, 1.75, 11.5), trim)
    m.box((3.5, -0.5, 3.5), (12.5, 0, 12.5), iron)
    # slim corner posts with little capped ends
    for x, z in ((4.75, 4.75), (10.5, 4.75), (4.75, 10.5), (10.5, 10.5)):
        m.box((x, 1.75, z), (x + 0.75, 9.25, z + 0.75), iron)
        m.box((x - 0.15, 9.0, z - 0.15), (x + 0.9, 9.6, z + 0.9), trim)
    # trim band round the top of the glass, and the stepped roof
    m.box((4.5, 9.25, 4.5), (11.5, 10.0, 11.5), trim)
    m.box((4.0, 10.0, 4.0), (12.0, 10.75, 12.0), iron)
    m.box((5.0, 10.75, 5.0), (11.0, 11.5, 11.0), iron)
    m.box((6.0, 11.5, 6.0), (10.0, 12.25, 10.0), iron)
    m.box((7.0, 12.25, 7.0), (9.0, 13.0, 9.0), trim)
    m.box((7.5, 13.0, 7.5), (8.5, 13.75, 8.5), trim)                            # the finial
    # a curved handle arching over the top
    for (a, b) in (((4.25, 10.75, 7.6), (5.0, 12.5, 8.4)), ((11.0, 10.75, 7.6), (11.75, 12.5, 8.4)),
                   ((4.75, 12.5, 7.6), (5.75, 14.0, 8.4)), ((10.25, 12.5, 7.6), (11.25, 14.0, 8.4)),
                   ((5.5, 14.0, 7.6), (10.5, 14.75, 8.4))):
        m.box(a, b, iron)
    # the glass panes, last, so the light shows through them
    for (a, b) in (((5.5, 1.75, 5.0), (10.5, 9.25, 5.25)), ((5.5, 1.75, 10.75), (10.5, 9.25, 11.0)),
                   ((5.0, 1.75, 5.5), (5.25, 9.25, 10.5)), ((10.75, 1.75, 5.5), (11.0, 9.25, 10.5))):
        m.box(a, b, glass, decal=streak, ao=False)
    d = blade_held(0, 0.5, tp=0.6)
    for k in ("firstperson_righthand", "firstperson_lefthand"):
        d[k]["rotation"] = [0, d[k]["rotation"][1], 0]
        d[k]["translation"] = [0, 7.5, 0]
    m.write(d, translucent=True)


LIGHT = ["c86a10", "ec9020", "fab238", "ffcc5a", "ffe28c", "fff2c0"]
SOUL_LIGHT = ["1478a0", "1ea4cc", "3ccae8", "78e2f6", "b8f4ff", "e8fcff"]


def lantern():
    lantern_like("lantern", LIGHT, BRASS)


def soul_lantern():
    lantern_like("soul_lantern", SOUL_LIGHT, SILVER)


DYES = {"": "e8dcc0", "white": "f0f0f0", "orange": "f07a1a", "magenta": "c040c0", "light_blue": "5aaef0",
        "yellow": "f8d030", "lime": "80c820", "pink": "f090b0", "gray": "505860", "light_gray": "9a9aa0",
        "cyan": "20989a", "purple": "8030b0", "blue": "3040a8", "brown": "7a4a24", "green": "4a6a1a",
        "red": "b02020", "black": "202024"}


def wax(hexc):
    """a wax colour ramp around one dye colour"""
    c = np.array([int(hexc[i:i + 2], 16) for i in (0, 2, 4)], float)
    steps = [c * 0.45, c * 0.65, c * 0.85, c, c + (255 - c) * 0.35, c + (255 - c) * 0.65]
    return ["%02x%02x%02x" % tuple(int(v) for v in np.clip(s, 0, 255)) for s in steps]


def candle(colour):
    name = f"{colour}_candle" if colour else "candle"
    m = Model(name)
    w = Mat(wax(DYES[colour]), base=3.0, bevel=0.6)
    wick = Mat(["1a1614", "34302c"], base=1, bevel=0)
    m.box((6.5, 0, 6.5), (9.5, 9, 9.5), w, decal=shine)
    m.box((6.25, 7.5, 6.25), (6.75, 9, 7), w)                                   # a drip of wax
    m.box((9.25, 6, 8.5), (9.75, 9, 9.25), w)
    m.box((7.75, 9, 7.75), (8.25, 10.5, 8.25), wick, ao=False)
    m.write(upright(scale=0.42, lift=6.0))


def chain_item():
    """a long iron chain of eight links, each turned to the one before"""
    m = Model("chain")
    iron = Mat(CHAIN, base=3.0, kind="metal", bevel=0.6)
    for k in range(8):
        y = -6 + k * 3.25
        if k % 2 == 0:
            m.box((6.5, y, 7.6), (9.5, y + 0.75, 8.4), iron), m.box((6.5, y + 3, 7.6), (9.5, y + 3.75, 8.4), iron)
            m.box((6.5, y, 7.6), (7.25, y + 3.75, 8.4), iron), m.box((8.75, y, 7.6), (9.5, y + 3.75, 8.4), iron)
        else:
            m.box((7.6, y, 6.5), (8.4, y + 0.75, 9.5), iron), m.box((7.6, y + 3, 6.5), (8.4, y + 3.75, 9.5), iron)
            m.box((7.6, y, 6.5), (8.4, y + 3.75, 7.25), iron), m.box((7.6, y, 8.75), (8.4, y + 3.75, 9.5), iron)
    m.write(upright(scale=0.4, lift=4.0))


LIGHTS = {"torch": torch, "soul_torch": soul_torch, "redstone_torch": redstone_torch, "lantern": lantern,
          "soul_lantern": soul_lantern, "chain": chain_item}
LIGHTS.update({(f"{c}_candle" if c else "candle"): (lambda c=c: candle(c)) for c in DYES})

ARMOR = {f"{t}_{p}": (lambda t=t, p=p: armor_item(t, p)) for t in TIERS for p in PIECES}
ARMOR["turtle_helmet"] = turtle_helmet
