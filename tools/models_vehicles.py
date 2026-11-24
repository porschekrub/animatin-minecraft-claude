#!/usr/bin/env python3
"""Batch 8 of Lifelike Motion's 3D items: boats and rafts (with and without a chest), minecarts (plain and with
what they carry) and horse armour (built with tools/models.py's parts and painter; run tools/models.py to write
them). All are held up in front of you, tipped so you can see inside."""
import numpy as np

from models import Mat, Model, upright, IRON, GOLD, DIAMOND, TINTED
from models_food import shine, stripes, chain
from models_drops import STICK, STRING
from models_special import SADDLE

# wood, dark to light (picked from the game's own planks, stretched a little for light and shade)
WOODS = {
    "oak": ["4a3518", "6b4f2a", "8f6e3e", "a8844e", "bc995e", "d2b276"],
    "spruce": ["2e1e0e", "45301a", "5e4224", "70522e", "86653a", "9c7a4a"],
    "birch": ["6e5e3a", "988656", "b4a270", "c8b77a", "dccb8e", "ece0aa"],
    "jungle": ["4a2e1c", "6e4a30", "93653f", "aa7954", "c08d68", "d6a684"],
    "acacia": ["5a2a14", "7e3c20", "9c4e2a", "ad5d32", "c46c3c", "d8865a"],
    "dark_oak": ["170e05", "24170a", "33220f", "432d15", "553a1c", "6a4a26"],
    "mangrove": ["3a0e10", "561c1e", "6f2a2d", "7f3836", "92483e", "a85e50"],
    "cherry": ["9a5856", "c27c78", "d8a09a", "e6b3ad", "eec6c0", "f8dcd6"],
    "bamboo": ["6a5a22", "8e7c34", "b4a046", "c8b14d", "dcc65e", "eedc7e"],
}
CHEST = ["24180a", "3e2a12", "5e401c", "7e5626", "9e6e30", "be8a40"]
CART = ["1a1e22", "262c31", "343c43", "48525a", "66727a", "8e9aa2", "c0c8ce"]
STONE_P = ["1e1e20", "2e2e31", "424246", "5a5a5e", "75757a", "96969a"]
FIRE_GLOW = ["6a1a04", "b03a08", "f07018", "ffa83a", "ffd880", "fff4d0"]
TNT = ["3a0406", "6a0a0e", "9a1418", "c42024", "e03a34", "f06a5a"]
TNT_BAND = ["8a8486", "b0aaac", "cfcacb", "e4e0e0", "f6f4f4"]
COMMAND = ["4a2c16", "6e4228", "945c3a", "b87650", "d09470", "e6b494", "f6d8c0"]
COMMAND_PANEL = ["2a2a34", "3e3e4a", "565664", "727282", "9494a4", "c0c0ce"]
RUBY_PLUME = ["3a0608", "640c10", "9a1418", "c82424", "e84a3e", "fa8a6a"]
HORSE_LEATHER = ["2a1408", "44220e", "613416", "7e4820"]

HELD = dict(scale=0.4, lift=6.0, tilt=28)


def rivets(k, ii, jj, w, h, face):
    """small round rivets near the corners of the bigger faces"""
    if w >= 5 and h >= 4:
        dots = np.isin(ii, (1, w - 2)) & np.isin(jj, (1, h - 2))
        k = np.where(dots, k + 1.6, k)
    return k


def seams(k, ii, jj, w, h, face):
    """the lines between planks along a hull's side"""
    if face not in ("up", "down") and h >= 3:
        k = np.where(jj % 2 == 1, k - 0.7, k)
    return k


def boards(k, ii, jj, w, h, face):
    """floor boards: lines across the top"""
    if face == "up" and h >= 3:
        k = np.where(jj % 2 == 1, k - 0.9, k)
    return k


def nodes(k, ii, jj, w, h, face):
    """bamboo: a dark ring every few pixels along the pole"""
    if face in ("up", "down", "north", "south"):
        k = np.where(ii % 4 == 3, k - 1.4, k)
    return k


