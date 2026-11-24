#!/usr/bin/env python3
"""Batch 11 of Lifelike Motion's 3D items: plants - flowers, saplings, grasses and ferns, sea plants, mushrooms
and nether plants, corals and seeds (built with tools/models.py's parts and painter; run tools/models.py to write
them). Plants are held up by the stem, facing you; seeds are a little heap in your palm.

Each plant is built from a few shaped parts like a modeler would: stems and blades tipped at 22.5 / 45 degrees,
petals as crossed plates round a raised centre, caps and canopies as rounded blocks."""
import random

import numpy as np

from models import Mat, Model, upright, LEAF
from models_food import spots, stripes, shine, chain, blob
from models_discs import ramp, circle_rows

FLOWER = dict(scale=0.45, lift=4.5, tilt=8)
TALL = dict(scale=0.36, lift=2.5, tilt=8)
SEEDS = dict(scale=0.52, lift=7.0, tilt=30)

STEM = ["1c3610", "284c16", "36641e", "4a7e28", "629a36"]
GRASS = ["1e4012", "2a5a18", "3a7622", "4e922e", "68ae3e", "8ac858"]
DARK_LEAF = ["122a0c", "1a3a10", "244e16", "30641e", "407c28", "549434"]
BARK = ["2a1a0c", "3e2814", "56381e", "6e4a28", "866034"]
BIRCH_BARK = ["2a2a26", "8e8c84", "c0beb4", "dcdad0", "eeece4"]
CHERRY_BLOSSOM = ["a0406a", "c8608a", "e488ac", "f4a8c6", "fcc8dc", "fff0f6"]
DRY = ["3a2410", "54361a", "6e4a24", "8a6030", "a4783e"]
SEA = ["0c3a26", "125236", "1a6c46", "268a58", "38a86c", "56c488"]
KELP = ["1c3410", "284a16", "36621c", "487c24", "5e9630"]
BAMBOO = ["2e4a10", "406616", "56861e", "6ea628", "8cc23a", "b2dc62"]
SHROOM_STEM = ["8a7e6a", "b0a48c", "d0c6ae", "e8e0cc", "f6f2e6"]
RED_CAP = ["4a0606", "740c0c", "a01414", "c82020", "e43a30", "f47060"]
BROWN_CAP = ["3a2416", "54361e", "6e4a2a", "8a6038", "a47a4c", "bc9466"]
CRIMSON = ["3a0810", "5c0c18", "841224", "a81c30", "cc3040", "e85a5a"]
WARPED = ["0a3a36", "0e544e", "147068", "1c8e84", "2eb0a2", "5cd4c4"]
NETHER_STEM = ["2a1a1a", "422828", "5c3a38", "7a5048", "966a5a"]
ORANGE_SPOT = ["8a3a08", "c05a10", "f08a20", "ffb848", "ffdc8a"]
WART = ["3a0408", "5c0810", "841018", "a81a22", "c8302e", "e05a48"]
SEED_PALS = {"wheat_seeds": ["3a4a14", "566a1e", "748a2a", "92a83a", "b4c45a"],
             "pumpkin_seeds": ["8a7a4a", "b4a26a", "d4c48a", "ece0b0", "fbf6e0"],
             "melon_seeds": ["0c0a08", "1a1612", "2c241c", "40362a", "5c5040"],
             "beetroot_seeds": ["3a2412", "56361c", "724a28", "8e6036", "ac7a48"],
             "torchflower_seeds": ["3a4a1a", "566c24", "7a8e30", "9eae44", "c4cc6a"]}
COCOA = ["2a1408", "42200e", "5c3016", "784020", "96562c", "b4703c"]
PITCHER = ["1a3a4a", "245a6e", "2e7a90", "3c9cb0", "5cbccc", "94dce4"]


def blade(m, mat, x, y, length, angle=0, width=1.0, z=7.6, depth=0.8, axis="z"):
    """a straight blade (a leaf, a stalk, a petal) rising from (x, y), tipped by angle about its foot"""
    m.box((x - width / 2, y, z), (x + width / 2, y + length, z + depth), mat, ao=False,
          rot=(angle, axis, (x, y, z + depth / 2)) if angle else None)


def bent(m, mat, x, y, parts, z=7.6, width=1.0, depth=0.8):
    """a stalk that bends as it rises: parts of (length, angle) each starting where the last one ended"""
    import math
    for (length, angle) in parts:
        blade(m, mat, x, y, length, angle, width, z, depth)
        a = math.radians(angle)
        x, y = x - length * math.sin(a), y + length * math.cos(a)
    return x, y


# ---------------------------------------------------------------- flower heads
def star(m, pal, cx, cy, z, r, centre_pal=None, cr=0.8, petals=8, thick=0.5, base=3.2, pw=0.6):
    """an open flower facing you: crossed plates of petals (half width pw) round a raised centre"""
    petal = Mat(pal, base=base, bevel=0.4)
    m.box((cx - r, cy - pw, z), (cx + r, cy + pw, z + thick), petal, ao=False)
    m.box((cx - pw, cy - r, z + 0.02), (cx + pw, cy + r, z + thick - 0.02), petal, ao=False)
    if petals == 8:
        for a in (45, -45):
            m.box((cx - r * 0.9, cy - pw * 0.85, z - 0.05), (cx + r * 0.9, cy + pw * 0.85, z + thick - 0.08), petal,
                  ao=False, rot=(a, "z", (cx, cy, z)))
    if centre_pal:
        m.box((cx - cr, cy - cr, z - 0.2), (cx + cr, cy + cr, z + thick + 0.35),
              Mat(centre_pal, base=len(centre_pal) - 2.5, bevel=0.3), decal=spots(0.25, 99, seed=cx), ao=False)


