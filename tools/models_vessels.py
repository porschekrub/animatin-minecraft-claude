#!/usr/bin/env python3
"""Batch 3 of Lifelike Motion's 3D items: bottles and buckets (built with tools/models.py's parts and painter; run
tools/models.py to write them). Every bucket is the same iron bucket (rolled rim, band, lugs, a carry handle with a
wooden grip) holding something different; every bottle is clear glass you can see into."""
import numpy as np

from models import Mat, Model, upright, GLASS, CORK, STRING, IRON, WOOD, WATER, TINTED
from models_food import COD, COD_BELLY, SALMON, SILVER, TROPIC, WHITE, PUFFER, EYE_DARK, spots, shine

LAVA = ["5a0f02", "9a2204", "d84a08", "f77a12", "ffae2a", "ffd86a", "fff4c0"]
MILK = ["b8b2a8", "d6d1c8", "ece8e0", "f8f6f0", "ffffff"]
SNOW = ["a6b8cc", "c4d4e4", "dde8f2", "eef5fb", "ffffff"]
XP = ["2a5a06", "4a8a0a", "6cba16", "9ae02a", "c8f860", "f0ffb0"]
DRAGON = ["3a0a3a", "5e1462", "8a2690", "b444b8", "d878d8", "f4b4f0", "fff0ff"]
AXOLOTL = ["9a4a6a", "c46a8c", "e290ae", "f4b6cc", "ffd8e6"]
GILLS = ["8a1e4a", "b8306a", "e05290", "f47ab0"]
TADPOLE = ["1a120c", "2e2216", "463424"]


# ---------------------------------------------------------------- buckets
def ripples(k, ii, jj, w, h, face):
    if face == "up":
        band = (ii + jj >= 3) & (ii + jj <= 5)
        k = np.where(band, k + 1.3, k)                                   # the sky reflected across the water
        k = np.where((ii + jj == 9) & (ii >= 4) & (ii <= 5), k + 1.0, k)
        k = np.where((ii == 2) & (jj == 2), k + 3, k)                    # a glint
    return k


def lava_flow(k, ii, jj, w, h, face):
    if face == "up":
        k = np.where(((ii * 2 + jj) % 5 == 0), k + 1.6, k)               # bright cracks
        k = np.where(((ii + jj * 3) % 7 == 0), k - 1.8, k)               # cooling crust
    return k


def bucket(name, fill=None, level=9, extra=None):
    """the iron bucket; fill = (material, decal) filling it to `level`; extra(m) adds what sits in it"""
    m = Model(name)
    iron = Mat(IRON, base=3.6, kind="metal", bevel=0.8, shine=0.45)
    band = Mat(IRON, base=1.8, kind="metal", bevel=0.8, shine=0.5)
    rim = Mat(IRON, base=4.4, kind="metal", bevel=0.9, shine=0.4)
    wood = Mat(WOOD, base=2.6, kind="wood", bevel=0.6)
    m.box((3.5, 0, 3.5), (12.5, 1, 12.5), iron)                          # bottom
    m.box((3, 1, 3), (13, 10, 4), iron), m.box((3, 1, 12), (13, 10, 13), iron)   # walls
    m.box((3, 1, 4), (4, 10, 12), iron), m.box((12, 1, 4), (13, 10, 12), iron)
    if fill:
        m.box((4, 1, 4), (12, level, 12), fill[0], decal=fill[1])
    m.box((2.5, 10, 2.5), (13.5, 11, 3.5), rim), m.box((2.5, 10, 12.5), (13.5, 11, 13.5), rim)  # rolled rim
    m.box((2.5, 10, 3.5), (3.5, 11, 12.5), rim), m.box((12.5, 10, 3.5), (13.5, 11, 12.5), rim)
    m.box((2.75, 3.5, 2.75), (13.25, 4.5, 13.25), band)                  # band
    m.box((1.75, 8, 7), (3, 10, 9), band), m.box((13, 8, 7), (14.25, 10, 9), band)  # lugs
    # the carry handle: up from the lugs, leaning in, across the top with a wooden grip
    m.box((2, 10, 7.6), (2.8, 13, 8.4), band)
    m.box((13.2, 10, 7.6), (14, 13, 8.4), band)
    m.box((2, 12.5, 7.6), (2.8, 16.5, 8.4), band, rot=(-45, "z", (2.4, 12.6, 8)))
    m.box((13.2, 12.5, 7.6), (14, 16.5, 8.4), band, rot=(45, "z", (13.6, 12.6, 8)))
    m.box((5.1, 15.3, 7.6), (10.9, 16.1, 8.4), band)
    m.box((6, 15, 7.25), (10, 16.5, 8.75), wood)
    if extra:
        extra(m)
    m.write(upright(0.3, 5.0))