# ---------------------------------------------------------------- chests (on boats and in carts)
def small_chest(m, x0, y0, z0, x1, y1, z1, latch_face="east"):
    """a wooden chest: body, a lid with a darker band, and an iron latch on one side"""
    body = Mat(CHEST, base=3.0, kind="wood", bevel=0.6)
    band = Mat(CHEST, base=1.4, kind="wood", bevel=0.4)
    iron = Mat(IRON, base=3.6, kind="metal", bevel=0.3)
    lid = y0 + (y1 - y0) * 0.68
    m.box((x0, y0, z0), (x1, lid, z1), body)
    m.box((x0 - 0.1, lid, z0 - 0.1), (x1 + 0.1, lid + 0.5, z1 + 0.1), band)          # the lid's rim
    m.box((x0, lid + 0.5, z0), (x1, y1, z1), body, decal=shine)
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    if latch_face == "east":
        m.box((x1, lid - 1.0, cz - 0.5), (x1 + 0.4, lid + 0.8, cz + 0.5), iron, ao=False)
    else:   # south
        m.box((cx - 0.5, lid - 1.0, z1), (cx + 0.5, lid + 0.8, z1 + 0.4), iron, ao=False)


# ---------------------------------------------------------------- boats
def boat_like(name, wood, chest=False):
    """a rowboat: a plank hull with a pointed, rising bow, darker gunwales, a seat, iron oarlocks and two oars
    resting in them"""
    pal = WOODS[wood]
    m = Model(name)
    w = Mat(pal, base=3.0, bevel=0.6)
    rim = Mat(pal, base=1.6, kind="wood", bevel=0.5)
    oar = Mat(STICK, base=2.6, kind="wood", bevel=0.4)
    blade = Mat(pal, base=3.6, kind="wood", bevel=0.4)
    iron = Mat(IRON, base=3.0, kind="metal", bevel=0.3)
    m.box((1.5, -0.4, 7.5), (16.5, 0, 8.5), rim)                                   # keel
    m.box((2, 0, 5.5), (13, 1, 10.5), w, decal=boards)                              # bottom
    m.box((2, 1, 4.5), (13, 4, 5.5), w, decal=seams)                                # sides
    m.box((2, 1, 10.5), (13, 4, 11.5), w, decal=seams)
    m.box((1, 0.5, 4.5), (2, 4.5, 11.5), w, decal=seams)                            # stern
    d = 3.5 / 2 ** 0.5                                                              # the bow: a square turned
    m.box((13 - d, 0.3, 8 - d), (13 + d, 4.0, 8 + d), w, rot=(45, "y", (13, 0.3, 8)), decal=seams)   # to a point
    e = 3.75 / 2 ** 0.5
    m.box((13 - e, 3.95, 8 - e), (13 + e, 4.45, 8 + e), rim, rot=(45, "y", (13, 3.95, 8)))  # its deck
    m.box((16.1, 0.6, 7.4), (17.1, 5.6, 8.6), rim)                                  # stem post
    m.box((2, 4, 4.25), (13, 4.6, 5.75), rim)                                       # gunwales
    m.box((2, 4, 10.25), (13, 4.6, 11.75), rim)
    m.box((0.75, 4.5, 4.2), (2.25, 5.0, 11.8), rim)                                 # stern rail
    m.box((7.5, 2.6, 5.5), (9.5, 3.2, 10.5), rim)                                   # the seat
    for z0, z1 in ((4.4, 5.6), (10.4, 11.6)):                                       # oarlocks
        m.box((8.1, 4.6, z0), (8.9, 5.2, z1), iron, ao=False)
    for zs in (3.3, 12.1):                                                          # oars, blades dipping astern
        rot = (22.5, "z", (8.5, 4.9, zs + 0.3))
        m.box((3.5, 4.6, zs), (13, 5.2, zs + 0.6), oar, rot=rot, ao=False)
        m.box((13, 4.5, zs - 0.05), (14, 5.3, zs + 0.65), rim, rot=rot, ao=False)    # the handle's grip
        m.box((0.5, 4.0, zs + 0.05), (3.5, 5.8, zs + 0.55), blade, rot=rot, ao=False)
    if chest:
        small_chest(m, 2.4, 1, 6, 6.8, 5.8, 10)
    m.write(upright(**HELD), particle=f"minecraft:block/{wood}_planks")