def cup(m, pal, cx, cy, cz, r=1.3, h=2.4, base=3.0):
    """a tulip's cup: a closed bloom with four petal tips standing up round its rim"""
    p = Mat(pal, base=base, bevel=0.5)
    m.box((cx - r, cy, cz - r), (cx + r, cy + h, cz + r), p, decal=shine)
    m.box((cx - r * 0.7, cy - 0.5, cz - r * 0.7), (cx + r * 0.7, cy, cz + r * 0.7), p)
    for dx, dz in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        m.box((cx + dx * r - (0.8 if dx > 0 else 0), cy + h, cz + dz * r - (0.8 if dz > 0 else 0)),
              (cx + dx * r + (0 if dx > 0 else 0.8), cy + h + 0.9, cz + dz * r + (0 if dz > 0 else 0.8)),
              Mat(pal, base=base + 0.8, bevel=0.3), ao=False)


def pompom(m, pal, cx, cy, cz, r, speckle=0.2):
    """a round ball of tiny flowers (an allium, a dandelion)"""
    p = Mat(pal, base=3.0, bevel=0.5)
    d = spots(speckle, 99, seed=int(cx * 10 + cy))
    m.box((cx - r, cy - r * 0.6, cz - r * 0.6), (cx + r, cy + r * 0.6, cz + r * 0.6), p, decal=d)
    m.box((cx - r * 0.6, cy - r, cz - r * 0.6 + 0.02), (cx + r * 0.6, cy + r, cz + r * 0.6 - 0.02), p, decal=d)
    m.box((cx - r * 0.6 + 0.02, cy - r * 0.6 + 0.02, cz - r), (cx + r * 0.6 - 0.02, cy + r * 0.6 - 0.02, cz + r), p,
          decal=d)
    m.box((cx - r * 0.82, cy - r * 0.82, cz - r * 0.82), (cx + r * 0.82, cy + r * 0.82, cz + r * 0.82), p, decal=d)


def rose(m, pal, cx, cy, cz, r=1.5, base=3.0):
    """a rose: layers of petals wrapped round each other, each turned against the last"""
    for n, (rr, y0, y1, a) in enumerate(((r, 0, 1.6, 0), (r * 0.8, 0.4, 2.1, 45), (r * 0.5, 0.9, 2.4, 0))):
        m.box((cx - rr, cy + y0, cz - rr), (cx + rr, cy + y1, cz + rr), Mat(pal, base=base + 0.6 * n, bevel=0.6),
              rot=(a, "y", (cx, cy, cz)) if a else None, ao=False)
    m.box((cx - r * 0.7, cy - 0.5, cz - r * 0.7), (cx + r * 0.7, cy, cz + r * 0.7), Mat(STEM, base=3, bevel=0.4))


def leaves_pair(m, mat, x, y, length=3.5, spread=45, z=7.6):
    blade(m, mat, x, y, length, spread, 1.2, z)
    blade(m, mat, x, y + 0.6, length * 0.85, -spread, 1.2, z + 0.05)


# ---------------------------------------------------------------- flowers
def stem_and_leaves(m, top, leaf_y=2.0, leaf_len=3.5, mat=None):
    mat = mat or Mat(STEM, base=3.0, bevel=0.4)
    blade(m, mat, 8, 0, top, 0, 1.0)
    leaves_pair(m, Mat(LEAF, base=2.8, bevel=0.5), 8, leaf_y, leaf_len)


def b_dandelion(m):
    stem_and_leaves(m, 8)
    pompom(m, ramp("f8d020"), 8, 9.5, 8, 2.2, 0.25)


def b_poppy(m):
    stem_and_leaves(m, 8.5)
    star(m, ramp("d01818"), 8, 10, 7.6, 2.5, ramp("201010"), 0.8, pw=1.3)


def b_blue_orchid(m):
    stem_and_leaves(m, 7)
    blade(m, Mat(STEM, base=3, bevel=0.4), 8, 6, 4, 22.5)
    star(m, ramp("2aa8e8"), 8, 8.5, 7.6, 2.0, ramp("d8f0ff"), 0.6)
    star(m, ramp("2aa8e8"), 6.4, 10.8, 7.4, 1.5, ramp("d8f0ff"), 0.5)


def b_allium(m):
    stem_and_leaves(m, 10, leaf_len=3.0)
    pompom(m, ramp("b060e0"), 8, 12, 8, 2.6, 0.3)


def b_azure_bluet(m):
    stem_and_leaves(m, 5, leaf_len=2.6)
    for (x, y, z) in ((8, 6.5, 7.8), (6.2, 7.6, 7.2), (9.8, 8.2, 7.5)):
        blade(m, Mat(STEM, base=3, bevel=0.3), 8, 4.5, y - 4.5, 0 if x == 8 else (22.5 if x < 8 else -22.5), 0.8)
        star(m, ramp("e8eef8"), x, y, z, 1.2, ramp("f0d040"), 0.45)


def b_tulip(colour):
    def b(m):
        stem_and_leaves(m, 8, leaf_len=4.0)
        cup(m, ramp(colour), 8, 8.5, 8)
    return b


def b_oxeye_daisy(m):
    stem_and_leaves(m, 8.5)
    star(m, ramp("f4f4ee"), 8, 10, 7.6, 2.6, ramp("f0c020"), 0.9)


def b_cornflower(m):
    stem_and_leaves(m, 8.5)
    star(m, ramp("4060e0"), 8, 10, 7.6, 2.4, ramp("1a2470"), 0.7)
    for a in (22.5, -22.5):                                         # its ragged petal tips
        blade(m, Mat(ramp("6080f0"), base=3.4, bevel=0.3), 8, 10, 3.0, a, 0.6, 7.7, 0.4)


