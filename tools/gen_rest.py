#!/usr/bin/env python3
"""The rest of the items, built by family. Each family has one shape; its colours come from the item's own texture
(the main colours sampled from the game's picture), so every variant comes out in the right colours.

usage: gen_rest.py <pack dir> [families...]
"""
import io
import json
import math
import os
import sys
import zipfile
from collections import Counter

sys.path.insert(0, os.path.dirname(__file__))
import gen_food as G  # noqa: E402
from gen_food import Food, TINT, TINT2, ell, mix, shade, noise  # noqa: E402

PACK = sys.argv[1]
G.PACK = PACK
ONLY = set(sys.argv[2:])
Z = zipfile.ZipFile(G.JAR)
NS = "lifelikemotion"
ITEMS = os.path.join(PACK, "assets", "minecraft", "models", "item")


def vanilla(name):
    return json.loads(Z.read(f"assets/minecraft/models/item/{name}.json"))


def palette(tex, n=4):
    """the n most used opaque colours of a texture, darkest first ('minecraft:item/x' or 'item/x')"""
    p = tex.split(":")[-1]
    from PIL import Image
    im = Image.open(io.BytesIO(Z.read(f"assets/minecraft/textures/{p}.png"))).convert("RGBA")
    c = Counter(px[:3] for px in im.getdata() if px[3] > 128)
    top = [col for col, _ in c.most_common(max(n * 3, 8))]
    # spread: skip colours too close to one already taken
    out = []
    for col in top:
        if all(sum(abs(a - b) for a, b in zip(col, o)) > 40 for o in out):
            out.append(col)
        if len(out) == n:
            break
    while len(out) < n:
        out.append(out[-1] if out else (128, 128, 128))
    return sorted(out, key=lambda c: sum(c))


def item_json(name, base_model, particle, gui_parent=None, gui_textures=None, overrides=None):
    gui = {"parent": gui_parent or "minecraft:item/generated"}
    if gui_textures:
        gui["textures"] = gui_textures
    d = {"loader": "forge:separate_transforms", "textures": {"particle": particle},
         "base": {"parent": f"{NS}:item3d/{base_model}"}, "perspectives": {"gui": gui}}
    if overrides:
        d["overrides"] = overrides
    with open(os.path.join(ITEMS, name + ".json"), "w") as f:
        json.dump(d, f, separators=(",", ":"))


def build(model_name, shape, glow=None, tilt=0, **kw):
    if tilt:
        shape = G.tilt(shape, tilt)
    return Food(model_name, write_item=False).build(shape, glow or (lambda c: False), **kw)


def plain_item(name, shape, glow=None, tilt=0, **kw):
    """an item whose game model is a single picture: our shape in hand, the picture in the inventory"""
    v = vanilla(name)
    build(name, shape, glow, tilt, **kw)
    item_json(name, name, v["textures"]["layer0"], gui_textures=v["textures"], overrides=v.get("overrides"))