def raft_like(name, chest=False):
    """a bamboo raft: a deck of poles tied to cross logs, a raised log across the front, and a paddle lying on it"""
    pal = WOODS["bamboo"]
    m = Model(name)
    tie = Mat(STRING, base=2.0, kind="wrap", bevel=0.3)
    for n, z in enumerate((4.3, 5.7, 7.1, 8.5, 9.9, 11.3)):                         # the deck's poles
        pole = Mat(pal, base=2.8 + 0.5 * (n % 2), bevel=0.5)
        m.box((1, 0.6, z), (15, 2.0, z + 1.4), pole, decal=nodes)
    log = Mat(pal, base=2.2, bevel=0.6)
    m.box((2.5, -0.2, 4), (4, 0.6, 13), log)                                          # cross logs underneath
    m.box((11.5, -0.2, 4), (13, 0.6, 13), log)
    m.box((14.2, 2.0, 3.8), (16, 3.8, 13.2), log, decal=nodes)                       # the raised front log
    m.box((0.6, 2.0, 3.8), (1.8, 3.0, 13.2), log)                                    # and a lower one behind
    for x in (14.6, 1.0):
        for z in (4.6, 12.0):
            m.box((x, 1.8, z), (x + 1.2, 3.2 if x > 10 else 2.6, z + 0.6), tie, ao=False)   # lashings
    oar = Mat(STICK, base=2.6, kind="wood", bevel=0.4)
    blade = Mat(pal, base=3.8, bevel=0.4)
    rot = (22.5, "y", (8, 2.3, 8))
    m.box((5, 2.0, 9.0), (13, 2.6, 9.6), oar, rot=rot, ao=False)
    m.box((2.2, 2.0, 8.4), (5, 2.5, 10.2), blade, rot=rot, ao=False)
    if chest:
        small_chest(m, 2.4, 2.0, 5.2, 7.2, 6.8, 9.8)
    m.write(upright(**HELD), particle="minecraft:block/bamboo_planks")


def make_boats():
    out = {}
    for wood in WOODS:
        if wood == "bamboo":
            out["bamboo_raft"] = lambda: raft_like("bamboo_raft")
            out["bamboo_chest_raft"] = lambda: raft_like("bamboo_chest_raft", chest=True)
        else:
            out[f"{wood}_boat"] = lambda wood=wood: boat_like(f"{wood}_boat", wood)
            out[f"{wood}_chest_boat"] = lambda wood=wood: boat_like(f"{wood}_chest_boat", wood, chest=True)
    return out


# ---------------------------------------------------------------- minecarts
def cart(m):
    """the iron tub: floor, riveted sides, a heavier rim round the top, and four wheels on axles"""
    body = Mat(CART, base=3.4, kind="metal", bevel=0.7, shine=0.5)
    dark = Mat(CART, base=1.6, kind="metal", bevel=0.4, shine=0.3)
    rim = Mat(CART, base=4.4, kind="metal", bevel=0.5)
    m.box((2.5, 1.5, 4.5), (13.5, 2.5, 11.5), dark)                                  # floor
    m.box((2, 1.5, 4), (3, 7, 12), body, decal=rivets)                                # ends
    m.box((13, 1.5, 4), (14, 7, 12), body, decal=rivets)
    m.box((3, 1.5, 4), (13, 7, 5), body, decal=rivets)                                # sides
    m.box((3, 1.5, 11), (13, 7, 12), body, decal=rivets)
    m.box((1.75, 7, 3.75), (14.25, 7.5, 5.0), rim)                                    # the rim
    m.box((1.75, 7, 11.0), (14.25, 7.5, 12.25), rim)
    m.box((1.75, 7, 5.0), (3.0, 7.5, 11.0), rim)
    m.box((13.0, 7, 5.0), (14.25, 7.5, 11.0), rim)
    m.box((1.8, 3.0, 3.8), (14.2, 3.6, 12.2), dark)                                   # a band round the middle
    for x in (4, 12):                                                                 # wheels on their axles
        m.box((x - 0.5, 0.75, 3.2), (x + 0.5, 1.75, 12.8), dark)
        for z0, z1 in ((3.2, 3.9), (12.1, 12.8)):
            m.box((x - 0.75, -0.25, z0), (x + 0.75, 2.75, z1), dark)
            m.box((x - 1.25, 0.25, z0 + 0.1), (x + 1.25, 2.25, z1 - 0.1), dark)
            m.box((x - 0.35, 0.9, z0 - 0.1), (x + 0.35, 1.6, z1 + 0.1), rim, ao=False)   # hub


def minecart_like(name, load=None, unlit=False):
    """unlit: the glowing bits (fire, a lit fuse) keep their full colour from every side"""
    m = Model(name)
    cart(m)
    if load:
        load(m)
    m.write(upright(**HELD), particle="minecraft:item/" + name, unlit=unlit)