def water():
    return (Mat(WATER, base=3.3, bevel=0.0), ripples)


def leaping_fish(body_pal, belly_pal, fin_pal):
    """a little fish leaping out of the water"""
    def f(m):
        body = Mat(body_pal, base=3.0, kind="organic", grad=1.0)
        belly = Mat(belly_pal, base=len(belly_pal) / 2, bevel=0.3)
        fin = Mat(fin_pal, base=len(fin_pal) / 2 - 0.5, bevel=0.3)
        dark = Mat(EYE_DARK, base=0.5, bevel=0)
        r = (22.5, "z", (8, 10, 8))
        m.box((5, 9, 7), (10, 12, 9), body, rot=r, decal=shine)
        m.box((5.5, 8.5, 7.25), (9.5, 9, 8.75), belly, rot=r)
        m.box((10, 9.75, 7.5), (11, 11.25, 8.5), body, rot=r)
        m.box((11, 9, 7.6), (12.5, 12, 8.4), fin, rot=r)                 # tail flicking up
        m.box((6.5, 12, 7.6), (8.5, 12.75, 8.4), fin, rot=r)
        m.box((5.5, 10.5, 6.9), (6.25, 11.25, 9.1), dark, rot=r)         # eyes
    return f


def bucket_items():
    return {
        "bucket": lambda: bucket("bucket"),
        "water_bucket": lambda: bucket("water_bucket", water()),
        "lava_bucket": lambda: bucket("lava_bucket", (Mat(LAVA, base=3.4, bevel=0.0, glow=True), lava_flow)),
        "milk_bucket": lambda: bucket("milk_bucket", (Mat(MILK, base=2.6, bevel=0.0),
                                                      lambda k, ii, jj, w, h, face: np.where(
                                                          (face == "up") & (ii == 2) & (jj == 2), 99, k))),
        "powder_snow_bucket": lambda: bucket("powder_snow_bucket", (Mat(SNOW, base=2.8, kind="organic", bevel=0.3),
                                                                    spots(0.08, 99, seed="snow")), level=10,
                                             extra=powder_heap),
        "cod_bucket": lambda: bucket("cod_bucket", water(), extra=leaping_fish(COD, COD_BELLY, COD)),
        "salmon_bucket": lambda: bucket("salmon_bucket", water(), extra=leaping_fish(SALMON, SILVER, SALMON)),
        "tropical_fish_bucket": lambda: bucket("tropical_fish_bucket", water(),
                                               extra=leaping_fish(TROPIC + ["ffffff"], WHITE, TROPIC)),
        "pufferfish_bucket": lambda: bucket("pufferfish_bucket", water(), extra=puffer_peek),
        "axolotl_bucket": lambda: bucket("axolotl_bucket", water(), extra=axolotl_peek),
        "tadpole_bucket": lambda: bucket("tadpole_bucket", water(), extra=tadpoles),
    }


def powder_heap(m):
    snow = Mat(SNOW, base=3.0, kind="organic", bevel=0.4)
    m.box((4.5, 10, 4.5), (11.5, 11.5, 11.5), snow, decal=spots(0.08, 99, seed="heap"))
    m.box((6, 11.5, 6), (10, 12.5, 10), snow, decal=spots(0.08, 99, seed="heap2"))


def puffer_peek(m):
    body = Mat(PUFFER, base=3.2, kind="organic", grad=1.0)
    spike = Mat(["8a6a10", "c8a018", "f0d050"], base=1.4, bevel=0.2)
    dark = Mat(EYE_DARK, base=0.5, bevel=0)
    m.box((5.5, 8, 5.5), (10.5, 12, 10.5), body, decal=shine)
    for (x, y, z) in ((5, 10, 7.5), (10.5, 10.5, 8), (7.5, 12, 7.5), (6.5, 11.5, 10), (9, 11.5, 5)):
        m.box((x, y, z), (x + 0.75, y + 0.75, z + 0.75), spike)
    m.box((6.5, 10, 10.5), (7.5, 11, 10.75), dark), m.box((8.5, 10, 10.5), (9.5, 11, 10.75), dark)


