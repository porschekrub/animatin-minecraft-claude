#!/usr/bin/env python3
"""Batch 6 of Lifelike Motion's 3D items: special items, many with states the game switches between (a compass
needle turning, the clock's sun and moon, a bow drawn, a crossbow loaded, a shield raised, a rod cast, a horn played,
a brush brushing). Each maker builds its models and writes its own item models with the game's own override lists,
so every state keeps working; the inventory keeps the game's flat (and animated) pictures.
Built with tools/models.py's parts and painter; run tools/models.py to write them."""
import json
import math
import os
import zipfile

import numpy as np

from models import (Mat, Model, upright, blade_held, item_model, vanilla_layers, vanilla_overrides, JAR, PACK, NS,
                    WOOD, LEATHER, GOLD, IRON, STRING, DIAMOND, GLASS)
from models_food import blob, spots, shine, chain, stripes, CARROT, VINE, EYE_DARK
from models_drops import STICK, FEATHER, FLINT_HEAD, PAPER

DARK_WOOD = ["1e1208", "2e1d0c", "45301a", "5f4325", "7a5830"]
BRASS = ["4a3006", "7a5210", "a8761c", "d09c34", "eac462", "fbe6a4"]
FACE = ["9a9286", "c2bba8", "e0d9c6", "f2ecdc", "fffaf0"]
NEEDLE_RED = ["6a0808", "a81414", "d82a22", "f45a48"]
NEEDLE_GREY = ["3c3c44", "6a6a74", "a2a2ac", "d4d4dc"]
SCULK = ["06141a", "0a222a", "10363e", "185058", "1e7076"]
SCULK_GLOW = ["0e5a60", "15888c", "2ec0b8", "7af0e0", "d0fff6"]
SKY_DAY = ["2a5ab0", "3a74d0", "5a94e8", "8ab8f4"]
SKY_NIGHT = ["080a1c", "10142e", "1a2044", "262e5c"]
SKY_DUSK = ["6a2a3a", "a8463a", "e07a42", "f8b060"]
SUN = ["e8a810", "fcd030", "fff07a", "fffbd8"]
MOON = ["9a9aa8", "c4c4d0", "e4e4ee", "fafaff"]
RED_GEM = ["4a0510", "7d0c1c", "b5172c", "e2324a", "ff7a8a"]
GREEN_GEM = ["0a3a14", "126024", "1c8a34", "34b850", "7ae890"]
EMERALD = ["063d1a", "0b5e27", "128a38", "1cb44c", "3ee070", "96f8b4"]
PRISM = ["17463e", "245e54", "33786c", "4a9a8a", "6cbcaa", "a0dccc"]
PLANK = ["2a1a0c", "3e2812", "553a1c", "6e4c26", "876032"]
COVER = {"book": ["3a1e0c", "5a3014", "7a441c", "985a28", "b47436"],
         "writable_book": ["3a1e0c", "5a3014", "7a441c", "985a28", "b47436"],
         "written_book": ["1e2a14", "2e4020", "42582e", "58723e", "708e52"],
         "enchanted_book": ["1a0a3a", "2c1460", "43228a", "5e36b0", "7e54d0"],
         "knowledge_book": ["3a0808", "5e0e10", "84161a", "aa2428", "cc3c3c"]}
PAGES = ["b8ae98", "d6cdb8", "ebe4d2", "f7f2e6", "fffcf4"]
INK_BLACK = ["08080a", "141418", "24242a"]
ROPE = ["5a4220", "7e5e30", "a07e44", "c0a060", "dcc080"]
SADDLE = ["2a1408", "44220e", "613416", "7e4820", "9a5e2c", "b6783c"]
FUNGUS = ["0e3a36", "15544e", "1e7068", "2a9084", "40b0a2"]
FUNGUS_CAP = ["4a0e0e", "6e1616", "962020", "bc3030", "dc5a4a"]
HORN = ["5a4a38", "7a6650", "9c8668", "bca684", "d8c6a4", "efe2c6"]
ROCKET = ["4a0808", "7a1010", "a81a1a", "d02a24", "ee4e40"]
TAG = ["8a7448", "b09a68", "d2be8c", "ecdcb0", "fbf2d8"]
BRUSH_HAIR = ["4a3a24", "6e5634", "927448", "b4945e", "d2b47a"]


def write_json(name, d):
    p = os.path.join(PACK, "assets", "minecraft", "models", "item")
    os.makedirs(p, exist_ok=True)
    with open(os.path.join(p, name + ".json"), "w") as fh:
        json.dump(d, fh, separators=(",", ":"))


def vanilla_display(name):
    """an item's display as the game has it: item/generated's, with the item's own on top"""
    with zipfile.ZipFile(JAR) as z:
        gen = json.loads(z.read("assets/minecraft/models/item/generated.json")).get("display", {})
        own = json.loads(z.read(f"assets/minecraft/models/item/{name}.json")).get("display", {})
    d = {k: dict(v) for k, v in gen.items()}
    for k, v in own.items():
        d[k] = dict(v)
    for k in ("thirdperson_righthand", "firstperson_righthand"):
        left = k.replace("right", "left")
        if k in d and left not in own and left not in gen:
            r = d[k].get("rotation", [0, 0, 0])
            d[left] = dict(d[k], rotation=[r[0], -r[1], -r[2]])
    return d


HELD = dict(scale=0.42, lift=6.5)