def furnace_load(m):
    """a furnace with fire glowing through its grate and a little chimney"""
    stone = Mat(STONE_P, base=3.0, bevel=0.7)
    fire = Mat(FIRE_GLOW, base=3.4, bevel=0.3, glow=True, shade=False)
    iron = Mat(CART, base=2.4, kind="metal", bevel=0.4)
    m.box((3.5, 4.5, 5.2), (12.5, 11.5, 10.8), stone, decal=chain(stripes(3, -0.8), shine))
    m.box((5, 7.6, 10.8), (11, 10.4, 11.1), iron)                                     # the grate's frame
    m.box((5.6, 8.0, 10.9), (10.4, 10.0, 11.2), fire, decal=stripes(2, -1.6, axis="v"), ao=False)
    m.box((9, 11.5, 6.2), (11, 14, 8.2), iron, decal=stripes(2, 0.8))                  # chimney
    m.box((8.6, 14, 5.8), (11.4, 14.6, 8.6), Mat(CART, base=4.2, kind="metal", bevel=0.4))


def chest_load(m):
    small_chest(m, 3.6, 4.0, 5.4, 12.4, 11.5, 10.6, latch_face="south")


def hopper_load(m):
    """a hopper's open funnel sitting in the cart"""
    iron = Mat(STONE_P, base=2.6, kind="metal", bevel=0.6)
    inside = Mat(STONE_P, base=0.6, bevel=0.2)
    m.box((3.25, 7.5, 5.0), (12.75, 9.5, 6.25), iron)
    m.box((3.25, 7.5, 9.75), (12.75, 9.5, 11.0), iron)
    m.box((3.25, 7.5, 6.25), (4.5, 9.5, 9.75), iron)
    m.box((11.5, 7.5, 6.25), (12.75, 9.5, 9.75), iron)
    m.box((4.5, 7.0, 6.25), (11.5, 8.0, 9.75), inside)                                 # the dark funnel inside
    m.box((5, 2.5, 5.5), (11, 7.5, 10.5), iron)


def tnt_load(m):
    """a block of TNT: red, with a pale paper band and a fuse"""
    red = Mat(TNT, base=3.0, bevel=0.7)
    band = Mat(TNT_BAND, base=2.6, bevel=0.4)
    m.box((4.5, 4.5, 5.2), (11.5, 11.5, 10.8), red, decal=stripes(2, -1.2, axis="v"))
    m.box((4.4, 8.0, 5.1), (11.6, 10.0, 10.9), band,
          decal=lambda k, ii, jj, w, h, face: np.where((face != "up") & (face != "down") & (ii % 3 != 2)
                                                       & (jj == 1), 0, k))      # the dark letters on the band
    m.box((7.6, 11.5, 7.6), (8.4, 12.8, 8.4), Mat(["1a1a1a", "3a3a3a", "5a5a5a"], base=1.0, bevel=0.2), ao=False)
    m.box((7.7, 12.8, 7.7), (8.3, 13.3, 8.3), Mat(FIRE_GLOW, base=4, bevel=0, glow=True, shade=False), ao=False)


def command_load(m):
    """a command block: warm brown with a dark panel and an arrow on its face"""
    shell = Mat(COMMAND, base=3.2, bevel=0.8)
    panel = Mat(COMMAND_PANEL, base=2.4, bevel=0.4)
    m.box((4.5, 4.5, 5.2), (11.5, 11.5, 10.8), shell, decal=stripes(3, -0.9))
    m.box((5.5, 7.8, 10.8), (10.5, 11.0, 11.0), panel,
          decal=lambda k, ii, jj, w, h, face: np.where((np.abs(ii - (w - 1) / 2) <= (jj - 0.5)) & (jj < h - 1)
                                                       & (np.abs(ii - (w - 1) / 2) >= jj - 1.5), 99, k))
    m.box((5.5, 11.5, 6.2), (10.5, 11.8, 9.8), panel)


MINECARTS = {
    "minecart": lambda: minecart_like("minecart"),
    "chest_minecart": lambda: minecart_like("chest_minecart", chest_load),
    "furnace_minecart": lambda: minecart_like("furnace_minecart", furnace_load, unlit=True),
    "hopper_minecart": lambda: minecart_like("hopper_minecart", hopper_load),
    "tnt_minecart": lambda: minecart_like("tnt_minecart", tnt_load, unlit=True),
    "command_block_minecart": lambda: minecart_like("command_block_minecart", command_load),
}


