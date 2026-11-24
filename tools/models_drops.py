#!/usr/bin/env python3
"""Batch 5 of Lifelike Motion's 3D items: mob drops and crafting bits (built with tools/models.py's parts and painter;
run tools/models.py to write them). Long things (a stick, a bone, arrows) are held like tools; the rest are held up
facing you."""
import numpy as np

from models import Mat, Model, upright, blade_held, WOOD, STRING, GOLD, TINTED
from models_food import blob, spots, shine, chain, stripes, BOWL, STRAW, VINE, EYE_DARK

STICK = ["3a2610", "5a3d1c", "7a5428", "966a35", "b0844a"]
BONE = ["8e8676", "b4ab98", "d4ccba", "ece6d8", "fbf8f0"]
FEATHER = ["9a9690", "bebab4", "dcd8d2", "f0ede8", "ffffff"]
QUILL = ["8a7a5a", "b09e7a", "d8c8a4"]
LEATHER_HIDE = ["3e2010", "5e3218", "7e4622", "9c5c2e", "b8763e", "d0925a"]
RABBIT = ["6a5038", "8e6e4e", "b08e6a", "ccac88", "e2c8a8", "f4e4cc"]
INK = ["06060a", "101018", "1c1c28", "2c2c3e", "464660", "7a7aa0"]
GLOW_INK = ["063a3a", "0a5a58", "10847c", "1ab4a4", "4ee2cc", "a8fff0"]
HONEYCOMB = ["7a4404", "a86408", "d68a12", "f2ae2a", "fccc58", "ffe8a0"]
HONEY = ["7a3c04", "a85806", "d6800e", "f0a420", "fcc448", "ffe28a"]
SCUTE = ["1a3e14", "28581c", "3a7a28", "549c38", "7cbc52", "a8dc7a"]
SHULKER = ["2a1a34", "44284e", "623c6e", "80548e", "a072ae", "c49cd0"]
NAUTILUS = ["6a5440", "8e7458", "b09878", "ccb898", "e4d6bc", "f8f0e2"]
NAUTILUS_STRIPE = ["6a2a14", "8e3a1c", "b04e28"]
MEMBRANE = ["5a5e4a", "7a7e66", "9ca084", "bcc0a4", "d8dcc4", "f0f2e4"]
TEAR = ["5a7a86", "86a6b2", "b4d2dc", "dcf0f6", "f6feff", "ffffff"]
PAPER = ["a8a294", "cac4b6", "e2ddd2", "f2efe8", "fdfcf8"]
WHEAT = ["7a5a1a", "a07a28", "c49c3a", "dcb850", "eed27a", "faeab0"]
EGG = ["a88a64", "c8a880", "e0c8a2", "f0e0c4", "fbf2e2"]
SNOW = ["a6b8cc", "c4d4e4", "dde8f2", "eef5fb", "ffffff"]
FLINT_HEAD = ["101012", "1c1c20", "2c2c32", "40404a", "5c5c68", "8a8a98"]
SPECTRAL = ["8a5a04", "c08a0a", "eab41a", "fcd640", "fff090", "fffbe0"]
FIRE = ["1a0a04", "3a1406", "6a2208", "b0400c", "f07818", "ffb840", "fff0b0"]
PALE_WOOD = ["5a4024", "7a5a34", "9c7a4a", "bc9a62", "d6b87e", "ecd4a0"]
CANE = ["2a4a14", "3e6a1e", "56902a", "74b23a", "9ad25a", "c8f088"]

HELD = dict(scale=0.42, lift=7.0)


def blade(name, build, turn=45, held=None):
    """a long thing standing up in the model, held like a tool (or as given)"""
    m = Model(name)
    build(m)
    m.write(held or blade_held(turn, 0.34, 2.0))


