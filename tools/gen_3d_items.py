#!/usr/bin/env python3
"""Builds the "Lifelike 3D Items" built-in resource pack.

Every flat item (one texture layer, no special model) gets a chunky 3D model made of little blocks: each pixel of the
item's own texture becomes a column whose thickness depends on what the item is and how far the pixel is from the
item's outline. Blades get a raised middle ridge, tool heads are thick with a bevelled rim, handles are round-ish rods,
food is puffy. The models only point at the game's textures (nothing of Mojang's is copied into the pack), so
texture packs still colour them.

In the inventory (GUI) the item stays the usual flat picture: the pack uses Forge's "separate_transforms" model loader.

usage: gen_3d_items.py <minecraft 1.20.1 client.jar> <output pack dir>
"""
import io
import json
import os
import re
import sys
import zipfile

from PIL import Image

JAR, OUT = sys.argv[1], sys.argv[2]
NS = "lifelikemotion"
z = zipfile.ZipFile(JAR)


def read_json(path):
    return json.loads(z.read(path))


def texture(name):
    """'minecraft:item/iron_sword' -> RGBA image (or None)."""
    ns, _, p = name.partition(":") if ":" in name else ("minecraft", "", name)
    try:
        return Image.open(io.BytesIO(z.read(f"assets/{ns}/textures/{p}.png"))).convert("RGBA")
    except KeyError:
        return None


def has_animation(name):
    ns, _, p = name.partition(":") if ":" in name else ("minecraft", "", name)
    return f"assets/{ns}/textures/{p}.png.mcmeta" in z.namelist()


GENERATED = ("minecraft:item/generated", "item/generated")
HANDHELD = ("minecraft:item/handheld", "item/handheld", "minecraft:item/handheld_rod", "item/handheld_rod")

# the game's display transforms for flat and hand-held items (copied so our models are held exactly like the originals)
gen_display = read_json("assets/minecraft/models/item/generated.json")["display"]
hand_display = dict(gen_display)
hand_display.update(read_json("assets/minecraft/models/item/handheld.json")["display"])
rod_display = dict(gen_display)
rod_display.update(read_json("assets/minecraft/models/item/handheld_rod.json")["display"])

STICK = {p[:3] for p in Image.open(io.BytesIO(z.read("assets/minecraft/textures/item/stick.png"))).convert("RGBA").getdata() if p[3] > 0}

FOOD = set("""apple golden_apple enchanted_golden_apple bread cookie melon_slice glistering_melon_slice carrot golden_carrot potato
baked_potato poisonous_potato beetroot pumpkin_pie cake beef cooked_beef porkchop cooked_porkchop chicken cooked_chicken mutton
cooked_mutton rabbit cooked_rabbit cod cooked_cod salmon cooked_salmon tropical_fish pufferfish rotten_flesh spider_eye
fermented_spider_eye chorus_fruit popped_chorus_fruit sweet_berries glow_berries dried_kelp honeycomb egg slime_ball
magma_cream snowball""".split())
CHUNKY = set("""iron_ingot gold_ingot copper_ingot netherite_ingot netherite_scrap brick nether_brick diamond emerald
lapis_lazuli amethyst_shard quartz coal charcoal raw_iron raw_gold raw_copper flint ender_pearl ender_eye heart_of_the_sea
nether_star totem_of_undying echo_shard prismarine_shard prismarine_crystals clay_ball bucket water_bucket lava_bucket
milk_bucket powder_snow_bucket glass_bottle experience_bottle honey_bottle book writable_book written_book enchanted_book
knowledge_book compass recovery_compass clock lead name_tag saddle brush flower_pot""".split())
THIN = set("""paper map filled_map feather leather rabbit_hide string phantom_membrane gunpowder sugar glowstone_dust
redstone blaze_powder bone_meal ink_sac glow_ink_sac cocoa_beans wheat_seeds pumpkin_seeds melon_seeds beetroot_seeds
torchflower_seeds pitcher_pod""".split()) | {n for n in [] }
RODS = set("stick blaze_rod bone breeze_rod end_rod".split())
SKIP = re.compile(r"(spawn_egg|banner_pattern|pottery_sherd|smithing_template|music_disc|_trim$|potion|tipped_arrow"
                  r"|firework|leather_|dyed|bundle)")


def kind(name, parent):
    if name.endswith("_sword"):
        return "blade"
    if re.search(r"_(pickaxe|axe|shovel|hoe)$", name) or name in ("shears", "flint_and_steel", "fishing_rod", "carrot_on_a_stick",
                                                                  "warped_fungus_on_a_stick", "trident", "mace"):
        return "tool"
    if name in RODS:
        return "rod"
    if name in FOOD:
        return "food"
    if name in CHUNKY:
        return "chunky"
    if name in THIN or name.endswith("_dye"):
        return "thin"
    if parent in HANDHELD:
        return "tool"
    return "plain"


# total thickness (in texture pixels) by kind and by distance (in pixels) from the outline: 1 = on the rim
PROFILE = {
    "blade": (1.0, 1.5, 2.0, 2.0),
    "tool": (2.0, 2.5, 3.0, 3.0),
    "rod": (1.75, 2.0, 2.0, 2.0),
    "food": (2.0, 3.0, 3.5, 4.0),
    "chunky": (2.0, 2.75, 3.25, 3.5),
    "thin": (0.75, 0.75, 0.75, 0.75),
    "plain": (1.0, 1.5, 2.0, 2.0),
}
HANDLE = 2.0