# ---------------------------------------------------------------- horse armour
def horse_armor(name, pal, base, trim_pal=None, plume=None, gem=None, tint=False):
    """a horse's head and neck armour, side on like a chess knight: a long face plate sloping down to the snout,
    with eye holes, a ridge and ear guards, and a neck guard of overlapping plates running down behind (crested
    with plumes and set with a gem on the finer ones)"""
    m = Model(name)
    plate = Mat(pal, base=base, kind="organic" if tint else "metal", bevel=0.7, tint=tint, shine=0.6)
    edge = Mat(trim_pal or pal, base=(len(trim_pal) - 2.4) if trim_pal else base + 1.0,
               kind="organic" if tint else "metal", bevel=0.4)
    dark = Mat(["0a0a0c", "16161a", "24242a"], base=0.6, bevel=0)
    strap = Mat(HORSE_LEATHER, base=1.6, kind="wrap", bevel=0.4)
    head = (-45, "z", (8, 14, 8))                       # the face plate slopes forward and down from the poll
    neck = (45, "z", (8, 14, 8))                        # the neck guard runs back and down from it
    m.box((8, 10.5, 5.5), (17, 14.5, 10.5), plate, rot=head, decal=shine)
    m.box((17, 11, 6), (19.5, 14.2, 10), plate, rot=head)                        # the snout
    m.box((9, 14.5, 7.5), (16.5, 15.1, 8.5), edge, rot=head)                     # a ridge down the face
    m.box((16.8, 10.6, 5.6), (17.4, 14.6, 10.4), edge, rot=head)                 # a rim where the snout starts
    for z in (5.35, 10.5):                                                       # eye holes
        m.box((10, 12, z), (11.6, 13.2, z + 0.15), dark, rot=head, ao=False)
    for n, (x0, x1, d) in enumerate(((-2.5, 1.5, 0.3), (1, 4.8, 0.15), (4.3, 8.3, 0))):   # overlapping neck plates
        m.box((x0, 10.6 + d, 5.6 + d), (x1, 14.5 - d, 10.4 - d), plate, rot=neck, decal=shine if n == 1 else None)
        m.box((x1 - 0.5, 10.4 + d, 5.4 + d), (x1, 14.7 - d, 10.6 - d), edge, rot=neck)
    m.box((-2.5, 14.5, 7.6), (8, 15.0, 8.4), edge, rot=neck)                      # the crest
    for z in (6.0, 9.0):                                                          # ear guards
        m.box((7.2, 14.4, z), (8.6, 16.8, z + 1.0), edge, rot=(-22.5, "z", (8, 14.4, 8)), ao=False)
    m.box((10.6, 9.6, 5.3), (11.4, 14.0, 10.7), strap, rot=head)                  # cheek strap
    if plume:
        pl = Mat(plume, base=3.0, kind="organic", bevel=0.5)
        for x in (-1.5, 1.0, 3.5, 6.0):                                           # plumes along the crest
            m.box((x, 15.0, 7.4), (x + 1.4, 17.5 - 0.15 * (6 - x), 8.6), pl, rot=neck, ao=False)
    if gem:
        m.box((11.5, 14.4, 7.3), (13, 15.3, 8.7), Mat(gem, base=len(gem) - 2.5, kind="gem", bevel=0.3, glow=True),
              rot=head, ao=False)
    m.write(upright(scale=0.42, lift=5.0, tilt=6))


HORSE_ARMOR = {
    "leather_horse_armor": lambda: horse_armor("leather_horse_armor", TINTED, 3.0, trim_pal=HORSE_LEATHER,
                                               tint=True),
    "iron_horse_armor": lambda: horse_armor("iron_horse_armor", IRON, 3.6),
    "golden_horse_armor": lambda: horse_armor("golden_horse_armor", GOLD, 2.8, plume=RUBY_PLUME),
    "diamond_horse_armor": lambda: horse_armor("diamond_horse_armor", DIAMOND, 4.2, trim_pal=GOLD,
                                               plume=["0a2a4a", "12406e", "1c5c9a", "2a7cc4", "4aa2e4", "8ad0fa"],
                                               gem=DIAMOND),
}

VEHICLES = {**make_boats(), **MINECARTS, **HORSE_ARMOR}