def b_lily_of_the_valley(m):
    green = Mat(LEAF, base=3.0, bevel=0.5)
    for a, z in ((22.5, 7.4), (-22.5, 7.8)):                        # two broad leaves from the ground
        blade(m, green, 8, 0, 8, a, 2.2, z, 0.5)
    s = Mat(STEM, base=3, bevel=0.3)
    blade(m, s, 8.5, 0, 9, 0, 0.7, 8.6, 0.6)                          # the stem, arching over at the top
    blade(m, s, 8.5, 9, 2, -45, 0.7, 8.6, 0.6)
    m.box((9.7, 10.0, 8.6), (12.6, 10.6, 9.2), s, ao=False)
    bell = Mat(ramp("f6f6f0"), base=3.4, bevel=0.4)
    for (bx, by) in ((9.0, 9.4), (10.6, 10.0), (12.0, 10.0)):         # white bells hanging under it
        m.box((bx - 0.6, by - 1.2, 8.3), (bx + 0.6, by, 9.5), bell, ao=False)
        m.box((bx - 0.8, by - 1.5, 8.1), (bx + 0.8, by - 1.1, 9.7), bell, ao=False)


def b_wither_rose(m):
    stem_and_leaves(m, 8, mat=Mat(["0e0e0c", "1a1a16", "282822", "38382e"], base=2, bevel=0.3))
    rose(m, ["06060a", "101014", "1a1a20", "26262e", "36363e", "4a4a54"], 8, 8.5, 8, 1.7)


def b_torchflower(m):
    stem_and_leaves(m, 8)
    fl = ["7a1a08", "b02e0c", "e05414", "f88a28", "fcc048", "fff0a0"]
    m.box((6.8, 8, 6.8), (9.2, 9.5, 9.2), Mat(fl, base=3.0, bevel=0.4))
    for a, h, z in ((0, 4, 7.6), (22.5, 3.2, 7.2), (-22.5, 3.2, 8.2), (45, 2.4, 7.9), (-45, 2.4, 7.5)):
        blade(m, Mat(fl, base=4.0 - abs(a) / 30, bevel=0.3), 8, 9.2, h, a, 1.0, z, 0.8)   # petals like flames


def b_sunflower(m):
    s = Mat(STEM, base=3.0, bevel=0.4)
    blade(m, s, 8, 0, 19, 0, 1.4)
    leaf = Mat(LEAF, base=2.8, bevel=0.5)
    for y, a in ((4, 45), (7, -45), (11, 45), (14, -45)):
        blade(m, leaf, 8, y, 4.5 - y * 0.12, a, 2.0, 7.4, 0.5)
    petal = Mat(ramp("f8c818"), base=3.2, bevel=0)
    centre = Mat(["2a1608", "3e220e", "553216", "6e4420", "8a5a2c"], base=2.2, bevel=0)
    for (y0, y1, hw) in circle_rows(4.5, 20):                          # the big face, looking at you
        m.box((8 - hw, y0, 8.6), (8 + hw, y1, 9.4), petal,
              decal=lambda k, ii, jj, w, h, face: np.where((ii + jj) % 2 == 0, k + 0.8, k), ao=False)
    for (y0, y1, hw) in circle_rows(2.5, 20):
        m.box((8 - hw, y0, 9.3), (8 + hw, y1, 9.9), centre, decal=spots(0.3, 4, seed="sun"), ao=False)
    m.box((7.2, 15.5, 8.0), (8.8, 17.5, 8.7), s)                      # the neck holding it


def bush(m, leaf_pal, bloom_pal, blooms, bloom_kind="cluster", height=14):
    """a tall flowering bush: stems, leafy clumps, and blooms set among them"""
    s = Mat(STEM, base=2.8, bevel=0.4)
    for a, z in ((0, 7.6), (22.5, 7.3), (-22.5, 7.9)):
        blade(m, s, 8, 0, height * 0.75, a, 0.9, z, 0.7)
    leaf = Mat(leaf_pal, base=3.0, bevel=0.5)
    for (x, y, r) in ((8, 6, 2.6), (5.6, 9, 2.0), (10.4, 9.5, 2.0), (8, 11.5, 2.2)):
        m.box((x - r, y - r * 0.7, 8 - r * 0.8), (x + r, y + r * 0.7, 8 + r * 0.8), leaf, decal=spots(0.12, 99, seed=x + y))
    for (x, y, z) in blooms:
        if bloom_kind == "rose":
            rose(m, bloom_pal, x, y, z, 1.2, base=2.6)
        else:
            pompom(m, bloom_pal, x, y, z, 1.4, 0.3)


def b_lilac(m):
    bush(m, LEAF, ramp("c07ad8"), ((8, 14.5, 8), (5.2, 12.5, 8.4), (10.8, 13, 7.6), (7, 11, 10.2)))


def b_rose_bush(m):
    bush(m, DARK_LEAF, ramp("c81820"), ((8, 13, 8.6), (5.4, 10.5, 9.2), (10.6, 11, 9.0), (8.4, 8.5, 10.2)), "rose")


def b_peony(m):
    bush(m, LEAF, ramp("f0a8d0"), ((8, 14.5, 8), (5.2, 12.0, 8.6), (10.8, 12.5, 8.2), (8, 10.5, 10.2)))


def b_pitcher_plant(m):
    s = Mat(STEM, base=3.0, bevel=0.4)
    blade(m, s, 8, 0, 14, 0, 1.2)
    leaf = Mat(LEAF, base=2.8, bevel=0.5)
    for y, a in ((2, 45), (3, -45), (6, 22.5), (7, -22.5)):
        blade(m, leaf, 8, y, 5, a, 2.2, 7.4, 0.5)
    p = Mat(PITCHER, base=3.0, bevel=0.5)
    m.box((6.4, 13, 6.4), (9.6, 17, 9.6), p, decal=shine)               # the pitcher
    m.box((6.0, 17, 6.0), (10.0, 17.8, 10.0), Mat(PITCHER, base=4.0, bevel=0.4))
    for a, z in ((22.5, 7.0), (-22.5, 8.6), (45, 7.8)):                 # blue-violet petals spilling out
        blade(m, Mat(ramp("6a6ae0"), base=3.4, bevel=0.3), 8, 17.2, 4, a, 1.4, z, 0.6)