def depths(img, k):
    w, h = img.size
    a = [[img.getpixel((x, y))[3] > 16 for x in range(w)] for y in range(h)]
    # distance from the outline: rings of a 4-neighbour flood from the transparent pixels
    INF = 99
    d = [[INF if a[y][x] else 0 for x in range(w)] for y in range(h)]
    frontier = [(x, y) for y in range(h) for x in range(w) if not a[y][x]]
    for x in range(w):  # the picture's edges count as outline too
        for y in (0, h - 1):
            if a[y][x] and d[y][x] > 1:
                d[y][x] = 1
    for y in range(h):
        for x in (0, w - 1):
            if a[y][x] and d[y][x] > 1:
                d[y][x] = 1
    ring = 0
    frontier += [(x, y) for y in range(h) for x in range(w) if d[y][x] == 1]
    while frontier:
        ring += 1
        nxt = []
        for x, y in frontier:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and d[ny][nx] > d[y][x] + 1:
                    d[ny][nx] = d[y][x] + 1
                    nxt.append((nx, ny))
        frontier = nxt
    prof = PROFILE[k]
    out = [[0.0] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if not a[y][x]:
                continue
            t = prof[min(d[y][x], len(prof)) - 1]
            # handles (the stick's colours) are rods whatever the head around them does
            if k in ("blade", "tool") and img.getpixel((x, y))[:3] in STICK:
                t = HANDLE
            out[y][x] = t
    return out


def r(v):
    return round(v, 4)


def elements(dep, w, h):
    """Runs of equal thickness along each row become one box each; only faces that can be seen are kept."""
    s = 16 / w  # model units per texture pixel (16x16 textures: 1)
    els = []

    def at(x, y):
        return dep[y][x] if 0 <= x < w and 0 <= y < h else 0.0

    used = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            t = dep[y][x]
            if t <= 0 or used[y][x]:
                continue
            # the biggest rectangle of equal thickness from here: as wide as possible, then as tall as possible
            x1 = x
            while x1 < w and dep[y][x1] == t and not used[y][x1]:
                x1 += 1
            y1 = y + 1
            while y1 < h and all(dep[y1][i] == t and not used[y1][i] for i in range(x, x1)):
                y1 += 1
            for yy in range(y, y1):
                for xx in range(x, x1):
                    used[yy][xx] = True
            x0, y0 = x, y
            z0, z1 = 8 - t / 2 * s, 8 + t / 2 * s
            u0, u1, v0, v1 = x0 * s, x1 * s, y0 * s, y1 * s
            faces = {
                "south": {"uv": [r(u0), r(v0), r(u1), r(v1)], "texture": "#layer0"},
                "north": {"uv": [r(u1), r(v0), r(u0), r(v1)], "texture": "#layer0"},
            }
            if any(at(i, y0 - 1) < t for i in range(x0, x1)):
                faces["up"] = {"uv": [r(u0), r(v0), r(u1), r(v0 + s)], "texture": "#layer0"}
            if any(at(i, y1) < t for i in range(x0, x1)):
                faces["down"] = {"uv": [r(u0), r(v1 - s), r(u1), r(v1)], "texture": "#layer0"}
            if any(at(x0 - 1, j) < t for j in range(y0, y1)):
                faces["west"] = {"uv": [r(u0), r(v0), r(u0 + s), r(v1)], "texture": "#layer0"}
            if any(at(x1, j) < t for j in range(y0, y1)):
                faces["east"] = {"uv": [r(u1 - s), r(v0), r(u1), r(v1)], "texture": "#layer0"}
            els.append({"from": [r(x0 * s), r(16 - y1 * s), r(z0)], "to": [r(x1 * s), r(16 - y0 * s), r(z1)], "faces": faces})
    return els


def main():
    made, skipped = [], []
    item_dir = "assets/minecraft/models/item/"
    for path in sorted(n for n in z.namelist() if n.startswith(item_dir) and n.endswith(".json")):
        name = path[len(item_dir):-5]
        m = read_json(path)
        parent = m.get("parent", "")
        tex = m.get("textures", {})
        if parent not in GENERATED + HANDHELD or list(tex) != ["layer0"] or "overrides" in m or "display" in m or SKIP.search(name):
            continue
        layer0 = tex["layer0"]
        img = texture(layer0)
        if img is None or img.size[0] != img.size[1] or img.size[0] not in (16, 32) or has_animation(layer0):
            skipped.append(name)
            continue
        k = kind(name, parent)
        w, h = img.size
        els = elements(depths(img, k), w, h)
        if not els:
            continue
        display = rod_display if parent.endswith("handheld_rod") else hand_display if parent in HANDHELD else gen_display
        model = {"gui_light": "front", "textures": {"layer0": layer0, "particle": layer0}, "display": display, "elements": els}
        wr(f"assets/{NS}/models/item3d/{name}.json", model)
        # the game's item model: 3D everywhere, the usual flat picture in the inventory
        wr(f"assets/minecraft/models/item/{name}.json", {
            "loader": "forge:separate_transforms",
            "base": {"parent": f"{NS}:item3d/{name}"},
            "perspectives": {"gui": {"parent": parent if ":" in parent else "minecraft:" + parent, "textures": {"layer0": layer0}}},
        })
        made.append((name, k, len(els)))
    wr("pack.mcmeta", {"pack": {"pack_format": 15, "description": "Chunky 3D items (Lifelike Motion)"}})
    by = {}
    for n, k, c in made:
        by.setdefault(k, []).append(c)
    print(f"{len(made)} items made 3D, {len(skipped)} skipped")
    for k, cs in sorted(by.items()):
        print(f"  {k:7s} {len(cs):4d} items, {sum(cs) / len(cs):.0f} boxes on average, at most {max(cs)}")


def wr(rel, obj):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        json.dump(obj, f, separators=(",", ":"))


main()