def axolotl_peek(m):
    head = Mat(AXOLOTL, base=2.8, kind="organic", grad=0.8)
    gill = Mat(GILLS, base=2.0, bevel=0.3)
    dark = Mat(EYE_DARK, base=0.5, bevel=0)
    m.box((5, 8.5, 6), (11, 12, 10.5), head, decal=shine)                # head peeking out
    for side in (-1, 1):                                                  # three feathery gills a side
        x = 4.25 if side < 0 else 11
        m.box((x, 10.5, 7.5), (x + 0.75, 13, 8.25), gill)
        m.box((x, 9.5, 8.75), (x + 0.75, 11.5, 9.5), gill)
        m.box((x, 11.5, 6.25), (x + 0.75, 13.5, 7), gill)
    m.box((6.25, 10.5, 10.5), (7, 11.25, 10.75), dark), m.box((9, 10.5, 10.5), (9.75, 11.25, 10.75), dark)
    m.box((7.25, 9.25, 10.5), (8.75, 9.5, 10.6), dark)                   # a little smile


def tadpoles(m):
    t = Mat(TADPOLE, base=1.2, bevel=0.3)
    for (x, z, a) in ((5, 5.5, 0), (8.5, 8, 1), (6, 9.5, 0)):
        m.box((x, 9, z), (x + 1.5, 9.75, z + 1.25), t)
        if a:
            m.box((x - 1.5, 9.1, z + 0.3), (x, 9.5, z + 0.8), t)
        else:
            m.box((x + 1.5, 9.1, z + 0.3), (x + 3, 9.5, z + 0.8), t)


# ---------------------------------------------------------------- bottles
def bottle(name, liquid=None, cork=True, string=True, extra=None, shape="potion"):
    """clear glass you can see into; liquid = (material, decal, top y) or None for an empty bottle"""
    m = Model(name)
    glass = Mat(GLASS, base=1.6, kind="glass", alpha=70, bevel=0.6)
    corkm = Mat(CORK, base=2.4, kind="wood", bevel=0.7)
    stringm = Mat(STRING, base=2.0, bevel=0.3)
    if shape == "potion":
        if liquid:
            m.box((5, 0.5, 5), (11, liquid[2], 11), liquid[0], decal=liquid[1], ao=False)
        m.box((4.5, 0, 4.5), (11.5, 7, 11.5), glass, ao=False)           # body
        m.box((5.5, 7, 5.5), (10.5, 8, 10.5), glass, ao=False)           # shoulder
        m.box((6.5, 8, 6.5), (9.5, 10.5, 9.5), glass, ao=False)          # neck
        m.box((6, 10.5, 6), (10, 11.5, 10), glass, ao=False)             # lip
        if cork:
            m.box((6.75, 10.25, 6.75), (9.25, 13, 9.25), corkm)
        if string:
            m.box((6.25, 8.5, 6.25), (9.75, 9.25, 9.75), stringm)
            m.box((9.75, 6.5, 7.5), (10.25, 8.75, 8.5), stringm)         # its loose end
    elif shape == "splash":
        # a round bottle with a short neck and a pull-cord, made for throwing
        if liquid:
            m.box((5, 1, 5), (11, liquid[2], 11), liquid[0], decal=liquid[1], ao=False)
            m.box((4, 2, 5.5), (12, liquid[2] - 0.5, 10.5), liquid[0], decal=liquid[1], ao=False)
            m.box((5.5, 2, 4), (10.5, liquid[2] - 0.5, 12), liquid[0], decal=liquid[1], ao=False)
        m.box((4.5, 0, 4.5), (11.5, 7, 11.5), glass, ao=False)
        m.box((3.5, 1.5, 5), (4.5, 5.5, 11), glass, ao=False, faces=("west", "up", "down", "north", "south"))
        m.box((11.5, 1.5, 5), (12.5, 5.5, 11), glass, ao=False, faces=("east", "up", "down", "north", "south"))
        m.box((5, 1.5, 3.5), (11, 5.5, 4.5), glass, ao=False, faces=("north", "up", "down", "east", "west"))
        m.box((5, 1.5, 11.5), (11, 5.5, 12.5), glass, ao=False, faces=("south", "up", "down", "east", "west"))
        m.box((6.5, 7, 6.5), (9.5, 9, 9.5), glass, ao=False)
        m.box((6, 9, 6), (10, 10, 10), glass, ao=False)
        m.box((6.75, 8.75, 6.75), (9.25, 11.5, 9.25), corkm)
        m.box((6.25, 7.5, 6.25), (9.75, 8.25, 9.75), stringm)
        m.box((9.75, 7.5, 7.6), (11.75, 8.25, 8.4), stringm)               # the pull-cord, looped
        m.box((11.25, 5.5, 7.6), (11.75, 7.5, 8.4), stringm)
    elif shape == "lingering":
        # a wide, low flask that lets its mist out slowly
        if liquid:
            m.box((4, 0.5, 5.5), (12, liquid[2], 10.5), liquid[0], decal=liquid[1], ao=False)
        m.box((3.5, 0, 5), (12.5, 5, 11), glass, ao=False)
        m.box((4.5, 5, 6), (11.5, 6, 10), glass, ao=False)
        m.box((6.75, 6, 6.75), (9.25, 9, 9.25), glass, ao=False)
        m.box((6.25, 9, 6.25), (9.75, 10, 9.75), glass, ao=False)
        m.box((7, 8.75, 7), (9, 11.25, 9), corkm)
        m.box((6.5, 7, 6.5), (9.5, 7.75, 9.5), stringm)
    if extra:
        extra(m)
    m.write(upright(0.34, 5.0), translucent=True)


