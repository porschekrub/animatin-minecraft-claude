#!/usr/bin/env python3
"""Batch 4 of Lifelike Motion's 3D items: gems and materials (built with tools/models.py's parts and painter; run
tools/models.py to write them). Gems, metals and magic things are made to look cool (cut facets, glints, a glow);
the rest (clay, sugar, dusts) to look clean and pretty."""
import numpy as np

from models import Mat, Model, upright, DIAMOND, GOLD, IRON, NETHERITE, EMBER
from models_food import blob, spots, shine, chain

EMERALD = ["063d1a", "0b5e27", "128a38", "1cb44c", "3ee070", "96f8b4", "e6fff0"]
LAPIS = ["0e1a4a", "1a2c78", "2642a8", "3a5ccc", "5a80e6", "9ab4f6"]
AMETHYST = ["2c1048", "45207a", "6634a8", "8a52cc", "b07ee6", "d8b4f6", "f6ecff"]
QUARTZ = ["8a8078", "b4aca4", "d6d0c8", "ece8e2", "f8f6f2", "ffffff"]
ECHO = ["041a1e", "08303a", "0e4a58", "13707e", "1fa0a8", "5ad8d0", "c0fff6"]
PRISMARINE = ["1a4a44", "28685e", "3a8a7a", "56aa96", "82c8b4", "b8e4d6"]
PRISM_CRYSTAL = ["4a7a6a", "7aa898", "a8d4c0", "d4f0e4", "f2fff8", "ffffff"]
COAL = ["0a0a0c", "141416", "1e1e22", "2a2a30", "3c3c44", "6a6a78", "b0b0c0"]
CHARCOAL = ["120c08", "1e140c", "2c1e12", "3c2a1a", "523a24", "6e5030", "8e6a44"]
FLINT = ["101012", "1c1c20", "2c2c32", "40404a", "5c5c68", "8a8a98"]
CLAY = ["6a7484", "8a94a4", "a8b2c0", "c4ccd8", "dce2ea", "f0f4f8"]
RAW_IRON = ["4a3a30", "6e5848", "968070", "b8a492", "d8c8b8", "f0e6da"]
RAW_GOLD = ["6a4404", "9a6608", "c89010", "e8b424", "f8d65a", "fff0a8"]
COPPER = ["5a2a14", "8a4220", "b4602e", "d88044", "eca068", "fac898"]
REDSTONE = ["3a0202", "6a0606", "9a0a0a", "d01414", "ff3a2a", "ff8a6a"]
GLOWSTONE = ["7a5010", "b07a18", "e0a828", "fcd048", "ffe888", "fffad8"]
GUNPOWDER = ["2a2a2a", "404040", "585858", "747474", "929292", "b4b4b4"]
SUGAR = ["b8b8c0", "d4d4dc", "e8e8ee", "f6f6fa", "ffffff"]
BLAZE = ["7a2a02", "b04a06", "e07810", "fca62a", "ffd060", "fff2b0"]
BONE_MEAL = ["a8a498", "c8c4b8", "e0dcd2", "f2f0ea", "ffffff"]
PEARL = ["041e1c", "08302c", "0e4a44", "166a60", "28968a", "62c8b8", "b8f2e8"]
EYE_GREEN = ["0e2a10", "1a4a1c", "2a6e2a", "44963c", "6cbe56", "a8e888", "e0ffd0"]
HEART = ["06204a", "0c3a7a", "1658b0", "2a7ee0", "58aaf6", "a8dcff", "eaf8ff"]
STAR = ["8a8aa8", "b8b8d0", "dcdcec", "f2f2fa", "ffffff"]
BLAZE_ROD = ["8a4a04", "c07008", "f0a018", "fcc840", "ffe680", "fff8d0"]
BRICK = ["4a1a10", "6e2818", "963a22", "b44e2e", "cc6a44", "e08c64"]
NETHER_BRICK = ["160608", "240a0e", "34101a", "4a1824", "602430", "7a3440"]
SLIME = ["2a5a1a", "3e7e26", "58a436", "7ccc4e", "a8e878", "d8ffb0"]
MAGMA = ["1a0602", "3a0e04", "6a1a06", "b03a0a", "f07018", "ffb040", "ffe8a0"]