def b_pink_petals(m):
    """little pink flowers lying among clover leaves, as if picked up off the ground in a clump"""
    leaf = Mat(LEAF, base=3.0, bevel=0.4)
    for (x, z) in ((5.5, 6), (10, 7), (7, 10.5), (11, 11)):
        m.box((x - 1.6, 0.5, z - 1.6), (x + 1.6, 1.0, z + 1.6), leaf, rot=(45, "y", (x, 0.5, z)), ao=False)
    s = Mat(STEM, base=3, bevel=0.3)
    for (x, z, h) in ((6, 7, 3), (9.5, 9, 4), (11, 6.2, 2.5), (7.4, 11, 2.2)):
        m.box((x - 0.3, 1.0, z - 0.3), (x + 0.3, 1.0 + h, z + 0.3), s, ao=False)
        star(m, ramp("f4a0c8"), x, 1.0 + h + 0.8, z - 0.25, 1.3, ramp("f8e070"), 0.4, thick=0.5)


FLOWERS = {
    "dandelion": b_dandelion, "poppy": b_poppy, "blue_orchid": b_blue_orchid, "allium": b_allium,
    "azure_bluet": b_azure_bluet, "red_tulip": b_tulip("d82020"), "orange_tulip": b_tulip("f07a1a"),
    "white_tulip": b_tulip("f0f0ea"), "pink_tulip": b_tulip("f0a0c8"), "oxeye_daisy": b_oxeye_daisy,
    "cornflower": b_cornflower, "lily_of_the_valley": b_lily_of_the_valley, "wither_rose": b_wither_rose,
    "torchflower": b_torchflower, "pink_petals": b_pink_petals,
}
TALL_FLOWERS = {"sunflower": b_sunflower, "lilac": b_lilac, "rose_bush": b_rose_bush, "peony": b_peony,
                "pitcher_plant": b_pitcher_plant}


# ---------------------------------------------------------------- saplings
def canopy(m, pal, clumps, seed):
    leaf = Mat(pal, base=3.0, bevel=0.6)
    for n, (x, y, z, r, h) in enumerate(clumps):
        m.box((x - r, y, z - r * 0.85), (x + r, y + h, z + r * 0.85), leaf, decal=spots(0.14, 99, seed=f"{seed}{n}"))
        m.box((x - r * 0.75, y + 0.3, z - r), (x + r * 0.75, y + h - 0.3, z + r), leaf,
              decal=spots(0.12, 0.6, seed=f"{seed}{n}b"))


def sapling(name, leaf_pal, trunk_pal=BARK, shape="round"):
    def make():
        m = Model(name)
        trunk = Mat(trunk_pal, base=2.6, kind="wood", bevel=0.4)
        if shape == "cone":                                          # spruce: tiers of needles
            blade(m, trunk, 8, 0, 11, 0, 1.2, 7.4, 1.2)
            leaf = Mat(leaf_pal, base=3.0, bevel=0.5)
            for (y, r) in ((4, 3.2), (6.8, 2.5), (9.2, 1.8), (11.2, 1.0)):
                m.box((8 - r, y, 8 - r), (8 + r, y + 1.8, 8 + r), leaf, decal=spots(0.15, 99, seed=f"{name}{y}"))
            m.box((7.6, 13, 7.6), (8.4, 14, 8.4), leaf)
        elif shape == "flat":                                        # acacia: a leaning trunk, a flat crown
            bent(m, trunk, 7, 0, ((5, -22.5), (4, 22.5)), 7.5, 1.2, 1.2)
            canopy(m, leaf_pal, ((8.4, 9, 8, 4.2, 1.6), (8.4, 10.6, 8, 2.6, 1.0)), name)
        elif shape == "propagule":                                   # mangrove: a long hanging pod
            m.box((7.5, 0, 7.5), (8.5, 9, 8.5), Mat(["2a3a10", "3e5416", "566e1e", "6e8828", "8aa236"], base=2.6,
                                                     bevel=0.4))
            m.box((7.3, 8.5, 7.3), (8.7, 10, 8.7), Mat(BARK, base=3, bevel=0.4))
            leaf = Mat(leaf_pal, base=3.0, bevel=0.5)
            for a, z in ((45, 7.6), (-45, 7.9), (0, 7.4)):
                blade(m, leaf, 8, 10, 3.2, a, 1.6, z, 0.5)
        else:
            thick = 1.6 if name == "dark_oak_sapling" else 1.2
            blade(m, trunk, 8, 0, 8, 0, thick, 8 - thick / 2, thick)
            blade(m, trunk, 8, 4, 3, 45, 0.8, 7.6, 0.8)              # a little branch
            if name == "jungle_sapling":
                canopy(m, leaf_pal, ((8, 7, 8, 3.6, 2.6), (5.6, 9.2, 8.6, 2.2, 2.0), (10.4, 9.0, 7.4, 2.2, 2.2),
                                     (8, 10.6, 8, 2.0, 1.6)), name)
            else:
                canopy(m, leaf_pal, ((8, 7, 8, 3.2, 3.0), (6.2, 9.4, 8.6, 2.2, 2.0), (9.8, 9.6, 7.6, 2.0, 2.0),
                                     (8, 11, 8, 1.6, 1.4)), name)
        m.write(upright(**FLOWER))
    return make