# ---------------------------------------------------------------- dials: compass, recovery compass, clock
def dial_case(m, case, face):
    """a round case lying flat, face up, with a little hanging loop"""
    # (each part a different height, so no two surfaces lie on top of each other: a stepped, rounded rim)
    m.box((4, 0, 3), (12, 2.1, 13), case)
    m.box((3, 0, 4), (13, 2.2, 12), case)
    m.box((3.5, 0, 3.5), (12.5, 2.5, 12.5), case)
    m.box((4.5, 2.5, 4.5), (11.5, 2.75, 11.5), face, faces=("up",), ao=False)
    m.box((7, 0.5, 1.5), (9, 2, 3), case)                                # the loop
    m.box((7.5, 0.5, 1), (8.5, 2, 1.5), case)


def needle(m, phi, red, grey, pivot):
    """a needle of little pixels lying on the face, the red end pointing at angle phi (clockwise from ahead)"""
    dx, dz = math.sin(phi), -math.cos(phi)
    for r in (1.0, 2.0, 3.0):
        x, z = 8 + dx * r, 8 + dz * r
        m.box((x - 0.5, 2.75, z - 0.5), (x + 0.5, 3.25, z + 0.5), red, ao=False)
    for r in (1.0, 2.0):
        x, z = 8 - dx * r, 8 - dz * r
        m.box((x - 0.5, 2.75, z - 0.5), (x + 0.5, 3.25, z + 0.5), grey, ao=False)
    m.box((7.5, 2.75, 7.5), (8.5, 3.5, 8.5), pivot, ao=False)


def compass_like(name, case_pal, face_pal, red_pal, glow=False):
    case = Mat(case_pal, base=len(case_pal) / 2, kind="metal", bevel=0.8)
    face = Mat(face_pal, base=len(face_pal) / 2, bevel=0.3, glow=glow)
    red = Mat(red_pal, base=len(red_pal) - 1.6, bevel=0.2, glow=True)
    grey = Mat(NEEDLE_GREY, base=2.0, bevel=0.2)
    pivot = Mat(BRASS, base=3.0, kind="metal", bevel=0.3)
    disp = upright(scale=0.42, lift=6.0, tilt=50)
    for k in range(32):
        m = Model(f"{name}_dir_{k:02d}")
        dial_case(m, case, face)
        needle(m, 2 * math.pi * k / 32, red, grey, pivot)
        m.write(disp, particle=vanilla_layers(name)[-1])
    # the game's 32 pictures: number i shows the needle (i - 16) / 32 of a turn clockwise from ahead
    for i in range(32):
        n = f"{name}_{i:02d}"
        item_model(n, base=f"{name}_dir_{(i - 16) % 32:02d}", layers=vanilla_layers(n))
    item_model(name, base=f"{name}_dir_00", overrides=vanilla_overrides(name))
    return False


def compass():
    return compass_like("compass", IRON, FACE, NEEDLE_RED)


def recovery_compass():
    return compass_like("recovery_compass", SCULK, SCULK, SCULK_GLOW, glow=True)