SMALL = dict(scale=0.42, lift=7.0)           # small things, held up close
LYING = dict(scale=0.4, lift=7.5, tilt=32)   # flat things lying down, tipped toward you


def glints(density=0.06, seed=0):
    """single bright pixels: light catching facets or crystals"""
    return spots(density, 99, seed=seed)


# ---------------------------------------------------------------- gems and crystals
def diamond():
    """a brilliant-cut diamond standing on its point: the pavilion narrowing down, the wide girdle, the crown and the
    table, with octagonal layers (each one twice, turned 45 degrees) and glints"""
    m = Model("diamond")
    g = Mat(DIAMOND, base=4.0, kind="gem", bevel=0.9, glow=True)
    hi = Mat(DIAMOND, base=5.2, kind="gem", bevel=0.9, glow=True)
    gl = None
    sides = ("north", "south", "east", "west")
    for (a, b, y0, y1, mat, faces) in ((7.25, 8.75, 0, 1.5, g, sides + ("down",)),
                                       (6.25, 9.75, 1.5, 3, g, sides + ("down",)),
                                       (5.25, 10.75, 3, 4.5, g, sides + ("down",)),
                                       (4, 12, 4.5, 6, g, None),
                                       (4.75, 11.25, 6, 7.5, hi, sides + ("up",)),
                                       (5.75, 10.25, 7.5, 8.5, hi, sides + ("up",))):
        # (only the faces that show: the pavilion widens upward, the crown narrows, so no two faces lie together)
        m.box((a, y0, a), (b, y1, b), mat, decal=gl, ao=False, faces=faces)
    m.box((6.25, 8.5, 6.25), (7.25, 8.75, 7.25), Mat(["ffffff", "ffffff"], base=1, bevel=0, glow=True),
          faces=("up", "south", "west"), ao=False)                         # a sparkle on the crown
    m.write(upright(**SMALL))


def emerald():
    """an emerald-cut gem standing up: a tall stepped octagon with a raised table on each face"""
    m = Model("emerald")
    g = Mat(EMERALD, base=3.8, kind="gem", bevel=0.6, glow=True)
    t = Mat(EMERALD, base=4.8, kind="gem", bevel=0.5, glow=True)
    gl = glints(0.06, "em")
    m.box((6, 0, 7), (10, 13, 9), g, decal=gl)
    m.box((5, 1, 7), (11, 12, 9), g, decal=gl)
    m.box((5.5, 0.5, 6.5), (10.5, 12.5, 9.5), g, decal=gl)
    m.box((6.5, 2, 6), (9.5, 11, 10), t, decal=gl)                         # the table, front and back
    m.write(upright(**SMALL))


def lapis_lazuli():
    """a rough lump of lapis, flecked with gold"""
    m = Model("lapis_lazuli")
    stone = Mat(LAPIS, base=3.0, kind="organic", grad=0.8)
    fleck = spots(0.07, 99, seed="lapis")
    blob(m, (3.5, 0, 4.5), (12, 7, 11.5), stone, decal=chain(fleck, shine))
    m.box((9, 5, 7), (12.5, 9, 9), stone, decal=fleck)
    gold = Mat(GOLD, base=4, kind="metal", bevel=0.3)
    for (x, y, z) in ((5, 4.5, 11.5), (8.5, 3, 11.5)):
        m.box((x, y, z), (x + 1, y + 1, z + 0.15), gold, faces=("south",), ao=False)
    m.write(upright(**SMALL))