SAPLINGS = {
    "oak_sapling": sapling("oak_sapling", LEAF),
    "spruce_sapling": sapling("spruce_sapling", ["10241a", "183424", "22462e", "2e5a3a", "3c6e48", "50845a"],
                              shape="cone"),
    "birch_sapling": sapling("birch_sapling", ["2a4a14", "3c661c", "528426", "6ca232", "88bc44", "a8d468"],
                             BIRCH_BARK),
    "jungle_sapling": sapling("jungle_sapling", ["14400c", "1e5812", "2a721a", "388e22", "4aaa2e", "68c444"]),
    "acacia_sapling": sapling("acacia_sapling", ["2c4a0c", "3e6412", "547e1a", "6c9824", "88b230", "a8c84c"],
                              ["3a3630", "56504a", "6e6860", "8a827a", "a49c92"], shape="flat"),
    "dark_oak_sapling": sapling("dark_oak_sapling", DARK_LEAF, ["1a1008", "2a1a0c", "3c2612", "4e341a", "624424"]),
    "cherry_sapling": sapling("cherry_sapling", CHERRY_BLOSSOM, ["2a1218", "3e1c24", "542830", "6c363e", "84464c"]),
    "mangrove_propagule": sapling("mangrove_propagule", ["1e4410", "2a5c16", "3a761e", "4e9028", "68aa38"],
                                  shape="propagule"),
}


# ---------------------------------------------------------------- grasses, ferns, vines, sea plants
def tuft(m, pal, blades, z0=7.2):
    mat = Mat(pal, base=3.0, bevel=0.4)
    for n, (x, length, angle, w) in enumerate(blades):
        blade(m, mat, x, 0, length, angle, w, z0 + (n % 3) * 0.45, 0.5)


def frond(m, mat, x, y, length, angle, z):
    """a fern frond: a rib with leaflets down both sides, getting smaller toward the tip"""
    import math
    blade(m, mat, x, y, length, angle, 0.6, z, 0.5)
    a = math.radians(angle)
    for i in range(1, int(length)):
        px, py = x - i * math.sin(a), y + i * math.cos(a)
        s = (1 - i / length) * 1.6 + 0.5
        m.box((px - s, py - 0.3, z + 0.05), (px + s, py + 0.3, z + 0.45), mat, ao=False,
              rot=(angle, "z", (px, py, z + 0.25)) if angle else None)


def b_grass(m):
    tuft(m, GRASS, ((8, 7, 0, 1), (6.5, 5.5, 22.5, 1), (9.5, 6, -22.5, 1), (7, 4, 45, 0.9), (9, 4.5, -45, 0.9),
                    (8.6, 5, 22.5, 0.8)))


def b_tall_grass(m):
    tuft(m, GRASS, ((8, 13, 0, 1.2), (6.5, 10, 22.5, 1), (9.5, 11, -22.5, 1), (7, 7, 45, 1), (9, 7.5, -45, 1),
                    (8.4, 9, 22.5, 0.9)))


def b_fern(m, scale=1.0):
    mat = Mat(GRASS, base=2.8, bevel=0.3)
    for (a, ln, z) in ((0, 8, 7.6), (22.5, 7, 7.2), (-22.5, 7, 8.0), (45, 5, 7.4), (-45, 5, 7.8)):
        frond(m, mat, 8, 0, ln * scale, a, z)


def b_dead_bush(m):
    twig = Mat(DRY, base=2.6, bevel=0.3)
    for parts, z in ((((4, 0), (3, 22.5), (2.5, 45)), 7.6), (((3, 0), (3.5, -22.5), (2, -45)), 7.9),
                     (((5, 22.5), (2.5, -22.5)), 7.3), (((4, -45), (2, 0)), 8.1)):
        bent(m, twig, 8, 0, parts, z, 0.6, 0.5)


def b_seagrass(m):
    mat = Mat(SEA, base=3.0, bevel=0.3)
    for parts, x, z in ((((4, 0), (4, 22.5), (3, 0)), 8, 7.6), (((3, -22.5), (4, 0), (3, -22.5)), 8.6, 7.9),
                        (((5, 22.5), (3, 0)), 7.4, 7.3)):
        bent(m, mat, x, 0, parts, z, 1.0, 0.4)


def b_kelp(m):
    stalk = Mat(KELP, base=2.8, bevel=0.3)
    x, y = bent(m, stalk, 8, 0, ((5, 0), (5, 22.5), (5, -22.5)), 7.6, 1.0, 0.8)
    bulb = Mat(["4a5a14", "6a7a1e", "8a9a2a", "a8b63c", "c4d060"], base=2.6, bevel=0.4)
    for (bx, by) in ((8.5, 5), (6.7, 9.6), (8.2, 13.6)):             # air bladders on short stalks
        m.box((bx - 0.7, by - 0.7, 7.4), (bx + 0.7, by + 0.7, 8.6), bulb, ao=False)
    leaf = Mat(KELP, base=3.4, bevel=0.3)
    for (lx, ly, a) in ((8, 3, -45), (7.4, 8, 45), (7.8, 12, -45), (x, y, 22.5)):
        blade(m, leaf, lx, ly, 3, a, 1.4, 7.7, 0.4)


def b_bamboo(m):
    stalk = Mat(BAMBOO, base=3.0, bevel=0.5)
    m.box((7.2, 0, 7.2), (8.8, 16, 8.8), stalk, decal=stripes(4, -1.6))
    for y in (4, 8, 12):
        m.box((7.0, y - 0.4, 7.0), (9.0, y, 9.0), Mat(BAMBOO, base=1.8, bevel=0.3), ao=False)   # its joints
    leaf = Mat(LEAF, base=3.0, bevel=0.4)
    for (y, a, z) in ((12.4, 45, 7.6), (12.8, -45, 8.0), (15, 22.5, 7.4), (15.4, -22.5, 8.2)):
        blade(m, leaf, 8, y, 4, a, 1.4, z, 0.4)