# ---------------------------------------------------------------- spawn eggs: one shape, coloured by the game
def egg_shape(x, y, z):
    if ell(x, y, z, 8, 7.4, 8, 3.2, 4.2 if y > 7.4 else 3.4, 3.2) < 1:
        # spots in the second colour, base in the first (both coloured by the game per mob)
        if noise(x // 1.5, y // 1.5, z // 1.5, 91) < 0.3:
            return TINT2
        return TINT
    return None


def spawn_eggs():
    build("spawn_egg", egg_shape)
    n = 0
    for f in Z.namelist():
        if f.startswith("assets/minecraft/models/item/") and f.endswith("_spawn_egg.json") and "template" not in f:
            name = f.split("/")[-1][:-5]
            item_json(name, "spawn_egg", "minecraft:item/spawn_egg", gui_parent="minecraft:item/template_spawn_egg")
            n += 1
    return n


# ---------------------------------------------------------------- armour and its trims
TRIM_COLOURS = {"quartz": (236, 230, 220), "iron": (200, 204, 210), "netherite": (80, 70, 74), "redstone": (200, 30, 30),
                "copper": (220, 120, 80), "gold": (250, 210, 70), "emerald": (40, 200, 90), "diamond": (110, 240, 230),
                "lapis": (50, 80, 200), "amethyst": (170, 110, 230)}
TIER_COLOURS = {"leather": None, "chainmail": (150, 154, 160), "iron": (220, 222, 228), "golden": (250, 210, 70),
                "diamond": (90, 230, 215), "netherite": (76, 66, 72), "turtle": (70, 170, 60)}


def armour_shape(piece, main, trim=None, chain=False):
    """main can be TINT (leather, dyed by the game)"""
    def c(x, y, z, base):
        if chain and base != TINT and (int(x * 2) + int(y * 2)) % 2 == 0:
            return shade(base, 0.8)
        return base

    def f(x, y, z):
        if piece == "helmet":
            d = ell(x, y, z, 8, 7, 8, 5.2, 5.0, 5.2)
            inner = ell(x, y, z, 8, 6.4, 8, 4.4, 4.4, 4.4)
            if d < 1 and not inner < 1 and y > 4:
                # the face opening
                if z > 10 and 4.5 < y < 8.2 and abs(x - 8) < 3.0:
                    return None
                if trim and abs(y - 8.4) < 0.5:
                    return trim
                if abs(x - 8) < 0.6 and y > 8:
                    return c(x, y, z, mix(main, (255, 255, 255), 0.25) if main != TINT else TINT)
                return c(x, y, z, main)
        elif piece == "chestplate":
            body = abs(x - 8) < 4.6 - max(0, (5 - y)) * 0.2 and 2 < y < 13 and abs(z - 8) < 2.4
            hollow = abs(x - 8) < 3.8 and abs(z - 8) < 1.6 and y < 12.4
            shoulder = 12 > y > 9 and 4.6 <= abs(x - 8) < 7 and abs(z - 8) < 2.0
            if (body and not hollow) or shoulder:
                if trim and (abs(y - 6) < 0.5 or (shoulder and y > 11.4)):
                    return trim
                if 11.4 < y and abs(x - 8) < 1.6 and z > 8:
                    return None  # the neck
                return c(x, y, z, main)
        elif piece == "leggings":
            for sx in (-1, 1):
                leg = abs(x - 8 - sx * 2.2) < 2.0 and 1 < y < 10 and abs(z - 8) < 2.0
                if leg and not (abs(x - 8 - sx * 2.2) < 1.3 and abs(z - 8) < 1.3):
                    if trim and abs(y - 5) < 0.5:
                        return trim
                    return c(x, y, z, main)
            if 9 <= y < 12 and abs(x - 8) < 4.2 and abs(z - 8) < 2.0 and not (abs(x - 8) < 3.4 and abs(z - 8) < 1.3):
                return shade(main, 0.85) if main != TINT else TINT
        elif piece == "boots":
            for sx in (-1, 1):
                bx = x - 8 - sx * 2.6
                if 3 <= y < 9 and abs(bx) < 1.9 and abs(z - 8) < 1.9 and not (abs(bx) < 1.2 and abs(z - 8) < 1.2 and y > 4):
                    if trim and abs(y - 7.6) < 0.5:
                        return trim
                    return c(x, y, z, main)
                if 3 <= y < 5 and abs(bx) < 1.9 and 9.9 <= z < 11.6:
                    return c(x, y, z, shade(main, 0.9) if main != TINT else TINT)
        return None
    return f


def armour():
    n = 0
    for tier, col in TIER_COLOURS.items():
        pieces = ["helmet"] if tier == "turtle" else ["helmet", "chestplate", "leggings", "boots"]
        for piece in pieces:
            name = f"{tier}_{piece}"
            main = TINT if tier == "leather" else col
            v = vanilla(name)
            chain = tier == "chainmail"
            build(name, armour_shape(piece, main, chain=chain), tilt=20)
            item_json(name, name, v["textures"]["layer0"], gui_textures=v["textures"], overrides=v.get("overrides"))
            n += 1
            for o in v.get("overrides", []):
                tname = o["model"].split("/")[-1]
                mat = tname[len(name) + 1:-len("_trim")].replace("_darker", "")
                tv = vanilla(tname)
                trim = TRIM_COLOURS.get(mat, (200, 200, 200))
                if tname.endswith("_darker_trim"):
                    trim = shade(trim, 0.75)
                build(tname, armour_shape(piece, main, trim, chain), tilt=20)
                item_json(tname, tname, tv["textures"]["layer0"], gui_textures=tv["textures"])
                n += 1
    # horse armour: a padded plate
    for tier in ("leather", "iron", "golden", "diamond"):
        name = f"{tier}_horse_armor"
        main = TINT if tier == "leather" else TIER_COLOURS[tier]

        def f(x, y, z, main=main):
            if ell(x, y, z, 8, 8, 8, 6.0, 4.0, 2.2) < 1 and not ell(x, y, z, 8, 7.6, 8, 5.2, 3.2, 1.4) < 1:
                if abs(x - 8) < 0.5:
                    return (240, 200, 80)
                return main
            return None
        v = vanilla(name)
        build(name, f)
        item_json(name, name, v["textures"]["layer0"], gui_textures=v["textures"])
        n += 1
    return n


# ---------------------------------------------------------------- discs, dyes, seeds, sherds, templates, patterns
def disc_shape(label, label2):
    def f(x, y, z):
        r = math.hypot(x - 8, y - 8)
        if abs(z - 8) > 0.6 or r > 6.4:
            return None
        if r < 0.7:
            return None
        if r < 2.4:
            return label if r > 1.4 else label2
        if r > 6.0:
            return (60, 60, 64)
        return (30, 30, 34) if int(r * 2) % 2 else (44, 44, 50)
    return f


def dye_shape(c, c2):
    """a little cloth pouch of dye, tied at the neck"""
    def f(x, y, z):
        if ell(x, y, z, 8, 6.4, 8, 3.4, 3.4, 3.4) < 1:
            return c if noise(x // 2, y // 2, z // 2, 97) > 0.25 else c2
        if 9.2 <= y < 10.2 and math.hypot(x - 8, z - 8) < 1.3:
            return (200, 180, 140)
        if 10.2 <= y < 11.8 and math.hypot(x - 8, z - 8) < 1.8 - (y - 10.2) * 0.3:
            return c
        return None
    return f


def seeds_shape(c, c2):
    pts = [(6.6, 6.2, 7.8), (8.4, 6.0, 8.8), (9.4, 6.4, 7.0), (7.6, 7.4, 7.0), (8.2, 7.2, 9.6)]

    def f(x, y, z):
        for i, (cx, cy, cz) in enumerate(pts):
            if ell(x, y, z, cx, cy, cz, 0.9, 0.6, 0.6) < 1:
                return c if i % 2 else c2
        return None
    return f


def plate(c, c2, c3, thick=0.6, w=5.6, h=6.0, round_=False):
    """a flat tile (pottery sherd, smithing template, banner pattern) with its picture's colours in bands"""
    def f(x, y, z):
        if abs(z - 8) > thick:
            return None
        if round_:
            if ell(x, y, z, 8, 8, 8, w, h, 99) >= 1:
                return None
        elif abs(x - 8) > w or abs(y - 8) > h or (abs(x - 8) > w - 1 and abs(y - 8) > h - 1):
            return None
        if abs(x - 8) > w - 0.6 or abs(y - 8) > h - 0.6:
            return c
        n = noise(x // 1, y // 1, 0, 101)
        return c3 if n < 0.18 else c2
    return f


def families_small():
    n = 0
    for f in sorted(Z.namelist()):
        if not (f.startswith("assets/minecraft/models/item/") and f.endswith(".json")):
            continue
        name = f.split("/")[-1][:-5]
        try:
            v = vanilla(name)
        except KeyError:
            continue
        tex = v.get("textures", {}).get("layer0")
        if name.startswith("music_disc_"):
            p = palette(tex, 4)
            build(name, disc_shape(p[-1], p[-2]))
            item_json(name, name, tex, gui_parent="minecraft:item/template_music_disc", gui_textures=v["textures"])
        elif name.endswith("_dye"):
            p = palette(tex, 3)
            build(name, dye_shape(p[-1], p[-2]))
            item_json(name, name, tex, gui_textures=v["textures"])
        elif name.endswith("_seeds") or name == "pitcher_pod" or name == "cocoa_beans":
            p = palette(tex, 3)
            build(name, seeds_shape(p[-1], p[-2]))
            item_json(name, name, tex, gui_textures=v["textures"])
        elif name.endswith("_pottery_sherd"):
            p = palette(tex, 3)
            build(name, plate(p[0], p[-1], p[1], 0.7, 5.4, 5.4, True), tilt=25)
            item_json(name, name, tex, gui_textures=v["textures"])
        elif name.endswith("_smithing_template"):
            p = palette(tex, 3)
            build(name, plate(p[0], p[1], p[-1], 0.5, 5.6, 6.6), tilt=25)
            item_json(name, name, tex, gui_textures=v["textures"])
        elif name.endswith("_banner_pattern"):
            p = palette(tex, 3)
            build(name, plate(p[0], p[-1], p[1], 0.3, 5.0, 6.2), tilt=25)
            item_json(name, name, tex, gui_textures=v["textures"])
        elif name.startswith("disc_fragment"):
            build(name, plate((40, 40, 44), (60, 60, 66), (90, 220, 210), 0.5, 3.6, 3.6, True), tilt=25)
            item_json(name, name, tex, gui_textures=v["textures"])
        else:
            continue
        n += 1
    return n


# ---------------------------------------------------------------- boats and minecarts
def boat_shape(wood, dark, chest=False, raft=False):
    def f(x, y, z):
        if raft:
            if 4 <= y < 6 and abs(x - 8) < 6.4 and abs(z - 8) < 3.6:
                return wood if int(z) % 2 else dark
            return None
        hull = abs(x - 8) < 7 and 3 <= y < 7.6 and abs(z - 8) < 3.6 - max(0, abs(x - 8) - 4.6) * 0.9
        inside = abs(x - 8) < 6.2 and y >= 4 and abs(z - 8) < 2.8 - max(0, abs(x - 8) - 4.6) * 0.9
        if hull and not inside:
            return dark if y < 4 or y > 6.8 else wood
        if 5 <= y < 5.8 and abs(x - 8 - 1.5) < 0.8 and abs(z - 8) < 2.8:
            return dark  # a seat
        if chest and 4 <= y < 8.6 and abs(x - 8 + 3) < 1.8 and abs(z - 8) < 1.8:
            return (180, 130, 60) if y < 8 else (90, 60, 30)
        # oars
        if abs(abs(z - 8) - 4.2) < 0.4 and 5 <= y < 6 and abs(x - 8) < 3.6:
            return dark
        return None
    return f


def cart_shape(cargo=None, cargo2=None):
    def f(x, y, z):
        box = abs(x - 8) < 5.4 and 4 <= y < 9 and abs(z - 8) < 3.6
        inside = abs(x - 8) < 4.6 and y >= 5 and abs(z - 8) < 2.8
        if box and not inside:
            return (140, 144, 150) if y > 5 else (100, 104, 110)
        if cargo and inside and y < 8.6:
            return cargo if noise(x // 2, y // 2, z // 2, 103) > 0.3 else (cargo2 or cargo)
        for sx in (-1, 1):
            for sz in (-1, 1):
                if ell(x, y, z, 8 + sx * 3.4, 3.8, 8 + sz * 3.7, 1.3, 1.3, 0.4) < 1:
                    return (50, 50, 54)
        return None
    return f


WOODS = {"oak": "oak_planks", "spruce": "spruce_planks", "birch": "birch_planks", "jungle": "jungle_planks", "acacia": "acacia_planks",
         "dark_oak": "dark_oak_planks", "mangrove": "mangrove_planks", "cherry": "cherry_planks", "bamboo": "bamboo_planks"}


def vehicles():
    n = 0
    for wood, planks in WOODS.items():
        p = palette(f"minecraft:block/{planks}", 3)
        for kind in ("boat", "chest_boat"):
            if wood == "bamboo":
                name = "bamboo_raft" if kind == "boat" else "bamboo_chest_raft"
            else:
                name = f"{wood}_{kind}"
            try:
                v = vanilla(name)
            except KeyError:
                continue
            build(name, boat_shape(p[1], p[0], kind == "chest_boat", wood == "bamboo"), tilt=15)
            item_json(name, name, v["textures"]["layer0"], gui_textures=v["textures"])
            n += 1
    carts = {"minecart": None, "chest_minecart": ((180, 130, 60), (90, 60, 30)), "furnace_minecart": ((90, 90, 96), (250, 160, 40)),
             "tnt_minecart": ((220, 40, 40), (240, 240, 240)), "hopper_minecart": ((70, 70, 74), (50, 50, 54)),
             "command_block_minecart": ((200, 130, 90), (120, 160, 150))}
    for name, cargo in carts.items():
        v = vanilla(name)
        build(name, cart_shape(*(cargo or (None, None))), tilt=15)
        item_json(name, name, v["textures"]["layer0"], gui_textures=v["textures"])
        n += 1
    return n


JOBS = {"eggs": spawn_eggs, "armour": armour, "small": families_small, "vehicles": vehicles}
if __name__ == "__main__":
    total = 0
    for k, fn in JOBS.items():
        if ONLY and k not in ONLY:
            continue
        c = fn()
        print(k, c)
        total += c
    print("made", total)