def crystal_cluster(name, pal, glow=False, small=False):
    """crystal points growing from a little base: a tall one in the middle, two leaning out"""
    m = Model(name)
    c = Mat(pal, base=len(pal) / 2 + 0.3, kind="gem", bevel=0.5, glow=glow)
    tip = Mat(pal, base=len(pal) - 1.6, kind="gem", bevel=0.3, glow=glow)
    base = Mat(pal, base=1.6, kind="organic", bevel=0.4)
    gl = glints(0.06, name)
    k = 0.7 if small else 1.0
    m.box((5, 0, 5.5), (11, 1.5, 10.5), base)
    m.box((7, 1, 7), (9, 1 + 9 * k, 9), c, decal=gl)                       # middle
    m.box((7.5, 1 + 9 * k, 7.5), (8.5, 3 + 9 * k, 8.5), tip)
    m.box((4.5, 1, 7.25), (6.5, 1 + 6.5 * k, 8.75), c, rot=(22.5, "z", (5.5, 1, 8)), decal=gl)   # leaning left
    m.box((5, 1 + 6.5 * k, 7.6), (6, 2.5 + 6.5 * k, 8.4), tip, rot=(22.5, "z", (5.5, 1, 8)))
    m.box((9.5, 1, 7.25), (11.5, 1 + 5.5 * k, 8.75), c, rot=(-22.5, "z", (10.5, 1, 8)), decal=gl)  # leaning right
    m.box((10, 1 + 5.5 * k, 7.6), (11, 2.5 + 5.5 * k, 8.4), tip, rot=(-22.5, "z", (10.5, 1, 8)))
    m.box((7.25, 1, 9.5), (8.75, 1 + 4 * k, 11), c, rot=(-22.5, "x", (8, 1, 10)))                # one leaning out
    m.write(upright(**SMALL))


def amethyst_shard():
    crystal_cluster("amethyst_shard", AMETHYST, glow=True)


def quartz():
    crystal_cluster("quartz", QUARTZ)


def prismarine_crystals():
    crystal_cluster("prismarine_crystals", PRISM_CRYSTAL, glow=True, small=True)


def echo_shard():
    """a jagged shard of the deep dark, glowing faintly from inside"""
    m = Model("echo_shard")
    s = Mat(ECHO, base=3.4, kind="gem", bevel=0.5, glow=True)
    core = Mat(ECHO, base=5.4, kind="gem", bevel=0.2, glow=True)
    m.box((6.5, 0, 7.25), (9, 4, 8.75), s)
    m.box((7, 4, 7.25), (10, 8, 8.75), s)
    m.box((6, 8, 7.25), (9, 12, 8.75), s)
    m.box((7, 12, 7.5), (8.5, 15, 8.5), s)
    m.box((7.5, 3, 7), (8.5, 12, 9), core, ao=False)                       # the glowing seam through it
    m.write(upright(**SMALL))


def prismarine_shard():
    """two sharp sea-green shards"""
    m = Model("prismarine_shard")
    s = Mat(PRISMARINE, base=3.2, kind="gem", bevel=0.6)
    m.box((5, 0, 7.25), (8, 9, 8.75), s, rot=(22.5, "z", (6.5, 0, 8)))
    m.box((5.75, 9, 7.5), (7.25, 12, 8.5), s, rot=(22.5, "z", (6.5, 0, 8)))
    m.box((8.5, 0, 7.4), (11, 7, 8.6), s, rot=(-22.5, "z", (9.75, 0, 8)))
    m.box((9.25, 7, 7.6), (10.25, 9.5, 8.4), s, rot=(-22.5, "z", (9.75, 0, 8)))
    m.write(upright(**SMALL))


# ---------------------------------------------------------------- rocks and lumps
def lump(name, pal, base=3.0, decal=None, extra=None, kind="organic"):
    m = Model(name)
    r = Mat(pal, base=base, kind=kind, grad=0.8)
    d = chain(decal, shine) if decal else shine
    blob(m, (3.5, 0, 4.5), (11.5, 7.5, 11.5), r, decal=d)
    m.box((10, 1, 6.5), (13, 5, 9.5), r, decal=decal)                      # smaller lumps stuck on
    m.box((5, 6.5, 7), (8.5, 9, 9), r, decal=decal)
    if extra:
        extra(m)
    m.write(upright(**SMALL))


def coal():
    lump("coal", COAL, base=2.4, decal=glints(0.05, "coal"))


def flint():
    """a knapped flint shard: chipped faces, sharp edges"""
    m = Model("flint")
    f = Mat(FLINT, base=2.8, kind="gem", bevel=0.8)
    chips = spots(0.12, 4.5, seed="flint")
    m.box((5, 0, 7.25), (11, 3, 8.75), f, decal=chips)
    m.box((5.5, 3, 7.25), (10.5, 7, 8.75), f, decal=chips)
    m.box((6.5, 7, 7.4), (9.5, 10, 8.6), f, decal=chips)
    m.box((7.25, 10, 7.6), (8.75, 12, 8.4), f)
    m.write(upright(**SMALL))