def b_lily_pad(m):
    pad = Mat(["123a10", "1a5016", "24681e", "308228", "3e9c34", "58b448"], base=3.0, bevel=0.4)
    for (z0, z1, hw) in circle_rows(6, 8):                              # a round pad lying flat, a notch cut in
        if z1 > 8 and hw > 1:
            m.box((8 - hw, 0, z0), (7.4, 0.8, z1), pad, decal=stripes(3, 0.7, axis="v", faces=("up",)), ao=False)
            m.box((8.6, 0, z0), (8 + hw, 0.8, z1), pad, decal=stripes(3, 0.7, axis="v", faces=("up",)), ao=False)
        else:
            m.box((8 - hw, 0, z0), (8 + hw, 0.8, z1), pad, decal=stripes(3, 0.7, axis="v", faces=("up",)), ao=False)
    m.write(upright(scale=0.45, lift=6.0, tilt=40))


def hanging(m, pal, strands, leaf_pal=None, bud_pal=None, top=15):
    """strands hanging (or climbing) with leaves or buds along them"""
    s = Mat(pal, base=3.0, bevel=0.3)
    for (x, z, parts) in strands:
        y = top
        for (length, angle) in parts:
            m.box((x - 0.4, y - length, z), (x + 0.4, y, z + 0.6), s, ao=False,
                  rot=(angle, "z", (x, y, z + 0.3)) if angle else None)
            y -= length
        if leaf_pal:
            for k in range(3):
                ly = top - 2 - k * 3.5
                m.box((x - 1.2 + (k % 2) * 1.2, ly - 1.0, z - 0.2), (x + (k % 2) * 1.2, ly, z + 0.8),
                      Mat(leaf_pal, base=3.0, bevel=0.4), ao=False)
        if bud_pal:
            m.box((x - 0.8, y - 1.4, z - 0.3), (x + 0.8, y, z + 0.9), Mat(bud_pal, base=3.6, bevel=0.4), ao=False)


def b_vine(m):
    hanging(m, ["1a3a10", "26521a", "326a22", "40822c"], ((6, 7.4, ((14, 0),)), (8.6, 7.8, ((11, 0),)),
                                                         (10.6, 7.2, ((8, 0),))), LEAF)
    m.box((4.5, 14.6, 7.0), (12.0, 15.4, 8.4), Mat(["1a3a10", "26521a", "326a22", "40822c"], base=2.4, bevel=0.3))


def b_glow_lichen(m):
    base = Mat(["2a3a34", "3e5048", "52665c", "687e72"], base=2.0, bevel=0.3)
    m.box((3, 2, 7.8), (13, 14, 8.4), base, decal=spots(0.2, 0.8, seed="lichen"))     # a patch of stone
    glow = Mat(["2a6a5a", "3e8e78", "5ab49a", "84d4b8", "b8f0dc", "e8fff4"], base=3.4, bevel=0.3, glow=True,
               shade=False)
    for (x, y, s) in ((5, 4, 1.6), (8.5, 5, 1.2), (6.5, 8.5, 1.8), (10.5, 9, 1.4), (5, 12, 1.2), (9, 12.4, 1.6),
                      (11, 4.4, 1.0)):
        m.box((x - s / 2, y - s / 2, 8.4), (x + s / 2, y + s / 2, 8.8), glow, ao=False)


def b_hanging_roots(m):
    hanging(m, ["4a3424", "6a4c36", "8a664a", "a8805e"], ((6.4, 7.6, ((6, 0), (4, 22.5))), (8.2, 8.0, ((9, 0),)),
                                                          (9.8, 7.4, ((5, 0), (3, -22.5)))))
    m.box((4.5, 14.6, 6.8), (11.5, 15.6, 9.0), Mat(["3a2a1c", "56402c", "6e5238", "8a6a4a"], base=2.2, bevel=0.4))


GRASSES = {"grass": b_grass, "tall_grass": b_tall_grass, "fern": b_fern, "large_fern": lambda m: b_fern(m, 1.6),
           "dead_bush": b_dead_bush, "seagrass": b_seagrass, "kelp": b_kelp, "bamboo": b_bamboo,
           "vine": b_vine, "glow_lichen": b_glow_lichen, "hanging_roots": b_hanging_roots}


# ---------------------------------------------------------------- mushrooms and the nether
def mushroom(m, cap_pal, stem_pal, spot_pal=None, flat=False, cap_r=3.6):
    st = Mat(stem_pal, base=3.0, bevel=0.5)
    m.box((7, 0, 7), (9, 6, 9), st)
    m.box((6.6, 0, 6.6), (9.4, 1, 9.4), st)
    cap = Mat(cap_pal, base=3.0, bevel=0.6)
    if flat:
        m.box((8 - cap_r, 5.5, 8 - cap_r), (8 + cap_r, 7.0, 8 + cap_r), cap, decal=shine)
        m.box((8 - cap_r + 1, 7.0, 8 - cap_r + 1), (8 + cap_r - 1, 7.8, 8 + cap_r - 1), cap)
    else:
        blob(m, (8 - cap_r, 5.5, 8 - cap_r), (8 + cap_r, 10.5, 8 + cap_r), cap, s=0.8, decal=shine)
    if spot_pal:
        sp = Mat(spot_pal, base=len(spot_pal) - 2, bevel=0.3)
        top = 7.8 if flat else 10.5
        for (x, z, s) in ((6.8, 7.0, 0.8), (9.2, 8.8, 0.8), (7.6, 9.4, 0.7), (9.4, 6.8, 0.7)):
            m.box((x - s / 2, top - 0.1, z - s / 2), (x + s / 2, top + 0.2, z + s / 2), sp, ao=False)
        m.box((7.6, 7.6, 8 + cap_r - 0.1), (8.8, 8.8, 8 + cap_r + 0.15), sp, ao=False)
        m.box((5.8, 8.6, 8 + cap_r - 0.9), (6.8, 9.6, 8 + cap_r - 0.75 + 0.15), sp, ao=False)


