#!/usr/bin/env python3
"""Batch 2 of Lifelike Motion's 3D items: every food, made to look beautiful (built with tools/models.py's parts and
painter; run tools/models.py to write them). Flat things (a cookie, a steak, a fish) are modelled standing up, facing
you, which is how they're held; bowls and pies are held tipped toward you so you see what's in them."""
import hashlib

import numpy as np

from models import Mat, Model, upright, LEAF, STEM, APPLE, GLASS, CORK, WOOD  # noqa: F401


def rnd01(*k):
    return int(hashlib.md5(repr(k).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


# ---------------------------------------------------------------- palettes (dark -> light)
GOLDEN = ["5e3f04", "8f6409", "c08c12", "e2b02a", "f4d15a", "ffeb9c", "fffbe0"]
BREAD = ["4e2b0e", "754217", "9c5d22", "c07d31", "da9e48", "ecc274", "f8e3ad"]
COOKIE = ["2a1407", "6b3d14", "8f5420", "b06f2c", "c98a3e", "dca659", "efc983"]
CRUST = ["5a3712", "84551f", "a8732f", "c99447", "e0b468", "f2d495"]
PUMPKIN = ["6e2a04", "9a3f08", "c5590f", "e07a22", "f19c42", "fbc27a"]
CREAM = ["b9b0a4", "d8d0c4", "eee8de", "fbf8f2", "ffffff"]
RIND = ["1e4012", "2c5c1a", "3f7d24", "5aa034", "86c45a"]
MELON = ["1a0908", "7a0f14", "b01c22", "d8322f", "ef5a48", "fb8a74", "ffd2c4"]
BERRY = ["3a040c", "660a16", "960f22", "c81c32", "ea4255", "ff8a96", "ffd6dc"]
GLOW = ["6a2a04", "a8480a", "e07a14", "ffa52a", "ffc85a", "ffe7a0", "fffbe8"]
VINE = ["1d3d12", "2c5a1a", "3f7a24", "59992f"]
CARROT = ["6b2a04", "9a3e07", "c9590e", "eb7a1c", "f9a03e", "ffc775"]
POTATO = ["5a3f1c", "80602c", "a5813e", "c49e55", "dcbb72", "efd798"]
BAKED = ["3f2410", "60391a", "855328", "a8713a", "c7914f", "e0b06a"]
FLUFF = ["c9b27a", "e3d09c", "f3e6bf", "fff7de", "fffdf4"]
BUTTER = ["c99a12", "e8bd2a", "f8d95a", "fff09a"]
POISON = ["3d4512", "5b6618", "7c8a22", "9aa830", "b8c450", "d4dc80"]
BEET = ["2e0516", "4c0a24", "6e1034", "931a45", "b52d5a", "d65a7e"]
RAW = ["4a0a0c", "7a1416", "a82020", "cc3a34", "e2645a", "f29a90"]
FAT = ["c9a29a", "e3c3ba", "f3ddd6", "fdf1ec", "ffffff"]
COOKED = ["2a1408", "4a2410", "6b3818", "8c4e22", "a8682e", "c4853e", "dca55a"]
PORK = ["7a3a3a", "a8565a", "cc7a7c", "e29c9a", "f2bebb", "fde0dc"]
ROAST = ["4a2008", "72340c", "9a4c14", "c06a1e", "dc8a30", "f0ae4c", "fcd27c"]
BONE = ["9c9284", "c4bba9", "e2dccb", "f6f2e6", "ffffff"]
SKIN = ["a8746a", "c99488", "e2b3a6", "f2cdc0", "fde7dd"]
COD = ["3c2c1c", "5e4630", "826446", "a3845e", "c2a67c", "dccaa0"]
COD_BELLY = ["9a8a70", "bcae92", "dcd2b8", "f2ecda"]
COD_COOKED = ["5a3a1c", "86582a", "ae7a3e", "cf9c58", "e6be7c", "f6dcaa"]
SALMON = ["3a0e10", "641a1c", "8f2a26", "b8402e", "d86040", "ee8a5c"]
SILVER = ["6c7478", "8f989c", "b4bcc0", "d6dcde", "f2f5f6"]
SALMON_COOKED = ["8a3a24", "b85a3a", "dc7c54", "f29c72", "fcbc96", "ffdcc4"]
TROPIC = ["7a2a04", "b04a08", "e06e12", "f7922a", "ffb456", "ffd498"]
WHITE = ["9aa0a6", "c4c9ce", "e4e8eb", "f8fafb", "ffffff"]
PUFFER = ["6e5408", "9c780c", "c8a014", "e8c42a", "f8de5a", "fff09a"]
EYE_DARK = ["0a0a0c", "1c1c22", "34343c"]
BOWL = ["3a230e", "593818", "7a5024", "9a6a32", "b88544", "d4a35c"]
BROTH = ["3e2210", "5c3418", "7a4822", "966030", "b07a42", "c99658"]
RED_SOUP = ["3e0610", "640c1a", "8e1626", "b82434", "d8444e", "f07a80"]
MUSH_RED = ["5a0808", "8a1414", "bc2420", "e0443a", "f4807a"]
MUSH_TAN = ["6a4a30", "8e6a48", "b08c64", "cfae84", "e8cfa8"]
FLESH = ["3a3214", "5a4c1e", "7c6a2a", "8f6f44", "a8805a", "c49a78"]
FLESH_SKIN = ["4a5a1c", "647828", "7f9632", "9cb048"]
SPIDER = ["3c0410", "62081c", "8e102a", "b81c3a", "dc3a56", "f47a8e"]
KELP = ["0e1e0a", "18300f", "234216", "30561e", "426e2a"]
CHORUS = ["2a1030", "44204c", "62326c", "80488a", "9e66a6", "c494c8", "ead0ea"]
HONEY = ["7a3c04", "a85806", "d6800e", "f0a420", "fcc448", "ffe28a"]
STRAW = ["8a6a2c", "b08c40", "d2ae58", "ecca78"]


# ---------------------------------------------------------------- shapes
def blob(m, lo, hi, mat, s=1.0, decal=None, top=None, top_decal=None, faces_top=None):
    """a rounded block: a core with stepped-in sides, top and bottom (smooth-looking at Minecraft's scale)"""
    x0, y0, z0 = lo
    x1, y1, z1 = hi
    m.box((x0 + s, y0 + s, z0 + s), (x1 - s, y1 - s, z1 - s), mat, decal=decal, ao=False)
    m.box((x0, y0 + 2 * s, z0 + 1.5 * s), (x1, y1 - 2 * s, z1 - 1.5 * s), mat, decal=decal)
    m.box((x0 + 1.5 * s, y0 + 2 * s, z0), (x1 - 1.5 * s, y1 - 2 * s, z1), mat, decal=decal)
    m.box((x0 + 2 * s, y1 - s, z0 + 2 * s), (x1 - 2 * s, y1, z1 - 2 * s), top or mat, decal=top_decal or decal,
          faces=faces_top)
    m.box((x0 + 2 * s, y0, z0 + 2 * s), (x1 - 2 * s, y0 + s, z1 - 2 * s), mat, decal=decal)


def slab(m, x0, y0, x1, y1, z0, z1, mat, s=1.0, decal=None):
    """a flat thing standing up facing you, with rounded corners"""
    m.box((x0 + s, y0, z0), (x1 - s, y1, z1), mat, decal=decal)
    m.box((x0, y0 + s, z0 + 0.1), (x1, y1 - s, z1 - 0.1), mat, decal=decal)


def disc(m, cx, cy, r, z0, z1, mat, decal=None):
    """a round flat thing standing up facing you (an octagon of three boxes)"""
    a = r * 0.42
    m.box((cx - a, cy - r, z0), (cx + a, cy + r, z1), mat, decal=decal)
    m.box((cx - r + 0.6, cy - r + 0.6, z0 + 0.1), (cx + r - 0.6, cy + r - 0.6, z1 - 0.1), mat, decal=decal)
    m.box((cx - r, cy - a, z0 + 0.2), (cx + r, cy + a, z1 - 0.2), mat, decal=decal)


def leaf(m, x, y, length, mat, angle, z=7.5, w=1.0, origin=None):
    """a thin leaf blade sticking out at an angle (22.5 / 45 degree steps)"""
    o = origin or (x, y, z + w / 2)
    m.box((x, y, z), (x + 1, y + length, z + w), mat, rot=(angle, "z", o) if angle else None, ao=False)


# ---------------------------------------------------------------- details (decals)
def shine(k, ii, jj, w, h, face):
    """a soft glossy highlight high on the lit faces"""
    if face in ("south", "west") and w >= 4 and h >= 4:
        k = np.where((jj == 1) & (ii >= 1) & (ii <= 2), 99, k)
        k = np.where((jj == 2) & (ii == 1), k + 2, k)
    return k


def spots(density, value, seed=0, faces=None, add=False):
    """a scatter of single pixels (seeds, speckles, chips, eyes)"""
    def f(k, ii, jj, w, h, face):
        if faces and face not in faces:
            return k
        mask = np.array([[rnd01(seed, face, w, h, i, j) < density for i in range(w)] for j in range(h)])
        return np.where(mask, k + value if add else value, k)
    return f


def stripes(every, value, axis="h", faces=("north", "south", "east", "west"), offset=0):
    """lines across a face (rings on a carrot, a wrapped band, flakes)"""
    def f(k, ii, jj, w, h, face):
        if face not in faces:
            return k
        line = ((jj if axis == "h" else ii) + offset) % every == 0
        return np.where(line, k + value, k)
    return f


def grill(k, ii, jj, w, h, face):
    """dark grill marks across the big faces of cooked meat"""
    if face in ("north", "south"):
        k = np.where(((ii + jj) % 4 == 0), 0.2, k)
    return k


def chain(*fs):
    def f(k, ii, jj, w, h, face):
        for g in fs:
            k = g(k, ii, jj, w, h, face)
        return k
    return f


def clamp_top(pal_len):
    """99 means "the palette's lightest step" (a highlight)"""
    return pal_len - 1


# ---------------------------------------------------------------- fruit and vegetables
def apple_like(name, pal, leaf_pal=LEAF, base=3.6):
    m = Model(name)
    skin = Mat(pal, base=base, kind="organic", grad=1.3)
    top = Mat(pal, base=base + 0.8, kind="organic", grad=1.0)
    stem = Mat(STEM, base=1.6, bevel=0.4)
    lf = Mat(leaf_pal, base=len(leaf_pal) / 2 - 0.4, bevel=0.2)

    def ring(k, ii, jj, w, h, face):
        if face == "up":
            r = np.hypot(ii - (w - 1) / 2, jj - (h - 1) / 2)
            k = np.where(r < 1.6, k - 1.6, k)
        return k

    def vein(k, ii, jj, w, h, face):
        return np.where(jj == h // 2, k + 1.4, k) if face in ("up", "down") else k

    m.box((4, 1, 4), (12, 10, 12), skin, ao=False)
    m.box((3, 2, 4.5), (13, 9, 11.5), skin, decal=shine)
    m.box((4.5, 2, 3), (11.5, 9, 13), skin, decal=shine)
    m.box((5, 10, 5), (11, 11, 11), top, decal=ring)
    m.box((5, 0, 5), (11, 1, 11), skin)
    m.box((7.5, 10.5, 7.5), (8.5, 14, 8.5), stem, rot=(22.5, "z", (8, 10.5, 8)))
    m.box((8.5, 12.5, 6.5), (13, 13, 9.5), lf, rot=(-22.5, "z", (8.5, 12.5, 8)), decal=vein, ao=False)
    m.write(upright(0.34, 4.0))


def apple():
    apple_like("apple", APPLE)


def golden_apple():
    apple_like("golden_apple", GOLDEN, leaf_pal=GOLDEN, base=3.2)


def enchanted_golden_apple():
    apple_like("enchanted_golden_apple", GOLDEN, leaf_pal=GOLDEN, base=3.4)


def carrot_like(name, pal, top_pal):
    m = Model(name)
    body = Mat(pal, base=3.2, kind="organic", grad=0.8)
    green = Mat(top_pal, base=len(top_pal) / 2, bevel=0.3)
    rings = stripes(3, -1.1, offset=1)
    m.box((7.5, 0, 7.5), (8.5, 1.5, 8.5), body)                          # the tip
    m.box((7, 1.5, 7), (9, 4.5, 9), body, decal=rings)
    m.box((6.5, 4.5, 6.5), (9.5, 8, 9.5), body, decal=rings)
    m.box((6, 8, 6), (10, 11, 10), body, decal=chain(rings, shine))
    m.box((6.5, 11, 6.5), (9.5, 11.5, 9.5), body)
    leaf(m, 7.5, 11.5, 4.5, green, 0)
    leaf(m, 6.6, 11.3, 3.5, green, 22.5, origin=(7.1, 11.5, 8))
    leaf(m, 8.4, 11.3, 3.8, green, -22.5, origin=(8.9, 11.5, 8))
    m.write(upright(0.36, 4.0))


def carrot():
    carrot_like("carrot", CARROT, VINE)


def golden_carrot():
    carrot_like("golden_carrot", GOLDEN, GOLDEN)


def potato_like(name, pal, extra=None, eyes=0.06):
    m = Model(name)
    skin = Mat(pal, base=3.0, kind="organic", grad=1.0)
    blob(m, (3, 0, 4.5), (13, 6.5, 11.5), skin, decal=chain(spots(eyes, 0.6, seed=name), shine))
    m.box((13, 2, 6.5), (14, 4.5, 9.5), skin)                             # a little lump at one end
    if extra:
        extra(m)
    m.write(upright(0.36, 4.5, tilt=22))


def potato():
    potato_like("potato", POTATO)


def baked_potato():
    def split(m):
        fluff = Mat(FLUFF, base=2.4, kind="organic", bevel=0.4)
        butter = Mat(BUTTER, base=2.2, bevel=0.6)
        m.box((5, 6, 6.5), (11, 6.75, 9.5), fluff)                        # the soft inside, through a split
        m.box((6.5, 6.5, 7), (9, 7.5, 9), butter)                         # a pat of butter
    potato_like("baked_potato", BAKED, split, eyes=0.0)


def poisonous_potato():
    potato_like("poisonous_potato", POISON, eyes=0.14)


def beetroot():
    m = Model("beetroot")
    bulb = Mat(BEET, base=3.2, kind="organic", grad=1.0)
    stalk = Mat(BEET, base=4.2, bevel=0.3)
    green = Mat(VINE, base=2.0, bevel=0.3)
    blob(m, (4.5, 1.5, 4.5), (11.5, 8.5, 11.5), bulb, decal=shine)
    m.box((7.5, 0, 7.5), (8.5, 1.5, 8.5), bulb)                          # root tip
    m.box((7.5, 8.5, 7.5), (8.5, 10, 8.5), stalk)
    leaf(m, 6.4, 9.6, 4.5, green, 22.5, w=1.2, origin=(6.9, 9.8, 8))
    leaf(m, 8.6, 9.6, 5, green, -22.5, w=1.2, origin=(9.1, 9.8, 8))
    m.write(upright(0.36, 4.0))


def melon_slice():
    m = Model("melon_slice")
    rind = Mat(RIND, base=2.4, bevel=0.5)
    pith = Mat(["d8e8c0", "eef6e0", "fbfff4"], base=1.0, bevel=0.0)
    flesh = Mat(MELON, base=3.6, kind="organic", grad=0.6)
    seeds = spots(0.08, 0.2, seed="melon", faces=("north", "south"))
    m.box((2, 1, 7), (14, 2.5, 9.5), rind)                               # a wedge, rind along the bottom
    m.box((2.5, 2.5, 7.1), (13.5, 3, 9.4), pith)
    m.box((3, 3, 7.1), (13, 5.5, 9.4), flesh, decal=seeds)
    m.box((4.5, 5.5, 7.15), (11.5, 8, 9.35), flesh, decal=seeds)
    m.box((6, 8, 7.2), (10, 10, 9.3), flesh, decal=seeds)
    m.box((7.25, 10, 7.25), (8.75, 11.5, 9.25), flesh)
    m.write(upright(0.4, 4.0, turn=-25))


def berries(name, pal, stem_pal, glow=False):
    m = Model(name)
    b = Mat(pal, base=3.2, grad=0.8, glow=glow, bevel=0.6)
    stem = Mat(stem_pal, base=1.6, bevel=0.3)
    green = Mat(VINE, base=2.2, bevel=0.2)
    for (x, y, z, s) in ((4.5, 1, 7, 3.2), (7.5, 1.5, 5.5, 3), (8, 0.5, 8.5, 3.2), (6, 3.8, 6.8, 3),
                         (9.2, 3.5, 7.2, 2.8)):
        m.box((x, y, z), (x + s, y + s, z + s), b, decal=shine)
    m.box((7.5, 6.5, 7.5), (8.5, 10, 8.5), stem)
    m.box((8.5, 9, 7.6), (9.5, 9.6, 8.4), stem)
    leaf(m, 8.8, 8.6, 3.5, green, -45, w=1.5, origin=(9.3, 9, 8.2))
    leaf(m, 6.2, 8.8, 3, green, 45, w=1.5, origin=(6.7, 9.2, 8.2))
    m.write(upright(0.38, 4.0))


def sweet_berries():
    berries("sweet_berries", BERRY, STEM)


def glow_berries():
    berries("glow_berries", GLOW, VINE, glow=True)


def chorus_fruit():
    m = Model("chorus_fruit")
    c = Mat(CHORUS, base=3.4, kind="organic", grad=1.0)
    speck = spots(0.08, 5.5, seed="chorus")
    blob(m, (4, 0, 4), (12, 8, 12), c, decal=chain(speck, shine))
    m.box((3, 5, 6), (6, 9, 9), c, decal=speck)                           # lumps
    m.box((9, 6, 5), (12.5, 10, 8.5), c, decal=speck)
    m.box((6.5, 7.5, 7.5), (9.5, 11, 10.5), c, decal=speck)
    m.write(upright(0.36, 4.0))


# ---------------------------------------------------------------- baked things
def bread():
    m = Model("bread")
    crust = Mat(BREAD, base=3.6, kind="organic", grad=1.2)
    top = Mat(BREAD, base=4.2, kind="organic")

    def cuts(k, ii, jj, w, h, face):
        if face == "up":
            k = np.where((ii + jj) % 4 == 0, 6, k)                        # the scored cuts, pale inside
        return k

    blob(m, (2, 0, 5), (14, 6, 11), crust, decal=shine, top=top, top_decal=cuts)
    m.write(upright(0.38, 4.5, tilt=20))


def cookie():
    m = Model("cookie")
    dough = Mat(COOKIE, base=4.0, kind="organic", grad=0.5)
    chips = spots(0.12, 0, seed="cookie", faces=("north", "south"))
    disc(m, 8, 7, 5.5, 7, 9, dough, decal=chips)
    m.write(upright(0.4, 4.5, turn=-20))


def pumpkin_pie():
    m = Model("pumpkin_pie")
    crust = Mat(CRUST, base=3.2, kind="organic", grad=0.8)
    fill = Mat(PUMPKIN, base=3.2, grad=0.5, bevel=0.3)
    cream = Mat(CREAM, base=2.6, bevel=0.6)

    def crimp(k, ii, jj, w, h, face):
        return np.where(ii % 2 == 0, k + 0.8, k) if face == "up" else k

    m.box((2.5, 0, 2.5), (13.5, 2.5, 13.5), crust, faces=("north", "south", "east", "west", "down"))
    m.box((3.5, 2, 3.5), (12.5, 2.75, 12.5), fill, ao=False)
    for (a, b) in (((2, 2.5, 2), (14, 3.5, 3.5)), ((2, 2.5, 12.5), (14, 3.5, 14)),
                   ((2, 2.5, 3.5), (3.5, 3.5, 12.5)), ((12.5, 2.5, 3.5), (14, 3.5, 12.5))):
        m.box(a, b, crust, decal=crimp)                                    # the crimped rim
    m.box((6.75, 2.75, 6.75), (9.25, 4, 9.25), cream)                      # a swirl of cream
    m.box((7.25, 4, 7.25), (8.75, 4.75, 8.75), cream)
    m.box((7.75, 4.75, 7.75), (8.25, 5.25, 8.25), cream)
    m.write(upright(0.36, 5.0, tilt=40))


# ---------------------------------------------------------------- meat
def marbled(k, ii, jj, w, h, face):
    """white streaks of fat through raw meat"""
    if face in ("north", "south"):
        k = np.where(((ii * 2 + jj * 3) % 9 == 0) | ((ii - jj * 2) % 11 == 0), 99, k)
    return k


def steak(name, cooked):
    m = Model(name)
    meat = Mat(COOKED if cooked else RAW, base=3.4 if cooked else 3.0, kind="organic", grad=0.7)
    fat = Mat(COOKED[2:] if cooked else FAT, base=2.2, bevel=0.6)
    detail = chain(grill, shine) if cooked else chain(marbled, shine)
    slab(m, 2.5, 2, 13.5, 12, 7, 9.5, meat, s=1.5, decal=detail)
    m.box((4, 12, 7.1), (12, 13.25, 9.4), fat)                            # a rim of fat along the top
    m.box((2, 5, 7.1), (2.5, 10, 9.4), fat)
    m.write(upright(0.38, 4.0, turn=-25))


def beef():
    steak("beef", False)


def cooked_beef():
    steak("cooked_beef", True)


def chop(name, cooked):
    m = Model(name)
    meat = Mat(ROAST if cooked else PORK, base=3.2, kind="organic", grad=0.7)
    bone = Mat(BONE, base=2.6, bevel=0.6)
    detail = chain(grill, shine) if cooked else shine
    slab(m, 4, 2, 14, 12, 7, 9.5, meat, s=1.5, decal=detail)
    m.box((1, 6, 7.5), (4, 8, 9), bone)                                    # the bone
    m.box((0, 5.25, 7.25), (1.5, 8.75, 9.25), bone)
    m.write(upright(0.38, 4.0, turn=-25))


def porkchop():
    chop("porkchop", False)


def cooked_porkchop():
    chop("cooked_porkchop", True)


def drumstick(name, pal, base, scale=0.36, small=False):
    """a leg of meat with the bone sticking out of the top"""
    m = Model(name)
    meat = Mat(pal, base=base, kind="organic", grad=1.0)
    bone = Mat(BONE, base=2.6, bevel=0.6)
    if small:
        blob(m, (5, 0, 5.5), (11, 6, 10.5), meat, decal=shine)
        m.box((7.25, 6, 7.25), (8.75, 9, 8.75), bone)
        m.box((6.5, 9, 7), (9.5, 10.5, 9), bone)
    else:
        blob(m, (4, 0, 5), (12, 8, 11), meat, decal=shine)
        m.box((5, 7, 6), (11, 9, 10), meat)
        m.box((7, 9, 7.25), (9, 12.5, 8.75), bone)
        m.box((6.25, 12.5, 6.75), (9.75, 14, 9.25), bone)
    m.write(upright(scale, 4.0))


def mutton():
    drumstick("mutton", RAW, 3.0)


def cooked_mutton():
    drumstick("cooked_mutton", COOKED, 3.6)


def rabbit():
    drumstick("rabbit", PORK, 2.8, small=True)


def cooked_rabbit():
    drumstick("cooked_rabbit", ROAST, 3.0, small=True)


def bird(name, cooked):
    """a whole chicken: a plump body, two legs with bone ends"""
    m = Model(name)
    pal = ROAST if cooked else SKIN
    body = Mat(pal, base=3.4 if cooked else 2.6, kind="organic", grad=1.0)
    bone = Mat(BONE, base=2.6, bevel=0.6)
    blob(m, (3, 0, 4), (12, 7.5, 12), body, decal=shine)
    for z in (4.5, 9):
        m.box((10.5, 2, z), (13.5, 5.5, z + 2.5), body, decal=shine)       # legs
        m.box((13.5, 3, z + 0.75), (15, 4.25, z + 1.75), bone)
        m.box((14.75, 2.5, z + 0.5), (15.75, 4.75, z + 2), bone)
    m.write(upright(0.36, 4.5, tilt=18))


def chicken():
    bird("chicken", False)


def cooked_chicken():
    bird("cooked_chicken", True)


def rotten_flesh():
    m = Model("rotten_flesh")
    f = Mat(FLESH, base=3.0, kind="organic", grad=0.8)
    green = spots(0.2, 0.8, seed="rot", faces=("north", "south"))
    slab(m, 3, 2, 13, 12, 7.25, 9, f, s=1.5, decal=green)
    m.box((2, 4, 7.4), (3, 7, 8.8), f), m.box((13, 6, 7.4), (14, 9, 8.8), f)   # torn edges
    m.box((5, 12, 7.4), (8, 13, 8.8), f), m.box((9, 1, 7.4), (12, 2, 8.8), f)
    m.write(upright(0.38, 4.0, turn=-25))


def spider_eye():
    m = Model("spider_eye")
    eye = Mat(SPIDER, base=3.2, kind="organic", grad=1.0)
    dark = Mat(EYE_DARK, base=1.0, bevel=0.3)
    gloss = Mat(["ffffff", "ffffff"], base=1, bevel=0)
    veins = spots(0.1, -1.2, seed="spider", add=True)
    blob(m, (4, 1, 4), (12, 9, 12), eye, decal=chain(veins, shine))
    m.box((6.75, 3.5, 12), (9.25, 6.5, 12.3), dark, faces=("south", "east", "west", "up", "down"))   # the pupil
    m.box((7, 5.5, 12.3), (7.75, 6.25, 12.4), gloss, faces=("south",))
    m.write(upright(0.36, 4.0, turn=-20))


def dried_kelp():
    m = Model("dried_kelp")
    k = Mat(KELP, base=2.6, kind="organic", grad=0.8)
    band = Mat(STRAW, base=1.8, bevel=0.5)
    rolls = stripes(2, 1.0, axis="v", faces=("north", "south", "up"))
    blob(m, (2.5, 2, 5.5), (13.5, 7, 10.5), k, decal=rolls)                # a rolled sheet
    m.box((7, 1.75, 5.25), (8.5, 7.25, 10.75), band)                       # tied with straw
    m.write(upright(0.38, 4.5, tilt=18))


# ---------------------------------------------------------------- fish
def fish(name, body_pal, belly_pal, fin_pal, base=3.0, pattern=None):
    m = Model(name)
    body = Mat(body_pal, base=base, kind="organic", grad=1.4)
    belly = Mat(belly_pal, base=len(belly_pal) / 2, bevel=0.4)
    fin = Mat(fin_pal, base=len(fin_pal) / 2 - 0.5, bevel=0.3)
    dark = Mat(EYE_DARK, base=0.5, bevel=0)
    detail = chain(pattern, shine) if pattern else shine
    m.box((3, 4.5, 6.75), (12, 9.5, 9.25), body, decal=detail)            # body
    m.box((2, 5.5, 7), (13, 8.5, 9), body, decal=detail)
    m.box((3.5, 3.5, 7), (11, 4.5, 9), belly)                              # pale belly
    m.box((12.5, 6, 7.4), (14, 8, 8.6), body)                              # tail root
    m.box((13.5, 3.5, 7.6), (15.5, 6.5, 8.4), fin), m.box((13.5, 7.5, 7.6), (15.5, 10.5, 8.4), fin)  # tail
    m.box((5.5, 9.5, 7.6), (10, 11, 8.4), fin)                             # back fin
    m.box((6, 2.5, 7.6), (8, 3.5, 8.4), fin)
    m.box((3.25, 7, 6.6), (4.5, 8.25, 9.4), dark)                          # eyes
    m.write(upright(0.36, 4.0, turn=-20))


def scales(k, ii, jj, w, h, face):
    return np.where((face in ("north", "south")) & ((ii + 2 * jj) % 5 == 0), k - 0.8, k)


def flakes(k, ii, jj, w, h, face):
    return np.where((face in ("north", "south")) & (ii % 3 == 0), k + 1.0, k)


def tropical_bands(k, ii, jj, w, h, face):
    return np.where((face in ("north", "south")) & ((ii == 2) | (ii == 6)), 99, k)


def cod():
    fish("cod", COD, COD_BELLY, COD, pattern=spots(0.1, -1.2, seed="cod", add=True))


def cooked_cod():
    fish("cooked_cod", COD_COOKED, COD_COOKED[2:], COD_COOKED, base=3.2, pattern=flakes)


def salmon():
    fish("salmon", SALMON, SILVER, SALMON, base=3.2, pattern=scales)


def cooked_salmon():
    fish("cooked_salmon", SALMON_COOKED, SALMON_COOKED[2:], SALMON_COOKED, base=3.0, pattern=flakes)


def tropical_fish():
    fish("tropical_fish", TROPIC + ["ffffff"], WHITE, TROPIC, base=3.2, pattern=tropical_bands)


def pufferfish():
    m = Model("pufferfish")
    body = Mat(PUFFER, base=3.2, kind="organic", grad=1.0)
    spike = Mat(["8a6a10", "c8a018", "f0d050"], base=1.4, bevel=0.2)
    dark = Mat(EYE_DARK, base=0.5, bevel=0)
    fin = Mat(TROPIC, base=3, bevel=0.3)
    blob(m, (4, 1.5, 4), (12, 10.5, 12), body, decal=chain(spots(0.07, -1.0, seed="puff", add=True), shine))
    for (x, y, z) in ((3, 5, 7.5), (12, 6, 8), (7.5, 10.5, 7.5), (5, 9, 5), (10, 3, 10), (9.5, 9.5, 10.5),
                      (6, 3.5, 4.5), (11, 8, 4.5), (4.5, 7.5, 11)):
        m.box((x, y, z), (x + 1, y + 1, z + 1), spike)                     # spikes
    m.box((5, 6, 11.75), (6.5, 7.5, 12.25), dark), m.box((9.5, 6, 11.75), (11, 7.5, 12.25), dark)  # eyes
    m.box((12, 3.5, 7.5), (13.5, 6, 8.5), fin), m.box((2.5, 3.5, 7.5), (4, 6, 8.5), fin)
    m.write(upright(0.36, 4.0))


# ---------------------------------------------------------------- bowls and bottles
def stew(name, broth_pal, chunks):
    m = Model(name)
    bowl = Mat(BOWL, base=3.0, kind="wood", bevel=0.6)
    soup = Mat(broth_pal, base=3.0, kind="organic", grad=0.3, bevel=0.0)
    sides = ("north", "south", "east", "west", "down")
    m.box((5.5, 0, 5.5), (10.5, 1, 10.5), bowl)                            # foot
    m.box((4.5, 1, 4.5), (11.5, 2, 11.5), bowl, faces=sides)               # curving out...
    m.box((3.5, 2, 4.5), (12.5, 4.5, 11.5), bowl, faces=sides)             # ...to a round belly
    m.box((4.5, 2, 3.5), (11.5, 4.5, 12.5), bowl, faces=sides)
    m.box((4, 4, 4), (12, 4.6, 12), soup, faces=("up",), ao=False)         # the soup
    for (a, b) in (((4.5, 4, 3), (11.5, 5, 4)), ((4.5, 4, 12), (11.5, 5, 13)), ((3, 4, 4.5), (4, 5, 11.5)),
                   ((12, 4, 4.5), (13, 5, 11.5)), ((3.5, 4, 3.5), (4.5, 5, 4.5)), ((11.5, 4, 3.5), (12.5, 5, 4.5)),
                   ((3.5, 4, 11.5), (4.5, 5, 12.5)), ((11.5, 4, 11.5), (12.5, 5, 12.5))):
        m.box(a, b, bowl)                                                  # the rounded rim
    for (x, z, s, pal) in chunks:
        m.box((x, 4.4, z), (x + s, 4.4 + s * 0.6, z + s), Mat(pal, base=len(pal) / 2, bevel=0.5))
    m.write(upright(0.38, 5.0, tilt=42))


def mushroom_stew():
    stew("mushroom_stew", BROTH, [(5, 5, 2, MUSH_TAN), (8.5, 6.5, 2, MUSH_RED), (6, 9, 1.5, MUSH_TAN),
                                  (9.5, 9.5, 1.5, MUSH_RED)])


def rabbit_stew():
    stew("rabbit_stew", BROTH, [(5, 5.5, 2, CARROT), (8.5, 5, 2, POTATO), (6, 9, 2, ROAST), (9.5, 9, 1.5, MUSH_TAN)])


def beetroot_soup():
    stew("beetroot_soup", RED_SOUP, [(6, 6, 1.5, CREAM), (9, 8.5, 1.2, VINE)])


def suspicious_stew():
    stew("suspicious_stew", BROTH, [(6.5, 6.5, 2, ["8a1018", "d02a30", "f06a6a"]), (8.25, 7.25, 0.75, BUTTER),
                                    (9.5, 9, 1.5, MUSH_TAN)])


def honey_bottle():
    m = Model("honey_bottle")
    glass = Mat(GLASS, base=1.6, kind="glass", alpha=70, bevel=0.6)
    honey = Mat(HONEY, base=3.2, bevel=0.5)

    def surface(k, ii, jj, w, h, face):
        return np.where((ii == 1) & (jj == 1), k + 2, k + 1.2) if face == "up" else k

    m.box((5, 0.5, 5), (11, 6, 11), honey, decal=surface, ao=False)       # honey, nearly full
    m.box((4.5, 0, 4.5), (11.5, 7, 11.5), glass, ao=False)
    m.box((5.5, 7, 5.5), (10.5, 8, 10.5), glass, ao=False)
    m.box((6.5, 8, 6.5), (9.5, 10.5, 9.5), glass, ao=False)
    m.box((6, 10.5, 6), (10, 11.5, 10), glass, ao=False)
    m.box((6.5, 10.5, 6.5), (9.5, 11, 9.5), honey)                         # a little honey on the lip...
    m.box((6, 9, 9.75), (6.75, 11, 10.25), honey)                          # ...running down the neck
    m.write(upright(0.34, 5.0), translucent=True)


FOOD = {f.__name__: f for f in (
    apple, golden_apple, enchanted_golden_apple, carrot, golden_carrot, potato, baked_potato, poisonous_potato,
    beetroot, melon_slice, sweet_berries, glow_berries, chorus_fruit, bread, cookie, pumpkin_pie, beef, cooked_beef,
    porkchop, cooked_porkchop, mutton, cooked_mutton, rabbit, cooked_rabbit, chicken, cooked_chicken, rotten_flesh,
    spider_eye, dried_kelp, cod, cooked_cod, salmon, cooked_salmon, tropical_fish, pufferfish, mushroom_stew,
    rabbit_stew, beetroot_soup, suspicious_stew, honey_bottle)}