def clay_ball():
    m = Model("clay_ball")
    c = Mat(CLAY, base=2.2, kind="organic", grad=1.0)
    blob(m, (4, 1, 4), (12, 9, 12), c, decal=chain(spots(0.04, -1, seed="clay", add=True), shine))
    m.write(upright(**SMALL))


def charcoal():
    """a burnt chunk of log: growth rings on the end, cracked black bark"""
    m = Model("charcoal")
    c = Mat(CHARCOAL, base=2.6, kind="wood", bevel=0.6)

    def rings(k, ii, jj, w, h, face):
        if face in ("east", "west"):
            r = np.hypot(ii - (w - 1) / 2, jj - (h - 1) / 2)
            k = np.where(np.round(r) % 2 == 0, k + 1.4, k - 0.4)
        return k

    m.box((3, 1, 5), (13, 7, 11), c, decal=rings)
    m.box((3.5, 0.5, 5.5), (12.5, 7.5, 10.5), c, decal=rings)
    m.box((4, 7, 6), (7, 8, 9), c), m.box((9, 0, 7), (12, 1, 10), c)       # cracked bits
    m.write(upright(**LYING))


def raw_ore(name, pal):
    def ext(m):
        return None
    lump(name, pal, base=3.0, decal=glints(0.07, name), extra=ext, kind="metal")


def raw_iron():
    raw_ore("raw_iron", RAW_IRON)


def raw_gold():
    raw_ore("raw_gold", RAW_GOLD)


def raw_copper():
    raw_ore("raw_copper", COPPER)


def netherite_scrap():
    """a scrappy chunk of ancient debris metal, embers still glowing in the cracks"""
    m = Model("netherite_scrap")
    s = Mat(NETHERITE, base=3.2, kind="metal", bevel=0.8)
    ember = Mat(EMBER, base=3.6, bevel=0.2, glow=True)
    m.box((3.5, 0, 5), (12, 5, 11), s, decal=glints(0.05, "scrap"))
    m.box((4.5, 5, 6), (10, 8, 10), s)
    m.box((10, 2, 6.5), (13, 6, 9.5), s)
    for (a, b) in (((6, 2, 11), (9, 2.5, 11.1)), ((8.5, 6, 10), (9.5, 7.5, 10.1)), ((12.5, 3, 8), (13.1, 4.5, 9))):
        m.box(a, b, ember, ao=False)
    m.write(upright(**SMALL))


# ---------------------------------------------------------------- metals
def ingot(name, pal, base, mark=True):
    """a cast ingot bar: wider at the bottom, bevelled, a maker's mark stamped on top"""
    m = Model(name)
    met = Mat(pal, base=base, kind="metal", bevel=0.9)
    top = Mat(pal, base=base + 0.6, kind="metal", bevel=0.9)

    def stamp(k, ii, jj, w, h, face):
        if face == "up" and mark and w > 6:
            cx, cy = (w - 1) / 2, (h - 1) / 2
            box = (np.abs(ii - cx) <= 2) & (np.abs(jj - cy) <= 1)
            edge = box & ((np.abs(ii - cx) > 1) | (np.abs(jj - cy) > 0))
            k = np.where(edge, k - 1.6, k)
        return k

    m.box((2.5, 0, 5), (13.5, 1.5, 11), met)
    m.box((3, 1.5, 5.5), (13, 3, 10.5), met)
    m.box((3.5, 3, 6), (12.5, 4, 10), top, decal=stamp)
    m.write(upright(**LYING))


def iron_ingot():
    ingot("iron_ingot", IRON, 3.6)


def gold_ingot():
    ingot("gold_ingot", GOLD, 2.8)


def copper_ingot():
    ingot("copper_ingot", COPPER, 2.8)


def netherite_ingot():
    ingot("netherite_ingot", NETHERITE, 3.6)


def nuggets(name, pal, base):
    m = Model(name)
    n = Mat(pal, base=base, kind="metal", bevel=0.7)
    for (x, y, z, s) in ((4.5, 0, 6.5, 3), (8, 0, 5.5, 3.5), (6.5, 2.5, 7, 2.5)):
        m.box((x, y, z), (x + s, y + s * 0.8, z + s), n, decal=glints(0.08, name + str(x)))
    m.write(upright(**SMALL))