def b_red_mushroom(m):
    mushroom(m, RED_CAP, SHROOM_STEM, ["c8c0b0", "e8e2d4", "fbf8f0"])


def b_brown_mushroom(m):
    mushroom(m, BROWN_CAP, SHROOM_STEM, flat=True, cap_r=4.0)


def b_crimson_fungus(m):
    mushroom(m, CRIMSON, NETHER_STEM, ORANGE_SPOT)


def b_warped_fungus(m):
    mushroom(m, WARPED, NETHER_STEM, ORANGE_SPOT)


def roots(m, pal, tip_pal=None):
    mat = Mat(pal, base=3.0, bevel=0.3)
    for parts, x, z in ((((4, 0), (3, 22.5)), 8, 7.6), (((3, 22.5), (3, 45)), 7.6, 7.9),
                        (((3.5, -22.5), (3, -45)), 8.4, 7.3), (((5, 0), (2, -22.5)), 8.8, 8.2)):
        tx, ty = bent(m, mat, x, 0, parts, z, 0.7, 0.5)
        if tip_pal:
            m.box((tx - 0.6, ty - 0.3, z - 0.1), (tx + 0.6, ty + 0.9, z + 0.6), Mat(tip_pal, base=3.4, bevel=0.3),
                  ao=False)


def b_nether_wart(m):
    stalk = Mat(WART, base=2.2, bevel=0.3)
    nub = Mat(WART, base=3.2, bevel=0.6)
    for (x, z, h) in ((6, 7, 4), (9.6, 7.6, 5.5), (7.8, 9.8, 3.4)):
        m.box((x - 0.5, 0, z - 0.5), (x + 0.5, h, z + 0.5), stalk, ao=False)
        m.box((x - 1.4, h - 0.4, z - 1.4), (x + 1.4, h + 1.8, z + 1.4), nub, decal=shine)
        m.box((x - 0.9, h + 1.8, z - 0.9), (x + 0.9, h + 2.4, z + 0.9), nub)


NETHER = {
    "red_mushroom": b_red_mushroom, "brown_mushroom": b_brown_mushroom, "crimson_fungus": b_crimson_fungus,
    "warped_fungus": b_warped_fungus, "crimson_roots": lambda m: roots(m, CRIMSON, ORANGE_SPOT),
    "warped_roots": lambda m: roots(m, WARPED, ["0a4a54", "147a80", "22a8a8", "4cd0c8", "90f0e0"]),
    "nether_sprouts": lambda m: tuft(m, WARPED, ((8, 4, 0, 0.8), (6.8, 3, 22.5, 0.8), (9.2, 3.4, -22.5, 0.8),
                                                 (7.4, 2.4, 45, 0.7), (8.8, 2.6, -45, 0.7))),
    "weeping_vines": lambda m: hanging(m, CRIMSON, ((6.6, 7.6, ((6, 0), (5, 22.5))), (8.6, 7.9, ((10, 0),)),
                                                    (10.0, 7.4, ((4, 0), (4, -22.5)))), bud_pal=CRIMSON),
    "twisting_vines": lambda m: [bent(m, Mat(WARPED, base=3.0, bevel=0.3), x, 0, parts, z, 0.8, 0.6)
                                 for (x, z, parts) in ((7, 7.6, ((5, 22.5), (5, -22.5), (3, 0))),
                                                       (9, 7.9, ((6, -22.5), (4, 22.5))))],
    "nether_wart": b_nether_wart,
}


# ---------------------------------------------------------------- corals
CORALS = {"tube": "3050d8", "brain": "e060a0", "bubble": "a030c8", "fire": "d02a2a", "horn": "e8d040"}
DEAD = ["4a4642", "66605a", "807a72", "9a948a", "b4aea4", "ccc6bc"]


def coral(kind, pal):
    def b(m):
        mat = Mat(pal, base=3.0, bevel=0.5)
        tip = Mat(pal, base=4.4, bevel=0.3)
        if kind == "tube":                                         # tubes standing up, open at the top
            for (x, z, h) in ((6, 7, 7), (8.4, 8.6, 9), (10, 6.8, 6), (7.4, 10, 5)):
                m.box((x - 0.9, 0, z - 0.9), (x + 0.9, h, z + 0.9), mat)
                m.box((x - 1.1, h, z - 1.1), (x + 1.1, h + 0.6, z + 1.1), tip, ao=False)
        elif kind == "brain":                                      # a rounded mound with winding grooves
            blob(m, (3, 0, 4), (13, 7, 12), mat, s=0.9, decal=stripes(2, -1.2, axis="v"))
        elif kind == "bubble":                                     # a cluster of bubbles on stalks
            for (x, y, z, r) in ((6, 6, 8, 1.6), (9.6, 7.6, 7.6, 1.8), (8, 10, 8.4, 1.5), (10.4, 4, 9.6, 1.2)):
                m.box((x - 0.4, 0, z - 0.4), (x + 0.4, y, z + 0.4), mat, ao=False)
                pompom(m, pal, x, y, z, r, 0.15)
        else:                                                      # fire / horn: branching antlers
            for parts, x, z in ((((4, 0), (3, 22.5), (2.5, 45)), 8, 7.6), (((4, 0), (3, -22.5), (2.5, -45)), 8.2, 7.9),
                                (((3, 22.5), (3, 0)), 7.4, 8.4), (((3, -22.5), (3, 0)), 8.8, 7.2),
                                (((6, 0), (2, 22.5)), 8, 8.1)):
                tx, ty = bent(m, mat, x, 0, parts, z, 1.2 if kind == "horn" else 0.8, 0.8)
                m.box((tx - 0.6, ty - 0.2, z - 0.1), (tx + 0.6, ty + 0.6, z + 0.9), tip, ao=False)
    return b