# ---------------------------------------------------------------- long things
def stick():
    """a real stick off a tree: a branch with a slight crook, tapering as it goes up, in rough bark with a bark-peeled
    patch, a knot, pale freshly broken ends showing their rings, a side twig with two leaves, and a snapped-off stub"""
    def b(m):
        bark = Mat(STICK, base=2.3, kind="wood", bevel=0.5)
        pale = Mat(PALE_WOOD, base=3.0, bevel=0.3)
        dark = Mat(STICK, base=0.9, bevel=0.3)

        def peeled(k, ii, jj, w, h, face):
            if face == "south" and h >= 5:
                k = np.where((jj >= 1) & (jj <= 3) & (ii >= 1), 4.0, k)          # a patch where the bark came off
            return k

        def rings(k, ii, jj, w, h, face):
            if face in ("up", "down"):
                ring = (ii == 0) | (jj == 0) | (ii == w - 1) | (jj == h - 1)
                k = np.where(ring, 0.8, k)                                        # the bark round the edge
                k = np.where((np.abs(ii - (w - 1) / 2) < 0.6) & (np.abs(jj - (h - 1) / 2) < 0.6), 1.6, k)
            return k
        # the branch: three lengths, each a little thinner and set a little off the last, for a gentle crook
        m.box((7.15, 0, 7.15), (8.85, 5.6, 8.85), bark)
        m.box((7.45, 5.2, 7.25), (9.05, 10.8, 8.75), bark, decal=peeled)
        m.box((7.3, 10.4, 7.35), (8.7, 15.2, 8.65), bark)
        m.box((7.15, -0.3, 7.15), (8.85, 0, 8.85), pale, decal=rings, ao=False)          # broken ends, pale wood
        m.box((7.3, 15.2, 7.35), (8.7, 15.5, 8.65), pale, decal=rings, ao=False)
        m.box((6.8, 3.0, 7.55), (7.15, 4.2, 8.45), dark, ao=False)                       # a knot
        m.box((6.65, 3.3, 7.75), (6.8, 3.9, 8.25), pale, ao=False)
        # a side twig reaching up and out, with two leaves at its end
        tw = (-45, "z", (8.9, 8.2, 8.0))
        m.box((8.45, 8.2, 7.6), (9.35, 12.6, 8.4), bark, rot=tw)
        leaf = Mat(VINE, base=2.6, bevel=0.3)
        vein = lambda k, ii, jj, w, h, face: np.where(ii == w // 2, k - 0.9, k)
        m.box((11.6, 10.9, 7.75), (12.8, 13.9, 8.25), leaf, rot=(-22.5, "z", (12.2, 10.9, 8.0)), decal=vein, ao=False)
        m.box((11.9, 10.4, 7.8), (13.0, 12.8, 8.2), leaf, rot=(-45, "z", (12.4, 10.4, 8.0)), decal=vein, ao=False)
        # a snapped-off stub on the other side, its end pale
        st = (45, "z", (7.4, 12.0, 8.0))
        m.box((7.05, 12.0, 7.65), (7.75, 14.2, 8.35), bark, rot=st)
        m.box((7.05, 14.2, 7.65), (7.75, 14.45, 8.35), pale, rot=st, ao=False)
    blade("stick", b)


def bone():
    def b(m):
        bn = Mat(BONE, base=2.6, bevel=0.7)
        m.box((7, 2.5, 7), (9, 13.5, 9), bn)
        for y in (0, 13.5):                                               # the knobbly ends
            m.box((5.5, y, 6.75), (8, y + 2.5, 9.25), bn, decal=shine)
            m.box((8, y, 6.75), (10.5, y + 2.5, 9.25), bn, decal=shine)
    blade("bone", b)


def arrow_like(name, head_mat, fletch_mat, glow=False):
    def b(m):
        shaft = Mat(STICK, base=3.0, kind="wood", bevel=0.5)
        m.box((7.5, 0, 7.5), (8.5, 13.5, 8.5), shaft)
        m.box((7, 13.5, 7), (9, 14.5, 9), head_mat)                       # the head
        m.box((7.25, 14.5, 7.25), (8.75, 15.5, 8.75), head_mat)
        m.box((7.6, 15.5, 7.6), (8.4, 16.5, 8.4), head_mat)
        m.box((6, 13, 7.75), (10, 14, 8.25), head_mat)                     # barbs
        m.box((6, 1, 7.85), (7.5, 5, 8.15), fletch_mat), m.box((8.5, 1, 7.85), (10, 5, 8.15), fletch_mat)
        m.box((7.85, 1, 6), (8.15, 5, 7.5), fletch_mat), m.box((7.85, 1, 8.5), (8.15, 5, 10), fletch_mat)
        m.box((7.25, 0, 7.25), (8.75, 0.75, 8.75), shaft)                  # the nock
    blade(name, b)


def arrow():
    arrow_like("arrow", Mat(FLINT_HEAD, base=3.0, kind="gem", bevel=0.6),
               Mat(FEATHER, base=2.8, bevel=0.3))


def spectral_arrow():
    arrow_like("spectral_arrow", Mat(SPECTRAL, base=3.6, kind="gem", bevel=0.4, glow=True),
               Mat(SPECTRAL, base=3.0, bevel=0.3, glow=True))


def tipped_arrow():
    """the head dipped in the potion (coloured by the game)"""
    arrow_like("tipped_arrow", Mat(TINTED, base=3.4, tint=True, bevel=0.5),
               Mat(FEATHER, base=2.8, bevel=0.3))


def sugar_cane():
    def b(m):
        c = Mat(CANE, base=3.0, bevel=0.5)
        joints = stripes(4, -1.6, faces=("north", "south", "east", "west"), offset=1)
        m.box((7, 0, 7), (9, 15, 9), c, decal=joints)
        m.box((4.5, 0, 7.25), (6, 11, 8.75), c, decal=joints)
        m.box((10, 0, 7.25), (11.5, 13, 8.75), c, decal=joints)
        leafm = Mat(VINE, base=2.6, bevel=0.3)
        m.box((9, 9, 7.75), (10, 13, 8.25), leafm, rot=(-45, "z", (9, 9, 8)), ao=False)
        m.box((6, 6, 7.75), (7, 9.5, 8.25), leafm, rot=(45, "z", (7, 6, 8)), ao=False)
    blade("sugar_cane", b, held=upright(scale=0.38, lift=5.0))


# ---------------------------------------------------------------- held up facing you
def string():
    """a hank of string looped round on itself, the end hanging loose"""
    m = Model("string")
    s = Mat(STRING, base=2.2, bevel=0.4)
    twist = stripes(2, 0.9, axis="v")
    for (a, b) in (((5, 3, 7.5), (11, 4, 8.5)), ((5, 11, 7.5), (11, 12, 8.5)), ((4, 4, 7.5), (5, 11, 8.5)),
                   ((11, 4, 7.5), (12, 11, 8.5)), ((6, 4.5, 8.5), (10, 5.25, 9.25)), ((6, 9.75, 8.5), (10, 10.5, 9.25)),
                   ((5.25, 5.25, 8.5), (6, 9.75, 9.25)), ((10, 5.25, 8.5), (10.75, 9.75, 9.25))):
        m.box(a, b, s, decal=twist)
    m.box((10.5, 0, 7.6), (11.25, 3, 8.4), s)                             # the loose end
    m.write(upright(**HELD))


def feather():
    m = Model("feather")
    vane = Mat(FEATHER, base=2.8, bevel=0.3)
    quill = Mat(QUILL, base=1.6, bevel=0.3)
    barbs = stripes(2, -0.8, axis="h", faces=("north", "south"))
    r = (22.5, "z", (8, 0, 8))
    m.box((7.6, 0, 7.75), (8.4, 15, 8.25), quill, rot=r)
    m.box((5.25, 4, 7.85), (7.6, 13, 8.15), vane, rot=r, decal=barbs)
    m.box((8.4, 3, 7.85), (10.75, 12.5, 8.15), vane, rot=r, decal=barbs)
    m.box((6.25, 13, 7.85), (7.6, 14.5, 8.15), vane, rot=r)
    m.box((8.4, 12.5, 7.85), (9.75, 14, 8.15), vane, rot=r)
    m.box((6, 2, 7.85), (7.6, 4, 8.15), Mat(FEATHER, base=3.6, bevel=0.2), rot=r)   # fluff at the base
    m.write(upright(**HELD))


def stitches(k, ii, jj, w, h, face):
    """a dashed line of stitching just inside the edge"""
    if face in ("north", "south") and w > 4 and h > 4:
        border = ((ii == 1) | (ii == w - 2) | (jj == 1) | (jj == h - 2)) & (ii >= 1) & (ii <= w - 2) & \
                 (jj >= 1) & (jj <= h - 2)
        k = np.where(border & ((ii + jj) % 2 == 0), 99, k)
    return k


def hide(name, pal, decal):
    m = Model(name)
    h = Mat(pal, base=len(pal) / 2 - 0.3, kind="organic", bevel=0.6)
    m.box((3, 2, 7.5), (13, 13, 8.75), h, decal=decal)
    m.box((2, 4, 7.6), (3, 10, 8.65), h), m.box((13, 5, 7.6), (14, 11, 8.65), h)   # the hide's ragged edges
    m.box((5, 13, 7.6), (8, 14, 8.65), h), m.box((9, 1, 7.6), (12, 2, 8.65), h)
    m.box((1, 11, 7.6), (3, 13, 8.65), h), m.box((13, 1, 7.6), (15, 3, 8.65), h)   # leg flaps
    m.write(upright(**HELD))


def leather():
    hide("leather", LEATHER_HIDE, chain(stitches, shine))


def rabbit_hide():
    hide("rabbit_hide", RABBIT, spots(0.15, 0.8, seed="fur", add=True))


def rabbit_foot():
    """a lucky rabbit's foot charm: soft fur, little toes, tied with a gold-clasped string"""
    m = Model("rabbit_foot")
    fur = Mat(RABBIT, base=3.2, kind="organic", grad=1.0)
    toe = Mat(RABBIT, base=4.2, bevel=0.4)
    m.box((6, 3, 6.5), (10, 11, 10), fur, decal=chain(spots(0.12, 0.8, seed="foot", add=True), shine))
    m.box((5.5, 3, 7), (10.5, 9, 9.5), fur)
    for x in (5.75, 7.25, 8.75):                                           # toes
        m.box((x, 1, 7.75), (x + 1.5, 3, 10.25), toe)
    m.box((6.5, 11, 7), (9.5, 12, 9.5), Mat(GOLD, base=3, kind="metal", bevel=0.5))   # a gold clasp
    m.box((7.5, 12, 8), (8.5, 15, 8.75), Mat(STRING, base=2, bevel=0.3))
    m.write(upright(**HELD))


def ink(name, pal, glow=False):
    m = Model(name)
    s = Mat(pal, base=3.0, kind="organic", grad=1.0, glow=glow)
    blob(m, (4, 3, 4.5), (12, 11, 11.5), s, decal=shine)
    m.box((7, 11, 7), (9, 12.5, 9), s)                                     # the knot at the top
    m.box((6.5, 12.5, 6.5), (9.5, 13.25, 9.5), s)
    m.box((6, 1, 9), (7, 3, 10), s), m.box((6.25, 0, 9.25), (6.75, 1, 9.75), s)   # a drip
    m.write(upright(**HELD))


def ink_sac():
    ink("ink_sac", INK)


def glow_ink_sac():
    ink("glow_ink_sac", GLOW_INK, glow=True)


def honeycomb():
    m = Model("honeycomb")
    c = Mat(HONEYCOMB, base=3.0, bevel=0.6)
    honey = Mat(HONEY, base=3.6, bevel=0.4)

    def cells(k, ii, jj, w, h, face):
        if face in ("north", "south"):
            row = jj // 3
            col = (ii + (row % 2) * 2) // 4
            cx = col * 4 + 1.5 - (row % 2) * 2
            cy = row * 3 + 1
            inside = (np.abs(ii - cx) <= 1) & (np.abs(jj - cy) <= 0.5)
            k = np.where(inside, k - 1.8, k + 0.6)                         # dark cell holes, light walls
        return k

    m.box((2.5, 2, 6.5), (13.5, 12, 9.5), c, decal=cells)
    m.box((3.5, 1, 6.75), (12.5, 13, 9.25), c, decal=cells)
    m.box((5, 0, 9.5), (6, 2, 10), honey), m.box((10, 0.5, 9.5), (11, 2, 10), honey)   # honey dripping
    m.box((5, 2, 9.5), (6.5, 3, 10), honey)
    m.write(upright(**HELD))


def scute():
    m = Model("scute")
    s = Mat(SCUTE, base=3.0, bevel=0.7)
    ridge = Mat(SCUTE, base=4.2, bevel=0.5)
    m.box((3, 3, 7.25), (13, 12, 8.75), s, decal=shine)
    m.box((4, 2, 7.4), (12, 13, 8.6), s)
    m.box((7, 3, 8.75), (9, 12, 9.5), ridge)                               # the ridge down the middle
    m.box((4, 7, 8.75), (12, 8, 9.25), ridge)
    m.write(upright(**HELD))


def shulker_shell():
    m = Model("shulker_shell")
    s = Mat(SHULKER, base=3.0, bevel=0.7)
    inside = Mat(SHULKER, base=1.0, bevel=0.2)
    m.box((3, 1, 3), (13, 7, 13), s, faces=("north", "south", "east", "west", "up"), decal=shine)
    m.box((4, 7, 4), (12, 9, 12), s, decal=shine)
    m.box((5.5, 9, 5.5), (10.5, 10, 10.5), s, decal=shine)                 # the domed top
    m.box((2.75, 1, 2.75), (13.25, 2, 13.25), Mat(SHULKER, base=4.4, bevel=0.5),
          faces=("north", "south", "east", "west", "up"))                    # a lighter lip round the rim
    m.box((4, 1.5, 4), (12, 7, 12), inside, faces=("down",), ao=False)
    m.box((3, 1, 3), (13, 1.5, 13), s, faces=("down",))
    m.write(upright(scale=0.4, lift=6.0, tilt=25))


def nautilus_shell():
    """a spiralling shell: chambers winding inward, banded in brown"""
    m = Model("nautilus_shell")
    s = Mat(NAUTILUS, base=3.2, bevel=0.6)
    def spiral(k, ii, jj, w, h, face):
        # brown bands winding in toward the middle of the shell
        if face in ("north", "south"):
            cx, cy = w * 0.42, h * 0.5
            ang = np.arctan2(jj - cy, ii - cx)
            r = np.hypot(ii - cx, jj - cy)
            k = np.where(((r + ang * 0.6) % 3) < 1.0, k - 2.0, k)
        return k

    m.box((3, 2, 6.5), (12, 11, 9.5), s, decal=chain(spiral, shine))
    m.box((2, 3, 6.75), (13, 10, 9.25), s, decal=spiral)
    m.box((4, 1, 6.75), (11, 12, 9.25), s, decal=spiral)
    m.box((11, 6, 6.25), (14, 11, 9.75), s)                                # the open mouth
    m.box((11.5, 7, 9.75), (13.5, 10, 9.9), Mat(NAUTILUS_STRIPE, base=0.5, bevel=0), faces=("south",))
    m.write(upright(**HELD))


def phantom_membrane():
    m = Model("phantom_membrane")
    mem = Mat(MEMBRANE, base=2.6, bevel=0.5, alpha=200)
    bone_m = Mat(MEMBRANE, base=4.6, bevel=0.3)
    m.box((3, 3, 7.75), (13, 13, 8.25), mem, decal=spots(0.08, -1.2, seed="mem", add=True))
    m.box((2, 6, 7.8), (3, 11, 8.2), mem), m.box((13, 4, 7.8), (14, 9, 8.2), mem)
    m.box((7.5, 3, 7.6), (8.5, 14, 8.4), bone_m)                           # a wing bone through it
    m.box((4, 9, 7.6), (7.5, 10, 8.4), bone_m)
    m.write(upright(**HELD), translucent=True)


def ghast_tear():
    m = Model("ghast_tear")
    t = Mat(TEAR, base=3.2, kind="gem", bevel=0.5, glow=True)
    m.box((5, 1, 5), (11, 6, 11), t, decal=shine)
    m.box((5.75, 6, 5.75), (10.25, 8, 10.25), t)
    m.box((6.5, 8, 6.5), (9.5, 10, 9.5), t)
    m.box((7.25, 10, 7.25), (8.75, 12, 8.75), t)
    m.box((7.6, 12, 7.6), (8.4, 13, 8.4), t)
    m.write(upright(**HELD))


def paper():
    m = Model("paper")
    p = Mat(PAPER, base=3.0, bevel=0.4)
    lines = stripes(2, -0.7, axis="h", faces=("south",))
    m.box((3.5, 1, 7.6), (12.5, 14, 8.1), p, decal=lines)
    m.box((3.5, 0, 7.9), (12.5, 1, 8.9), p)                                # the curled bottom edge
    m.box((3.5, 14, 7.2), (12.5, 15, 7.7), p)                              # and top
    m.write(upright(**HELD))


def wheat():
    """a sheaf of wheat tied with straw"""
    m = Model("wheat")
    stalk = Mat(WHEAT, base=2.4, bevel=0.3)
    ear = Mat(WHEAT, base=3.8, bevel=0.6)
    grains = stripes(2, -1.0, axis="h")
    for (x, z, h, rot) in ((7.5, 7.5, 9, None), (6, 7.25, 8, (22.5, "z", (6.5, 2, 8))),
                           (9, 7.25, 8, (-22.5, "z", (9.5, 2, 8))), (7.5, 9, 8.5, (-22.5, "x", (8, 2, 9.5))),
                           (7.5, 6, 8.5, (22.5, "x", (8, 2, 6.5)))):
        m.box((x, 0, z), (x + 1, h, z + 1), stalk, rot=rot)
        m.box((x - 0.25, h, z - 0.25), (x + 1.25, h + 4, z + 1.25), ear, rot=rot, decal=grains)
    m.box((6.5, 3, 6.5), (9.5, 4.5, 9.5), Mat(STRAW, base=1.6, bevel=0.5))   # the tie
    m.write(upright(**HELD))


def egg():
    m = Model("egg")
    e = Mat(EGG, base=3.2, kind="organic", grad=1.0)
    speck = spots(0.08, -1.4, seed="egg", add=True)
    blob(m, (4.5, 0, 4.5), (11.5, 9, 11.5), e, decal=chain(speck, shine))
    m.box((5.5, 8, 5.5), (10.5, 10.5, 10.5), e, decal=speck)               # narrowing to the top
    m.box((6.5, 10.5, 6.5), (9.5, 11.5, 9.5), e)
    m.write(upright(**HELD))


def snowball():
    m = Model("snowball")
    s = Mat(SNOW, base=2.8, kind="organic", grad=1.0)
    blob(m, (4, 2, 4), (12, 10, 12), s, decal=chain(spots(0.07, 99, seed="snow"), shine))
    m.box((10, 6.5, 6.5), (12.5, 8.5, 8.5), s)                             # a clump
    m.write(upright(**HELD))


def fire_charge():
    m = Model("fire_charge")
    c = Mat(FIRE, base=3.0, bevel=0.4, glow=True)

    def cracks(k, ii, jj, w, h, face):
        return np.where(((ii * 2 + jj * 3) % 7 < 2) | ((ii - jj) % 5 == 0), k + 2.2, k - 1.4)

    blob(m, (4, 2, 4), (12, 10, 12), c, decal=cracks)
    m.write(upright(**HELD))


def bowl():
    m = Model("bowl")
    b = Mat(BOWL, base=3.0, kind="wood", bevel=0.6)
    inner = Mat(BOWL, base=1.4, kind="wood", bevel=0.2)
    sides = ("north", "south", "east", "west", "down")
    m.box((5.5, 0, 5.5), (10.5, 1, 10.5), b)
    m.box((4.5, 1, 4.5), (11.5, 2, 11.5), b, faces=sides)
    m.box((3.5, 2, 4.5), (12.5, 4.5, 11.5), b, faces=sides)
    m.box((4.5, 2, 3.5), (11.5, 4.5, 12.5), b, faces=sides)
    m.box((4, 1.5, 4), (12, 2, 12), inner, faces=("up",), ao=False)        # the inside: floor and walls
    m.box((4.5, 2, 4.5), (11.5, 4.5, 5), inner, faces=("south",), ao=False)
    m.box((4.5, 2, 11), (11.5, 4.5, 11.5), inner, faces=("north",), ao=False)
    m.box((4, 2, 5), (4.5, 4.5, 11), inner, faces=("east",), ao=False)
    m.box((11.5, 2, 5), (12, 4.5, 11), inner, faces=("west",), ao=False)
    for (a, c) in (((4.5, 4, 3), (11.5, 5, 4)), ((4.5, 4, 12), (11.5, 5, 13)), ((3, 4, 4.5), (4, 5, 11.5)),
                   ((12, 4, 4.5), (13, 5, 11.5)), ((3.5, 4, 3.5), (4.5, 5, 4.5)), ((11.5, 4, 3.5), (12.5, 5, 4.5)),
                   ((3.5, 4, 11.5), (4.5, 5, 12.5)), ((11.5, 4, 11.5), (12.5, 5, 12.5))):
        m.box(a, c, b)
    m.write(upright(0.38, 5.0, tilt=42))


DROPS = {f.__name__: f for f in (
    stick, bone, string, feather, leather, rabbit_hide, rabbit_foot, ink_sac, glow_ink_sac, honeycomb, scute,
    shulker_shell, nautilus_shell, phantom_membrane, ghast_tear, paper, wheat, egg, snowball, arrow, spectral_arrow,
    tipped_arrow, fire_charge, bowl, sugar_cane)}