def iron_nugget():
    nuggets("iron_nugget", IRON, 3.6)


def gold_nugget():
    nuggets("gold_nugget", GOLD, 3.0)


# ---------------------------------------------------------------- dusts
def pile(name, pal, glow=False, specks=None):
    """a little heap of dust, a few grains spilled round it"""
    m = Model(name)
    d = Mat(pal, base=len(pal) / 2, kind="organic", bevel=0.4, glow=glow)
    dec = specks or glints(0.07, name)
    m.box((3, 0, 3.5), (13, 1.5, 12.5), d, decal=dec)
    m.box((4.5, 1.5, 4.5), (11.5, 3, 11.5), d, decal=dec)
    m.box((6, 3, 6), (10, 4.5, 10), d, decal=dec)
    m.box((7, 4.5, 7), (9, 5.5, 9), d, decal=dec)
    for (x, z) in ((1.5, 6), (13.5, 9), (9, 13), (5, 1.5)):
        m.box((x, 0, z), (x + 1, 0.75, z + 1), d)
    m.write(upright(**LYING))


def redstone():
    pile("redstone", REDSTONE, glow=True)


def glowstone_dust():
    pile("glowstone_dust", GLOWSTONE, glow=True)


def gunpowder():
    pile("gunpowder", GUNPOWDER, specks=spots(0.12, 0, seed="gp"))


def sugar():
    pile("sugar", SUGAR)


def blaze_powder():
    pile("blaze_powder", BLAZE, glow=True)


def bone_meal():
    pile("bone_meal", BONE_MEAL)


# ---------------------------------------------------------------- magic things
def swirl(k, ii, jj, w, h, face):
    return np.where(((ii * 2 + jj) % 6 < 2), k + 1.4, k)


def ender_pearl():
    m = Model("ender_pearl")
    p = Mat(PEARL, base=3.2, kind="gem", bevel=0.5, glow=True)
    blob(m, (4, 2, 4), (12, 10, 12), p, decal=chain(swirl, shine))
    m.write(upright(**SMALL))


def ender_eye():
    m = Model("ender_eye")
    e = Mat(EYE_GREEN, base=3.2, kind="gem", bevel=0.5, glow=True)

    def eye(k, ii, jj, w, h, face):
        if face in ("north", "south") and w >= 5:
            cx, cy = (w - 1) / 2, (h - 1) / 2
            r = np.hypot(ii - cx, jj - cy)
            k = np.where(r < 2.6, k + 1.6, k)                            # the iris
            k = np.where((np.abs(ii - cx) < 0.6) & (r < 2.6), -9, k)      # the slit pupil
        return k

    blob(m, (4, 2, 4), (12, 10, 12), e, decal=chain(eye, shine))
    m.write(upright(**SMALL))


def heart_of_the_sea():
    """a glowing blue heart held in a cage of dark prismarine"""
    m = Model("heart_of_the_sea")
    core = Mat(HEART, base=4.0, kind="gem", bevel=0.4, glow=True)
    cage = Mat(PRISMARINE, base=1.4, kind="metal", bevel=0.6)
    blob(m, (5, 3, 5), (11, 9, 11), core, decal=chain(swirl, shine))
    for (x, z) in ((4, 4), (11.25, 4), (4, 11.25), (11.25, 11.25)):
        m.box((x, 2.5, z), (x + 0.75, 9.5, z + 0.75), cage)              # uprights
    for y in (2.25, 9.25):
        m.box((4, y, 4), (12, y + 0.75, 4.75), cage), m.box((4, y, 11.25), (12, y + 0.75, 12), cage)
        m.box((4, y, 4.75), (4.75, y + 0.75, 11.25), cage), m.box((11.25, y, 4.75), (12, y + 0.75, 11.25), cage)
    m.box((7.25, 10, 7.25), (8.75, 11, 8.75), cage)                       # a knot on top
    m.write(upright(**SMALL))