def coral_fan(pal):
    def b(m):
        mat = Mat(pal, base=3.0, bevel=0.3)
        rib = Mat(pal, base=4.2, bevel=0.2)
        for (y0, y1, hw) in circle_rows(6, 2):                     # a half disc, fanned out above its foot
            if y0 >= 2:
                m.box((8 - hw, y0, 7.6), (8 + hw, y1, 8.2), mat, decal=stripes(2, -0.8, axis="v"), ao=False)
        for a in (0, 22.5, -22.5, 45, -45):                         # the ribs spreading from the foot
            blade(m, rib, 8, 1, 6.5, a, 0.6, 8.15, 0.25)
        m.box((7.2, 0, 7.4), (8.8, 2.2, 8.4), mat)
    return b


CORAL_ITEMS = {}
for _k, _c in CORALS.items():
    CORAL_ITEMS[f"{_k}_coral"] = coral(_k, ramp(_c))
    CORAL_ITEMS[f"dead_{_k}_coral"] = coral(_k, DEAD)
    CORAL_ITEMS[f"{_k}_coral_fan"] = coral_fan(ramp(_c))
    CORAL_ITEMS[f"dead_{_k}_coral_fan"] = coral_fan(DEAD)


# ---------------------------------------------------------------- seeds
def seeds(name, pal, n=8, size=(0.9, 0.35, 0.6)):
    """a little heap of seeds, each a rounded oval (a long box crossed with a shorter, wider one)"""
    def make():
        m = Model(name)
        mat = Mat(pal, base=2.8, bevel=0.4)
        sx, sy, sz = size
        for i in range(n):
            a = i * 2.4                                  # spread round in a little heap, none in the same plane
            x, z = 8 + (0.8 + 0.42 * i) * np.cos(a), 8 + (0.8 + 0.42 * i) * np.sin(a)
            y = 0.05 * i + (0.7 if i == n - 1 else 0)
            rot = ((-45, -22.5, 0, 22.5, 45)[i % 5], "y", (x, y, z))
            m.box((x - sx, y, z - sz * 0.6), (x + sx, y + sy * 2, z + sz * 0.6), mat, rot=rot, decal=shine)
            m.box((x - sx * 0.65, y + 0.02, z - sz), (x + sx * 0.65, y + sy * 2 - 0.02, z + sz), mat, rot=rot)
        m.write(upright(**SEEDS))
    return make


def cocoa_beans():
    m = Model("cocoa_beans")
    rnd = random.Random("cocoa")
    bean = Mat(COCOA, base=3.0, bevel=0.6)
    for i, (x, z, a) in enumerate(((6.4, 7.0, 22.5), (9.6, 7.6, -22.5), (8.0, 10.0, 45))):
        y = 0
        m.box((x - 1.6, y, z - 1.1), (x + 1.6, y + 2.2, z + 1.1), bean, rot=(a, "y", (x, y, z)),
              decal=lambda k, ii, jj, w, h, face: np.where((face == "up") & (jj == h // 2), 0.6, k))   # its seam
        m.box((x - 1.2, y + 2.2, z - 0.7), (x + 1.2, y + 2.6, z + 0.7), bean, rot=(a, "y", (x, y, z)))
    m.write(upright(**SEEDS))


def pitcher_pod():
    m = Model("pitcher_pod")
    pod = Mat(["2a3a3a", "3e5652", "56726a", "6e8e84", "8aaa9e", "aac8bc"], base=3.0, bevel=0.6)
    m.box((6.5, 0, 6.5), (9.5, 7, 9.5), pod, decal=stripes(2, -0.9, axis="v"))
    m.box((7, 7, 7), (9, 9, 9), pod)
    m.box((7.6, 9, 7.6), (8.4, 10.5, 8.4), Mat(PITCHER, base=3.2, bevel=0.3))
    m.box((7, -0.6, 7), (9, 0, 9), Mat(STEM, base=2.4, bevel=0.3))
    m.write(upright(**dict(SEEDS, tilt=10, lift=6.5)))


SEED_ITEMS = {n: seeds(n, p) for n, p in SEED_PALS.items()}
SEED_ITEMS["melon_seeds"] = seeds("melon_seeds", SEED_PALS["melon_seeds"], size=(1.0, 0.3, 0.7))
SEED_ITEMS["pumpkin_seeds"] = seeds("pumpkin_seeds", SEED_PALS["pumpkin_seeds"], n=7, size=(1.2, 0.3, 0.8))
SEED_ITEMS["cocoa_beans"] = cocoa_beans
SEED_ITEMS["pitcher_pod"] = pitcher_pod


# ---------------------------------------------------------------- all of them
def simple(name, build, held=FLOWER):
    def make():
        m = Model(name)
        build(m)
        m.write(upright(**held), unlit=name == "glow_lichen")
    return make


PLANTS = {}
for _n, _b in FLOWERS.items():
    PLANTS[_n] = simple(_n, _b)
for _n, _b in TALL_FLOWERS.items():
    PLANTS[_n] = simple(_n, _b, TALL)
PLANTS.update(SAPLINGS)
for _n, _b in GRASSES.items():
    PLANTS[_n] = simple(_n, _b, TALL if _n in ("tall_grass", "large_fern", "kelp", "bamboo") else FLOWER)
PLANTS["lily_pad"] = lambda: b_lily_pad(Model("lily_pad"))
for _n, _b in NETHER.items():
    PLANTS[_n] = simple(_n, _b)
for _n, _b in CORAL_ITEMS.items():
    PLANTS[_n] = simple(_n, _b)
PLANTS.update(SEED_ITEMS)