def tinted():
    def surface(k, ii, jj, w, h, face):
        if face == "up":
            k = k + 1.2
            k = np.where((ii == 1) & (jj == 1), k + 1.5, k)
        return k
    return Mat(TINTED, base=3.0, tint=True, bevel=0.5), surface


def mist(m):
    """a wisp of the potion's mist curling up from the cork"""
    wisp = Mat(TINTED, base=4, tint=True, alpha=120, bevel=0.2)
    m.box((7.5, 11.5, 7.5), (9, 12.5, 9), wisp, ao=False)
    m.box((8.5, 12.5, 7.75), (10, 13.5, 8.75), wisp, ao=False)
    m.box((7.25, 13.5, 7.9), (8.75, 14.25, 8.6), wisp, ao=False)


def sparkles(k, ii, jj, w, h, face):
    return np.where(((ii * 3 + jj * 5) % 7 == 0), 99, k)


def swirl(k, ii, jj, w, h, face):
    return np.where(((ii + jj * 2) % 5 < 2), k + 1.4, k - 0.4)


def bottle_items():
    t = tinted()
    return {
        "potion": lambda: bottle("potion", (t[0], t[1], 5.5)),
        "glass_bottle": lambda: bottle("glass_bottle", None, cork=False),
        "splash_potion": lambda: bottle("splash_potion", (t[0], t[1], 6), shape="splash"),
        "lingering_potion": lambda: bottle("lingering_potion", (t[0], t[1], 4.5), shape="lingering", extra=mist),
        "experience_bottle": lambda: bottle("experience_bottle",
                                            (Mat(XP, base=3.2, bevel=0.4, glow=True), sparkles, 6.5)),
        "dragon_breath": lambda: bottle("dragon_breath", (Mat(DRAGON, base=3.4, bevel=0.3, glow=True), swirl, 6.5),
                                        extra=dragon_wisp),
    }


def dragon_wisp(m):
    wisp = Mat(DRAGON, base=4.5, alpha=150, glow=True, bevel=0.2)
    m.box((7.5, 13, 7.5), (9, 14, 9), wisp, ao=False)
    m.box((8.5, 14, 7.75), (10, 15, 8.75), wisp, ao=False)


VESSELS = {**bucket_items(), **bottle_items()}
GUI = {"potion": ["minecraft:item/potion_overlay", "minecraft:item/potion"]}