def nether_star():
    """a glowing 3D star: six points straight out and four more on the diagonals"""
    m = Model("nether_star")
    s = Mat(STAR, base=3.4, kind="gem", bevel=0.4, glow=True)
    tip = Mat(STAR, base=4.0, kind="gem", bevel=0.2, glow=True)
    c = 8
    m.box((6, 6, 6), (10, 10, 10), s)
    for (a, b, ta, tb) in (((7, 10, 7), (9, 13, 9), (7.5, 13, 7.5), (8.5, 14.5, 8.5)),
                           ((7, 3, 7), (9, 6, 9), (7.5, 1.5, 7.5), (8.5, 3, 8.5)),
                           ((10, 7, 7), (13, 9, 9), (13, 7.5, 7.5), (14.5, 8.5, 8.5)),
                           ((3, 7, 7), (6, 9, 9), (1.5, 7.5, 7.5), (3, 8.5, 8.5)),
                           ((7, 7, 10), (9, 9, 12.5), (7.5, 7.5, 12.5), (8.5, 8.5, 13.5)),
                           ((7, 7, 3.5), (9, 9, 6), (7.5, 7.5, 2.5), (8.5, 8.5, 3.5))):
        m.box(a, b, s)
        m.box(ta, tb, tip)
    for ang in (45, -45):
        for (a, b) in (((7.25, 10, 7.25), (8.75, 12.5, 8.75)), ((7.25, 3.5, 7.25), (8.75, 6, 8.75))):
            m.box(a, b, tip, rot=(ang, "z", (c, c, c)), ao=False)
    m.write(upright(scale=0.42, lift=5.5))


def blaze_rod():
    """a glowing golden rod with darker bands, standing up"""
    m = Model("blaze_rod")
    r = Mat(BLAZE_ROD, base=3.4, kind="metal", bevel=0.6, glow=True)

    def bands(k, ii, jj, w, h, face):
        return np.where((face not in ("up", "down")) & (jj % 4 == 0), k - 1.8, k)

    m.box((7, 0, 7), (9, 16, 9), r, decal=bands)
    m.box((6.75, 15, 6.75), (9.25, 16, 9.25), r)
    m.box((6.75, 0, 6.75), (9.25, 1, 9.25), r)
    m.write(upright(scale=0.4, lift=5.0))


# ---------------------------------------------------------------- bricks
def brick_like(name, pal):
    m = Model(name)
    b = Mat(pal, base=3.0, kind="organic", bevel=0.8)
    m.box((2.5, 0, 5), (13.5, 5, 11), b, decal=spots(0.06, 0.5, seed=name))
    m.box((2.5, 4.5, 5), (4, 5, 6.5), Mat(pal, base=1.0, bevel=0), faces=("up",))   # a chipped corner
    m.write(upright(**LYING))


def brick():
    brick_like("brick", BRICK)


def nether_brick():
    brick_like("nether_brick", NETHER_BRICK)


# ---------------------------------------------------------------- squishy things
def slime_ball():
    """see-through green slime with a darker core"""
    m = Model("slime_ball")
    outer = Mat(SLIME, base=3.6, bevel=0.6, alpha=170)
    core = Mat(SLIME, base=1.6, bevel=0.3)
    m.box((6, 4, 6), (10, 8, 10), core, ao=False)
    blob(m, (4, 2, 4), (12, 10, 12), outer, decal=shine)
    m.write(upright(**SMALL), translucent=True)


def magma_cream():
    """a ball of molten cream: dark crust with glowing orange cracks"""
    m = Model("magma_cream")
    c = Mat(MAGMA, base=3.6, bevel=0.4, glow=True)

    def crust(k, ii, jj, w, h, face):
        return np.where(((ii * 3 + jj * 2) % 7 < 3), 0.8, k)

    blob(m, (4, 2, 4), (12, 10, 12), c, decal=crust)
    m.write(upright(**SMALL))


MATERIALS = {f.__name__: f for f in (
    diamond, emerald, lapis_lazuli, amethyst_shard, quartz, echo_shard, prismarine_shard, prismarine_crystals,
    coal, charcoal, flint, clay_ball, raw_iron, raw_gold, raw_copper, iron_ingot, gold_ingot, copper_ingot,
    netherite_ingot, netherite_scrap, iron_nugget, gold_nugget, redstone, glowstone_dust, gunpowder, sugar,
    blaze_powder, bone_meal, ender_pearl, ender_eye, heart_of_the_sea, nether_star, blaze_rod, brick, nether_brick,
    slime_ball, magma_cream)}