def clock():
    """a gold pocket clock standing up: a window in the top half where the sun and moon turn round with the time of
    day (the game's 64 pictures map onto 32 models), a decorated plate below, a crown and loop on top"""
    case = Mat(GOLD, base=3.0, kind="metal", bevel=0.8)
    plate = Mat(GOLD, base=3.8, kind="metal", bevel=0.6)
    crown = Mat(GOLD, base=2.4, kind="metal", bevel=0.6)
    sun = Mat(SUN, base=2.2, bevel=0.3, glow=True)
    moon = Mat(MOON, base=2.2, bevel=0.3, glow=True)

    def deco(k, ii, jj, w, h, face):
        if face == "south":
            k = np.where((jj == 1) & (ii % 2 == 0), k + 1.4, k)
            k = np.where((ii == w // 2) & (jj >= 2), k - 1.2, k)
        return k

    disp = upright(scale=0.42, lift=6.0)
    for k in range(32):
        th = 2 * math.pi * k / 32                                         # the sun's angle, clockwise from the top
        m = Model(f"clock_dir_{k:02d}")
        m.box((4, 2, 6.8), (12, 14, 9.2), case)                           # a round case
        m.box((3, 3, 6.65), (13, 13, 9.35), case)
        m.box((3.5, 2.5, 6.5), (12.5, 13.5, 9.5), case)
        sky = SKY_DAY if math.cos(th) > 0.25 else SKY_DUSK if math.cos(th) > -0.25 else SKY_NIGHT
        m.box((4.5, 8, 9.5), (11.5, 12, 9.75), Mat(sky, base=2.0, bevel=0.2), faces=("south",), ao=False)  # window
        for body, ang in ((sun, th), (moon, th + math.pi)):
            x, y = 8 + 2.6 * math.sin(ang), 8 + 2.6 * math.cos(ang)
            if y > 8.3:
                m.box((x - 1, max(y - 1, 8), 9.6), (x + 1, min(y + 1, 12), 9.9), body, ao=False)
        m.box((4.5, 4, 9.5), (11.5, 8, 10), plate, decal=deco)            # the plate covering the lower half
        m.box((7, 14, 7), (9, 15, 9), crown)                              # the crown and loop on top
        m.box((7.5, 15, 7.6), (8.5, 16.5, 8.4), crown)
        m.write(disp, particle="minecraft:item/clock_00")
    for i in range(64):
        n = f"clock_{i:02d}"
        item_model(n, base=f"clock_dir_{round(i / 2) % 32:02d}", layers=vanilla_layers(n))
    item_model("clock", base="clock_dir_00", overrides=vanilla_overrides("clock"))
    return False


# ---------------------------------------------------------------- bow and crossbow
def bow():
    """pull -1 resting, 0..2 drawn further: upright, the riser in the middle, limbs bending away from the string,
    gold tips, a gem in the grip; an arrow nocked when drawn"""
    limb = Mat(DARK_WOOD, base=2.6, kind="wood", bevel=0.6)
    tip = Mat(GOLD, base=3.2, kind="metal", bevel=0.4)
    grip = Mat(LEATHER, base=2.0, kind="wrap", bevel=0.4)
    string = Mat(["c8c8c8", "f4f4f4"], base=1, bevel=0)
    shaft = Mat(STICK, base=3.0, kind="wood", bevel=0.3)
    head = Mat(FLINT_HEAD, base=3.0, kind="gem", bevel=0.4)
    fletch = Mat(FEATHER, base=3.0, bevel=0.2)
    gem = Mat(GREEN_GEM, base=3.0, kind="gem", bevel=0.3, glow=True)
    for pull in (-1, 0, 1, 2):
        name = "bow" if pull < 0 else f"bow_pulling_{pull}"
        m = Model(name)
        draw = 0 if pull < 0 else 1.2 + pull * 1.2
        flex = 1.0 + (0 if pull < 0 else 0.35 * (pull + 1))
        m.box((6.8, 6.0, 7.1), (8.6, 10.0, 8.9), grip)
        m.box((6.5, 7.5, 7.5), (6.8, 8.5, 8.5), gem, ao=False)
        steps = [(0.0, 1.6), (-0.35, 1.6), (-0.9, 1.5), (-1.6, 1.5), (-2.5, 1.4)]
        for sgn in (1, -1):
            y = 10.0 if sgn > 0 else 6.0
            for dx, ln in steps:
                x = 7.2 + dx * flex
                y0, y1 = (y, y + ln) if sgn > 0 else (y - ln, y)
                m.box((x, y0, 7.35), (x + 1.2, y1, 8.65), limb)
                y = y1 if sgn > 0 else y0
            tx = 7.2 + steps[-1][0] * flex
            ty0, ty1 = (y, y + 1.6) if sgn > 0 else (y - 1.6, y)
            m.box((tx + 0.6, ty0, 7.5), (tx + 1.5, ty1, 8.5), tip)
        top, bot = 10.0 + sum(l for _, l in steps) + 1.2, 6.0 - sum(l for _, l in steps) - 1.2
        sx = 7.2 + steps[-1][0] * flex + 1.2 + draw
        m.box((sx, bot, 7.95), (sx + 0.15, top, 8.05), string, ao=False)
        if pull >= 0:
            m.box((sx - 13.0, 7.85, 7.85), (sx, 8.15, 8.15), shaft, ao=False)
            m.box((sx - 14.2, 7.6, 7.6), (sx - 13.0, 8.4, 8.4), head, ao=False)
            m.box((sx - 1.6, 7.3, 7.95), (sx - 0.2, 8.7, 8.05), fletch, ao=False)
        d = blade_held(0, 0.68)
        for k in ("firstperson_righthand", "firstperson_lefthand"):
            s = 1 if "right" in k else -1
            d[k] = {"rotation": [0, -30 * s, 10 * s], "translation": [-1 * s, 2.5, 0], "scale": [0.7] * 3}
        for k in ("thirdperson_righthand", "thirdperson_lefthand"):
            s = 1 if "right" in k else -1
            d[k] = {"rotation": [0, -90 * s, 0], "translation": [0, 2, 1], "scale": [0.8] * 3}
        m.write(d, particle="minecraft:item/bow")
        if pull >= 0:
            item_model(name)
    item_model("bow", overrides=vanilla_overrides("bow"))
    return False


def crossbow():
    stock = Mat(DARK_WOOD, base=2.6, kind="wood", bevel=0.6)
    metal = Mat(IRON, base=2.6, kind="metal", bevel=0.7)
    limb = Mat(PLANK, base=3.0, kind="wood", bevel=0.6)
    string = Mat(["c8c8c8", "f4f4f4"], base=1, bevel=0)
    shaft = Mat(STICK, base=3.0, kind="wood", bevel=0.3)
    head = Mat(FLINT_HEAD, base=3.0, kind="gem", bevel=0.4)
    gem = Mat(RED_GEM, base=3.0, kind="gem", bevel=0.3, glow=True)
    rocket = Mat(ROCKET, base=3.0, bevel=0.4)
    for state in ("standby", "pulling_0", "pulling_1", "pulling_2", "arrow", "firework"):
        name = "crossbow" if state == "standby" else f"crossbow_{state}"
        m = Model(name)
        m.box((7.2, -2.0, 7.2), (8.8, 14.0, 8.8), stock)
        m.box((7.0, 9.0, 6.8), (9.0, 14.6, 9.2), metal)
        m.box((1.0, 12.4, 7.4), (15.0, 13.8, 8.6), limb)
        m.box((0.4, 12.2, 7.2), (1.4, 14.0, 8.8), metal)
        m.box((14.6, 12.2, 7.2), (15.6, 14.0, 8.8), metal)
        m.box((7.5, 6.0, 6.4), (8.5, 7.0, 7.2), gem, ao=False)
        m.box((7.4, 2, 8.8), (8.6, 4.5, 9.6), metal)                        # the trigger
        pulled = {"standby": 0, "pulling_0": 1.5, "pulling_1": 3.0, "pulling_2": 4.5}.get(state, 4.8)
        sy = 12.9 - pulled
        m.box((1.2, sy, 7.95), (14.8, sy + 0.15, 8.05), string, ao=False)
        if state == "arrow":
            m.box((7.75, sy, 7.75), (8.25, 17.0, 8.25), shaft, ao=False)
            m.box((7.4, 17.0, 7.4), (8.6, 18.2, 8.6), head, ao=False)
        if state == "firework":
            m.box((7.75, sy, 7.75), (8.25, 15.0, 8.25), shaft, ao=False)
            m.box((7.2, 15.0, 7.2), (8.8, 18.0, 8.8), rocket, ao=False)
            m.box((7.6, 18.0, 7.6), (8.4, 19.0, 8.4), rocket, ao=False)
        d = blade_held(0, 0.68)
        for k in ("firstperson_righthand", "firstperson_lefthand"):
            s = 1 if "right" in k else -1
            d[k] = {"rotation": [-80, 0, -8 * s], "translation": [0, 0, -2], "scale": [0.65] * 3}
        for k in ("thirdperson_righthand", "thirdperson_lefthand"):
            d[k] = {"rotation": [-90, 0, 0], "translation": [0, 3, -1], "scale": [0.8] * 3}
        m.write(d, particle="minecraft:item/crossbow_standby")
        if state != "standby":
            item_model(name)
    item_model("crossbow", layers=["minecraft:item/crossbow_standby"], overrides=vanilla_overrides("crossbow"))
    return False


# ---------------------------------------------------------------- trident, shield, fishing rod, spyglass
def trident():
    m = Model("trident_in_hand")
    shaft = Mat(PRISM, base=2.6, kind="metal", bevel=0.6)
    prong = Mat(PRISM, base=4.0, kind="blade", bevel=0.6)
    edge = Mat(PRISM, base=5.0, kind="blade", bevel=0.3)
    glow = Mat(["2a9a92", "4ad8cc", "a8fff4"], base=1.6, bevel=0.2, glow=True)
    wrap = Mat(LEATHER, base=2.0, kind="wrap", bevel=0.4)
    m.box((7.4, -14.0, 7.4), (8.6, 14.0, 8.6), shaft)
    m.box((7.15, -6, 7.15), (8.85, -1, 8.85), wrap)
    m.box((6.8, -15.0, 6.8), (9.2, -13.6, 9.2), prong)
    m.box((5.0, 13.4, 7.2), (11.0, 15.0, 8.8), prong)
    for x in (5.0, 7.4, 9.8):
        top = 20.0 + (1.4 if x == 7.4 else 0)
        m.box((x, 15.0, 7.4), (x + 1.2, top, 8.6), prong)
        m.box((x + 0.3, top, 7.7), (x + 0.9, top + 1.6, 8.3), edge)
    m.box((7.7, 2.0, 7.15), (8.3, 12.0, 8.85), glow, ao=False)
    d = blade_held(25, 0.42, tp=0.7)
    for k in ("firstperson_righthand", "firstperson_lefthand"):
        d[k]["translation"] = [0, 9, -2]
    d["ground"] = {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.25] * 3}
    d["fixed"] = {"rotation": [0, 180, 45], "scale": [0.45] * 3}
    m.write(d, particle="minecraft:item/trident")
    write_json("trident_in_hand", {"parent": f"{NS}:item3d/trident_in_hand",
                                   "textures": {"particle": "minecraft:item/trident"}})
    item_model("trident", base="trident_in_hand")                       # on the ground and in item frames
    return False


def shield():
    """a round-topped wooden shield with an iron rim, a gold boss with a gem and a leather strap behind (the game's
    banner patterns aren't painted on it)"""
    plank = Mat(PLANK, base=3.0, kind="wood", bevel=0.4)
    rim = Mat(IRON, base=3.0, kind="metal", bevel=0.8)
    boss = Mat(GOLD, base=3.2, kind="metal", bevel=0.6)
    strap = Mat(LEATHER, base=2.0, kind="wrap", bevel=0.4)
    gem = Mat(["1a3a8a", "2a5ad0", "5a8af4", "a8c8ff"], base=2.4, kind="gem", bevel=0.3, glow=True)
    for blocking in (False, True):
        name = "shield_blocking" if blocking else "shield"
        m = Model(name)
        m.box((2.0, 2.0, 7.0), (14.0, 18.0, 8.4), plank)
        m.box((1.4, 1.4, 6.8), (14.6, 2.4, 8.6), rim)
        m.box((1.4, 17.6, 6.8), (14.6, 18.6, 8.6), rim)
        m.box((1.4, 2.4, 6.8), (2.4, 17.6, 8.6), rim)
        m.box((13.6, 2.4, 6.8), (14.6, 17.6, 8.6), rim)
        for y in (6, 14):                                               # rivets
            for x in (3, 12.5):
                m.box((x, y, 6.6), (x + 0.6, y + 0.6, 6.8), rim, faces=("north",), ao=False)
        m.box((6.4, 8.4, 6.2), (9.6, 11.6, 7.0), boss)
        m.box((7.4, 9.4, 5.8), (8.6, 10.6, 6.2), gem, ao=False)
        m.box((7.0, 5.0, 8.4), (9.0, 15.0, 9.4), strap)
        d = {
            "thirdperson_righthand": {"rotation": [0, 90, 0], "translation": [10, 6, -4], "scale": [1, 1, 1]},
            "thirdperson_lefthand": {"rotation": [0, 90, 0], "translation": [10, 6, 12], "scale": [1, 1, 1]},
            "firstperson_righthand": {"rotation": [0, 180, 5], "translation": [-10, 2, -10], "scale": [1.25] * 3},
            "firstperson_lefthand": {"rotation": [0, 180, 5], "translation": [10, 0, -10], "scale": [1.25] * 3},
            "ground": {"rotation": [0, 0, 0], "translation": [2, 4, 2], "scale": [0.25] * 3},
            "fixed": {"rotation": [0, 180, 0], "translation": [-2, 4, -5], "scale": [0.5] * 3},
            "gui": {"rotation": [15, -25, -5], "translation": [2, 3, 0], "scale": [0.65] * 3},
        }
        if blocking:
            d["thirdperson_righthand"] = {"rotation": [45, 135, 0], "translation": [3.51, 11, -2], "scale": [1, 1, 1]}
            d["thirdperson_lefthand"] = {"rotation": [45, 135, 0], "translation": [13.51, 3, 5], "scale": [1, 1, 1]}
            d["firstperson_righthand"] = {"rotation": [0, 180, -5], "translation": [-15, 5, -11], "scale": [1.25] * 3}
            d["firstperson_lefthand"] = {"rotation": [0, 180, -5], "translation": [5, 5, -11], "scale": [1.25] * 3}
        m.write(d, particle="minecraft:block/dark_oak_planks", gui_light="front")
    write_json("shield_blocking", {"parent": f"{NS}:item3d/shield_blocking"})
    write_json("shield", {"parent": f"{NS}:item3d/shield", "overrides": vanilla_overrides("shield")})
    return False


def rod(name, cast=False, bait=None):
    """a fishing rod: cork handle, reel, line guides, the line and a red-and-white float (or bait on the line)"""
    m = Model(name)
    pole = Mat(STICK, base=3.0, kind="wood", bevel=0.5)
    cork = Mat(["8a6a44", "b08c62", "d2ae82", "ecd0a6"], base=2.0, kind="organic", bevel=0.5)
    reel = Mat(IRON, base=3.0, kind="metal", bevel=0.5)
    line = Mat(["d8d8d8", "f8f8f8"], base=1, bevel=0)
    bob = Mat(["a81414", "e03a30", "f4f4f4", "ffffff"], base=1.5, bevel=0.3)
    m.box((7.4, -3.0, 7.4), (8.6, 1.6, 8.6), cork)
    r = (-22.5, "x", (8, 1.6, 8)) if cast else None
    m.box((7.55, 1.6, 7.55), (8.45, 21.0, 8.45), pole, rot=r)
    m.box((8.6, 1.8, 7.0), (10.2, 3.6, 9.0), reel)
    m.box((9.4, 2.2, 6.6), (10.0, 3.2, 7.0), reel)
    if not cast:
        for y in (6, 11, 16, 20.4):
            m.box((7.3, y, 7.85), (8.7, y + 0.4, 8.15), reel, ao=False)
        if bait:
            m.box((7.95, 13.0, 7.95), (8.05, 21.0, 8.05), line, ao=False)
            bait(m)
        else:
            m.box((7.95, 2.6, 7.95), (8.05, 21.0, 8.05), line, ao=False)
            m.box((6.6, 15.6, 7.6), (7.4, 16.1, 8.4), bob, ao=False)
            m.box((6.6, 16.1, 7.6), (7.4, 16.6, 8.4), Mat(["e8e8e8", "ffffff"], base=1, bevel=0), ao=False)
    d = blade_held(0, 0.55, -1.0)
    m.write(d, particle=vanilla_layers(name)[-1])


def fishing_rod():
    rod("fishing_rod_cast", cast=True)
    item_model("fishing_rod_cast")
    rod("fishing_rod")
    item_model("fishing_rod", overrides=vanilla_overrides("fishing_rod"))
    return False


def carrot_on_a_stick():
    def bait(m):
        c = Mat(CARROT, base=3.2, kind="organic", bevel=0.5)
        m.box((7.25, 9, 7.25), (8.75, 13, 8.75), c, decal=stripes(2, -1.0))
        m.box((7.5, 8, 7.5), (8.5, 9, 8.5), c)
        m.box((7.5, 13, 7.75), (8.5, 14.5, 8.25), Mat(VINE, base=2.4, bevel=0.3))
    rod("carrot_on_a_stick", bait=bait)
    item_model("carrot_on_a_stick")
    return False


def warped_fungus_on_a_stick():
    def bait(m):
        cap = Mat(FUNGUS, base=3.0, kind="organic", bevel=0.6, glow=True)
        stem = Mat(["c8a890", "e0c8b0", "f4e4d0"], base=1.4, bevel=0.3)
        m.box((7.5, 9, 7.5), (8.5, 12, 8.5), stem)
        m.box((6, 11, 6.5), (10, 13, 9.5), cap, decal=spots(0.15, 99, seed="fungus"))
    rod("warped_fungus_on_a_stick", bait=bait)
    item_model("warped_fungus_on_a_stick")
    return False


def spyglass():
    """a brass telescope: a wide lens tube and a narrower eyepiece, leather wrapped, glass at the end"""
    m = Model("spyglass_in_hand")
    brass = Mat(BRASS, base=3.2, kind="metal", bevel=0.6)
    leather = Mat(LEATHER, base=2.0, kind="wrap", bevel=0.4)
    lens = Mat(["2a5a8a", "4a8ac0", "8ac4f4", "e0f4ff"], base=2.0, kind="gem", bevel=0.2, glow=True)
    m.box((7, 8.5, 7), (9, 13.5, 9), brass)                                # eyepiece end, as the game has it
    m.box((6.9, 2.4, 6.9), (9.1, 8.6, 9.1), leather)
    m.box((6.75, 7.5, 6.75), (9.25, 8.75, 9.25), brass)
    m.box((6.75, 2.0, 6.75), (9.25, 3.0, 9.25), brass)
    m.box((7.25, 1.75, 7.25), (8.75, 2.0, 8.75), lens, faces=("down",), ao=False)
    m.box((7.25, 13.5, 7.25), (8.75, 13.75, 8.75), lens, faces=("up",), ao=False)
    with zipfile.ZipFile(JAR) as z:
        d = json.loads(z.read("assets/minecraft/models/item/spyglass_in_hand.json"))["display"]
    m.write(d, particle="minecraft:item/spyglass")
    write_json("spyglass_in_hand", {"parent": f"{NS}:item3d/spyglass_in_hand",
                                    "textures": {"particle": "minecraft:item/spyglass"}})
    item_model("spyglass", base="spyglass_in_hand")
    return False


# ---------------------------------------------------------------- tools and trinkets
def shears():
    """two blades crossing at a gold pivot, each with a red ring handle"""
    m = Model("shears")
    blade = Mat(IRON, base=4.0, kind="blade", bevel=0.6)
    grip = Mat(["5a0a0a", "8a1414", "b02020", "d03a34"], base=2.6, bevel=0.6)
    pin = Mat(GOLD, base=3.2, kind="metal", bevel=0.3)
    for sgn in (-1, 1):
        r = (sgn * 22.5, "z", (8, 8, 8))
        z0 = 7.5 if sgn < 0 else 8.0
        m.box((7.4, 8, z0), (8.6, 15.5, z0 + 0.5), blade, rot=r)              # a blade
        m.box((7.6, 15.5, z0), (8.4, 16.5, z0 + 0.5), blade, rot=r)           # its point
        m.box((7.5, 4.5, z0), (8.5, 8, z0 + 0.5), blade, rot=(-sgn * 22.5, "z", (8, 8, 8)))   # the arm down
        cx = 8 - sgn * 3.0                                                   # a ring handle below
        for (a, b) in (((cx - 1.75, 1), (cx + 1.75, 1.75)), ((cx - 1.75, 4), (cx + 1.75, 4.75)),
                       ((cx - 1.75, 1.75), (cx - 1, 4)), ((cx + 1, 1.75), (cx + 1.75, 4))):
            m.box((a[0], a[1], 7.4), (b[0], b[1], 8.6), grip)
    m.box((7.4, 7.4, 7.25), (8.6, 8.6, 8.75), pin, ao=False)
    m.write(blade_held(0, 0.5, 1.0))
    item_model("shears")
    return False


def flint_and_steel():
    m = Model("flint_and_steel")
    steel = Mat(IRON, base=3.6, kind="metal", bevel=0.7)
    flint = Mat(FLINT_HEAD, base=2.8, kind="gem", bevel=0.7)
    spark = Mat(["f8b020", "ffe080", "fffbe0"], base=2, bevel=0, glow=True)
    m.box((4.0, 4.0, 7.3), (10.0, 5.2, 8.7), steel)
    m.box((4.0, 5.2, 7.3), (5.2, 9.8, 8.7), steel)
    m.box((4.0, 9.8, 7.3), (10.0, 11.0, 8.7), steel)
    m.box((9.4, 9.0, 7.5), (10.4, 10.0, 8.5), steel)
    m.box((10.0, 5.0, 6.8), (13.6, 9.0, 9.2), flint, decal=spots(0.12, 4.5, seed="fas"))
    m.box((10.6, 8.6, 7.2), (12.8, 10.0, 8.8), flint)
    m.box((9.6, 9.8, 7.8), (10.2, 10.4, 8.2), spark, ao=False)
    m.write(upright(**HELD))
    item_model("flint_and_steel")
    return False


def totem_of_undying():
    """a little golden idol: arms raised, green emerald eyes and belt, a robe flaring at the bottom"""
    m = Model("totem_of_undying")
    gold = Mat(GOLD, base=3.0, kind="metal", bevel=0.8)
    robe = Mat(GOLD, base=2.4, kind="metal", bevel=0.8)
    eye = Mat(EMERALD, base=3.6, kind="gem", bevel=0.2, glow=True)
    m.box((6, 10, 6.5), (10, 14.5, 9.5), gold, decal=shine)                # head
    m.box((7.5, 11, 9.5), (8.5, 12.5, 10.25), gold)                         # nose
    m.box((6.5, 12.5, 9.5), (7.5, 13.5, 9.75), eye, ao=False)
    m.box((8.5, 12.5, 9.5), (9.5, 13.5, 9.75), eye, ao=False)
    m.box((6, 4.5, 7), (10, 10, 9), gold)                                   # body
    m.box((5, 0, 6.5), (11, 4.5, 9.5), robe, decal=stripes(2, -0.8, axis="v", faces=("south", "north")))
    m.box((6, 4.5, 6.8), (10, 5.5, 9.2), eye)                               # emerald belt
    m.box((2.5, 8.5, 7.25), (6, 10, 8.75), gold), m.box((10, 8.5, 7.25), (13.5, 10, 8.75), gold)  # arms
    m.box((2, 10, 7.25), (3.5, 12.5, 8.75), gold), m.box((12.5, 10, 7.25), (14, 12.5, 8.75), gold)  # raised hands
    m.write(upright(scale=0.42, lift=5.0))
    item_model("totem_of_undying")
    return False


def lead():
    """a coiled lead rope with a knotted loop"""
    m = Model("lead")
    rope = Mat(ROPE, base=2.4, bevel=0.5)
    twist = stripes(2, 1.0, axis="v")
    for (a, b) in (((4, 3, 7.25), (12, 4.5, 8.75)), ((4, 11, 7.25), (12, 12.5, 8.75)),
                   ((3, 4, 7.25), (4.5, 11, 8.75)), ((11.5, 4, 7.25), (13, 11, 8.75)),
                   ((5.5, 5, 8.75), (10.5, 6.25, 9.75)), ((5.5, 9.25, 8.75), (10.5, 10.5, 9.75))):
        m.box(a, b, rope, decal=twist)
    m.box((6.5, 1, 7), (9.5, 4.5, 9), rope)                                # the knot
    m.box((7.25, 0, 7.4), (8.75, 1, 8.6), rope)
    d = upright(**HELD)
    d["head"] = vanilla_display("lead")["head"]
    m.write(d)
    item_model("lead")
    return False


def name_tag():
    m = Model("name_tag")
    tag = Mat(TAG, base=2.6, bevel=0.6)
    ring = Mat(BRASS, base=3.0, kind="metal", bevel=0.4)
    cord = Mat(STRING, base=2.0, bevel=0.3)

    def writing(k, ii, jj, w, h, face):
        if face == "south" and w > 5:
            k = np.where(((jj == 2) | (jj == 4)) & (ii >= 2) & (ii <= w - 2) & ((ii * 7 + jj) % 5 != 0), 0.3, k)
        return k

    m.box((5, 3, 7.5), (14, 10, 8.5), tag, decal=writing)
    m.box((3.5, 4, 7.6), (5, 9, 8.4), tag)                                 # the pointed end
    m.box((2.5, 5, 7.6), (3.5, 8, 8.4), tag)
    m.box((3.25, 6, 7.4), (4.5, 7, 8.6), ring, ao=False)                    # the eyelet
    m.box((1, 6.25, 7.75), (3.25, 6.75, 8.25), cord, ao=False)              # the cord through it
    m.box((0.5, 6.25, 7.75), (1, 11, 8.25), cord, ao=False)
    m.write(upright(**HELD))
    item_model("name_tag")
    return False


def saddle():
    m = Model("saddle")
    s = Mat(SADDLE, base=3.0, kind="organic", bevel=0.7)
    trim = Mat(SADDLE, base=4.4, bevel=0.5)
    iron = Mat(IRON, base=3.0, kind="metal", bevel=0.5)
    m.box((3, 4, 4), (13, 6, 12), s, decal=shine)                           # the seat
    m.box((3, 6, 10), (13, 8.5, 12), s)                                     # the cantle behind
    m.box((5.5, 6, 3.5), (10.5, 9, 5.5), s)                                 # the pommel in front
    m.box((2.5, 3.5, 3.5), (13.5, 4, 12.5), trim)
    for x in (2, 13.25):                                                    # straps and stirrups
        m.box((x, 0.5, 7), (x + 0.75, 4, 8.5), s)
        m.box((x - 0.5, -1.5, 6.5), (x + 1.25, 0.5, 9), iron)
    m.write(upright(scale=0.4, lift=6.0, tilt=30))
    item_model("saddle")
    return False


def brush():
    """a wooden brush, built on the diagonal like its picture so the game's own brushing movement fits it"""
    handle = Mat(STICK, base=3.0, kind="wood", bevel=0.5)
    ferrule = Mat(BRASS, base=3.0, kind="metal", bevel=0.4)
    hair = Mat(BRUSH_HAIR, base=2.6, bevel=0.4)
    r = (45, "z", (8, 8, 8))
    for name in ("brush", "brush_brushing_0", "brush_brushing_1", "brush_brushing_2"):
        m = Model(name)
        m.box((7.25, 0.5, 7.25), (8.75, 9, 8.75), handle, rot=r)
        m.box((7, 9, 7), (9, 10.5, 9), ferrule, rot=r)
        m.box((6, 10.5, 6.75), (10, 13, 9.25), hair, rot=r, decal=stripes(2, -0.9, axis="v"))
        m.box((5.5, 13, 7), (10.5, 14.5, 9), hair, rot=r, decal=stripes(2, -0.9, axis="v"))
        m.write(vanilla_display(name), particle="minecraft:item/brush")
        if name != "brush":
            item_model(name, layers=["minecraft:item/brush"])
    item_model("brush", overrides=vanilla_overrides("brush"))
    return False


def goat_horn():
    """a curved horn, wide at the bell, a brass band, built in the plane of its picture so the game's own way of
    raising it to play fits it"""
    horn = Mat(HORN, base=3.0, kind="organic", bevel=0.7)
    band = Mat(BRASS, base=3.0, kind="metal", bevel=0.4)
    for name in ("goat_horn", "tooting_goat_horn"):
        m = Model(name)
        segs = [((2, 2.5), 1.0), ((3.5, 3.5), 1.4), ((5, 5), 1.8), ((6.5, 6.75), 2.2), ((8, 8.75), 2.6),
                ((9.5, 10.75), 3.0)]
        for (x, y), r in segs:
            m.box((x - r / 2, y - r / 2, 8 - r / 2), (x + r, y + r, 8 + r / 2), horn, decal=stripes(2, -0.7))
        m.box((10.5, 11.25, 6.25), (13.5, 14.5, 9.75), horn)                   # the bell
        m.box((11, 14.5, 6.75), (13, 14.75, 9.25), Mat(HORN, base=0.5, bevel=0), faces=("up",), ao=False)
        m.box((5.75, 5.75, 6.75), (7.25, 7.25, 9.25), band)
        d = vanilla_display(name)
        # a solid horn shows far more of itself than the flat picture does: held smaller
        if name == "goat_horn":
            up = upright(scale=0.42, lift=5.5)
            d["firstperson_righthand"], d["firstperson_lefthand"] = up["firstperson_righthand"], up["firstperson_lefthand"]
        else:
            for k in ("firstperson_righthand", "firstperson_lefthand"):
                d[k] = dict(d[k], scale=[0.7] * 3)
        m.write(d, particle="minecraft:item/goat_horn")
    item_model("tooting_goat_horn", layers=["minecraft:item/goat_horn"])
    item_model("goat_horn", overrides=vanilla_overrides("goat_horn"))
    return False


# ---------------------------------------------------------------- books, map, firework
def book_like(name, extra=None):
    m = Model(name)
    cover = Mat(COVER[name], base=2.6, kind="organic", bevel=0.8, glow=(name == "enchanted_book"))
    pages = Mat(PAGES, base=3.0, bevel=0.3)
    gold = Mat(GOLD, base=3.2, kind="metal", bevel=0.4)

    def page_lines(k, ii, jj, w, h, face):
        # the stacked page edges
        if face in ("east", "up", "down"):
            k = np.where((jj if face == "east" else ii) % 2 == 0, k - 0.7, k)
        return k

    def plate(k, ii, jj, w, h, face):
        if face == "south" and w > 6:
            corner = ((ii <= 1) | (ii >= w - 2)) & ((jj <= 1) | (jj >= h - 2))
            k = np.where(corner, 99, k)                                        # gold-ish corners (light)
        return k

    m.box((3.75, 1.5, 6.75), (12.5, 14.5, 9.25), pages, decal=page_lines)
    m.box((3.25, 1, 9.25), (13, 15, 10), cover, decal=plate)                   # front cover
    m.box((3.25, 1, 6), (13, 15, 6.75), cover)                                 # back cover
    m.box((3, 1, 6), (3.75, 15, 10), cover)                                    # spine
    for y in (3, 12.5):
        m.box((2.75, y, 5.75), (3.5, y + 0.75, 10.25), gold)                   # gold bands on the spine
    for (x, y) in ((3.5, 1.25), (12, 1.25), (3.5, 14), (12, 14)):
        m.box((x, y, 10), (x + 0.75, y + 0.75, 10.15), gold, faces=("south",), ao=False)   # corner caps
    if extra:
        extra(m)
    m.write(upright(scale=0.42, lift=6.0, turn=-30))
    item_model(name)
    return False


def book():
    return book_like("book")


def written_book():
    def ribbon(m):
        r = Mat(RED_GEM, base=2.4, bevel=0.3)
        m.box((9, -1.5, 8), (10, 1.5, 8.25), r, ao=False)                      # a ribbon bookmark
        m.box((6, 7, 10), (10.5, 9, 10.2), Mat(GOLD, base=3.4, bevel=0.3), faces=("south",), ao=False)  # the title
    return book_like("written_book", ribbon)


def writable_book():
    def quill(m):
        f = Mat(FEATHER, base=3.0, bevel=0.2)
        nib = Mat(INK_BLACK, base=1.0, bevel=0.2)
        rr = (-22.5, "z", (11, 6, 10.5))
        m.box((10.6, 6, 10.2), (11.4, 17, 10.8), f, rot=rr)                     # a quill tucked against the cover
        m.box((10.75, 4.5, 10.3), (11.25, 6, 10.7), nib, rot=rr)
    return book_like("writable_book", quill)


def enchanted_book():
    def rune(m):
        g = Mat(DIAMOND, base=5.0, kind="gem", bevel=0.3, glow=True)
        m.box((7.25, 7, 10), (8.75, 9, 10.4), g, ao=False)                       # a glowing gem set in the cover
    return book_like("enchanted_book", rune)


def knowledge_book():
    return book_like("knowledge_book")


def map_():
    """an empty map: a roll of parchment tied with a cord"""
    m = Model("map")
    p = Mat(PAPER[0:1] + ["c8b890", "e0d2ae", "f0e6cc", "fbf4e4"], base=2.6, bevel=0.5)
    cord = Mat(RED_GEM, base=2.2, bevel=0.3)
    m.box((2, 6, 7), (14, 10, 9), p, decal=shine)
    m.box((2, 6.5, 6.5), (14, 9.5, 9.5), p)
    m.box((1.5, 7, 7.25), (2, 9, 8.75), Mat(PAPER, base=1.0, bevel=0), faces=("west",), ao=False)   # the rolled end
    m.box((7, 5.75, 6.25), (8.5, 10.25, 9.75), cord)
    m.write(upright(**HELD))
    item_model("map")
    return False


def firework_rocket():
    m = Model("firework_rocket")
    tube = Mat(ROCKET, base=3.0, bevel=0.6)
    stripe = stripes(3, 99, axis="h", faces=("north", "south", "east", "west"))
    cone = Mat(GOLD, base=3.0, kind="metal", bevel=0.5)
    stick = Mat(STICK, base=3.0, kind="wood", bevel=0.4)
    fuse = Mat(["3a3a3a", "6a6a6a"], base=1, bevel=0)
    m.box((6.5, 4, 6.5), (9.5, 12, 9.5), tube, decal=stripe)
    m.box((7, 12, 7), (9, 13.5, 9), cone)
    m.box((7.5, 13.5, 7.5), (8.5, 14.5, 8.5), cone)
    m.box((7.6, -2, 7.6), (8.4, 4, 8.4), stick)
    m.box((7.75, 3, 9.5), (8.25, 5, 10.25), fuse, ao=False)
    m.write(upright(scale=0.42, lift=5.0))
    item_model("firework_rocket")
    return False


SPECIAL = {
    "compass": compass, "recovery_compass": recovery_compass, "clock": clock, "bow": bow, "crossbow": crossbow,
    "trident": trident, "shield": shield, "fishing_rod": fishing_rod, "carrot_on_a_stick": carrot_on_a_stick,
    "warped_fungus_on_a_stick": warped_fungus_on_a_stick, "spyglass": spyglass, "shears": shears,
    "flint_and_steel": flint_and_steel, "totem_of_undying": totem_of_undying, "lead": lead, "name_tag": name_tag,
    "saddle": saddle, "brush": brush, "goat_horn": goat_horn, "book": book, "writable_book": writable_book,
    "written_book": written_book, "enchanted_book": enchanted_book, "knowledge_book": knowledge_book, "map": map_,
    "firework_rocket": firework_rocket,
}
