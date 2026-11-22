#!/usr/bin/env python3
"""Sculpted 3D food for the "Lifelike 3D Items" pack.

Each food is a shape function sampled on a fine grid (half-unit voxels): it returns the colour of the material at a
point, or None for empty. Voxels of one colour in a row are merged into a box, and each colour becomes a tiny swatch in
the food's own texture. Light comes from above: colours are shaded by height and by how exposed the voxel is, so round
things look round.

usage: gen_food.py <pack dir> [names...]
"""
import json
import math
import os
import random
import sys

from PIL import Image

PACK = sys.argv[1]
ONLY = set(sys.argv[2:])
NS = "lifelikemotion"
STEP = 0.5
N = int(16 / STEP)


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ell(x, y, z, cx, cy, cz, rx, ry, rz):
    return ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 + ((z - cz) / rz) ** 2


def noise(x, y, z, seed=0):
    v = math.sin(x * 12.9898 + y * 78.233 + z * 37.719 + seed * 4.1) * 43758.5453
    return v - math.floor(v)


class Food:
    def __init__(self, name):
        self.name = name

    def build(self, shape, glow=lambda c: False, scale=1.0):
        """shape(x, y, z) -> (r, g, b) or None, sampled at voxel centres"""
        grid = {}
        for ix in range(N):
            for iy in range(N):
                for iz in range(N):
                    x, y, z = (ix + 0.5) * STEP, (iy + 0.5) * STEP, (iz + 0.5) * STEP
                    c = shape(x, y, z)
                    if c is not None:
                        grid[(ix, iy, iz)] = c
        # light: brighter toward the top (by layer, so whole slices of one material merge into big boxes);
        # hidden voxels are kept so the boxes can run straight through the inside
        lit = {}
        for (ix, iy, iz), c in grid.items():
            k = 0.8 + 0.34 * round((iy + 1) / N * 6) / 6
            lit[(ix, iy, iz)] = (shade(c, k), glow(c))
        # one swatch per colour
        colours = sorted({v for v in lit.values()})
        tex = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        uv = {}
        per_row = 64
        for i, (c, g) in enumerate(colours):
            px, py = (i % per_row) * 2, (i // per_row) * 2
            if py >= 128:
                raise RuntimeError(f"{self.name}: too many colours")
            for dx in range(2):
                for dy in range(2):
                    tex.putpixel((px + dx, py + dy), c + (255,))
            s = 16 / 128
            uv[(c, g)] = [px * s + 0.02, py * s + 0.02, (px + 2) * s - 0.02, (py + 2) * s - 0.02]
        # greedy merge: rectangles of one colour in each layer (x then z) become one box; only faces that can be seen
        els = []
        done = set()
        for (ix, iy, iz) in sorted(lit, key=lambda v: (v[1], v[2], v[0])):
            if (ix, iy, iz) in done:
                continue
            key = lit[(ix, iy, iz)]
            same = lambda a, b, c: (a, b, c) in lit and lit[(a, b, c)] == key and (a, b, c) not in done
            jx = ix
            while same(jx + 1, iy, iz):
                jx += 1
            jz = iz
            while all(same(k, iy, jz + 1) for k in range(ix, jx + 1)):
                jz += 1
            cells = [(a, iy, c) for a in range(ix, jx + 1) for c in range(iz, jz + 1)]
            done.update(cells)
            u = uv[key]
            faces = {}
            def open_(d):
                return any((a + d[0], b + d[1], c + d[2]) not in grid for (a, b, c) in cells)
            for name, d in (("west", (-1, 0, 0)), ("east", (1, 0, 0)), ("up", (0, 1, 0)), ("down", (0, -1, 0)),
                            ("south", (0, 0, 1)), ("north", (0, 0, -1))):
                if open_(d):
                    faces[name] = {"uv": u, "texture": "#t"}
            if not faces:
                continue
            e = {"from": [ix * STEP, iy * STEP, iz * STEP], "to": [(jx + 1) * STEP, (iy + 1) * STEP, (jz + 1) * STEP],
                 "faces": faces, "shade": False}
            if key[1]:
                e["forge_data"] = {"block_light": 15, "sky_light": 15}
            els.append(e)
        tname = f"item/food/{self.name}"
        tp = os.path.join(PACK, "assets", NS, "textures", tname + ".png")
        os.makedirs(os.path.dirname(tp), exist_ok=True)
        tex.save(tp)
        s = 0.46 * scale
        display = {
            "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.5 * scale] * 3},
            "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.5 * scale] * 3},
            "firstperson_righthand": {"rotation": [0, -90, 25], "translation": [1.13, 4.2, 1.13], "scale": [s] * 3},
            "firstperson_lefthand": {"rotation": [0, 90, -25], "translation": [1.13, 4.2, 1.13], "scale": [s] * 3},
            "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5, 0.5, 0.5]},
            "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
            "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
        }
        model = {"textures": {"t": f"{NS}:{tname}", "particle": f"{NS}:{tname}"}, "display": display, "elements": els}
        mp = os.path.join(PACK, "assets", NS, "models", "item3d", self.name + ".json")
        with open(mp, "w") as f:
            json.dump(model, f, separators=(",", ":"))
        gui = "minecraft:item/" + self.name
        item = {"loader": "forge:separate_transforms", "textures": {"particle": gui}, "base": {"parent": f"{NS}:item3d/{self.name}"},
                "perspectives": {"gui": {"parent": "minecraft:item/generated", "textures": {"layer0": gui}}}}
        with open(os.path.join(PACK, "assets", "minecraft", "models", "item", self.name + ".json"), "w") as f:
            json.dump(item, f, separators=(",", ":"))
        return len(els)


# ---------------------------------------------------------------- materials
def q(c, x, y, z, amt=0.12, seed=0):
    """a colour with a little grain, in coarse patches (so neighbours merge)"""
    return shade(c, 1 - amt / 4 + (amt / 2 if noise(x // 3, y // 3, z // 3, seed) > 0.7 else 0))


# ---------------------------------------------------------------- the foods
def apple(skin=(200, 30, 30), skin2=(240, 80, 60), glowing=False, leaf=(70, 160, 50)):
    def f(x, y, z):
        # a sphere, a little flattened, with a dimple on top
        d = ell(x, y, z, 8, 7.2, 8, 5.2, 4.8, 5.2)
        dimple = ell(x, y, z, 8, 12.2, 8, 1.6, 1.2, 1.6) < 1
        if d < 1 and not dimple:
            t = (y - 2.4) / 9.6
            c = mix(skin, skin2, max(0, min(1, (x - 4) / 8 * 0.6 + t * 0.4)))
            # a glossy highlight up front-left
            if ell(x, y, z, 6.0, 9.4, 11.5, 1.6, 1.4, 1.6) < 1:
                c = mix(c, (255, 255, 255), 0.55)
            if noise(x, y, z) < 0.06:
                c = mix(c, (250, 230, 120), 0.4)
            return c
        if abs(x - 8.2) < 0.5 and abs(z - 8) < 0.5 and 11.0 < y < 14.2:
            return (96, 62, 30)
        # a leaf off the stem
        if 8.3 < x < 11.8 and 12.6 < y < 13.6 and abs(z - 8 - (x - 8) * 0.3) < 1.1 - abs(x - 10) * 0.25:
            return leaf
        return None
    return f, (lambda c: glowing)


def carrot(body=(240, 130, 30), ridge=(190, 90, 20), tops=(70, 170, 60)):
    def f(x, y, z):
        # a cone from a fat top to a point, ringed with grooves
        if 1.0 < y < 12.0:
            r = 0.4 + (y - 1.0) / 11.0 * 2.2
            if (x - 8) ** 2 + (z - 8) ** 2 < r * r:
                return ridge if int(y * 1.6) % 3 == 0 else q(body, x, y, z)
        # leafy tops
        for ang in (0, 2.1, 4.2):
            lx, lz = 8 + math.cos(ang) * (y - 12) * 0.5, 8 + math.sin(ang) * (y - 12) * 0.5
            if 12.0 <= y < 15.5 and (x - lx) ** 2 + (z - lz) ** 2 < 0.5:
                return tops
        return None
    return f, None


def potato(skin=(200, 160, 90), spot=(150, 110, 60), inner=None):
    def f(x, y, z):
        d = ell(x, y, z, 8, 7, 8, 5.2, 3.6, 3.8) + 0.08 * math.sin(x * 1.3) * math.cos(z * 1.1)
        if d < 1:
            if inner and y > 9.0 and abs(z - 8) < 1.2:
                return inner
            return spot if noise(x, y, z, 3) < 0.07 else q(skin, x, y, z)
        return None
    return f, None


def beetroot():
    def f(x, y, z):
        if ell(x, y, z, 8, 7, 8, 3.8, 3.6, 3.8) < 1:
            return q((150, 30, 50), x, y, z)
        if abs(x - 8) < 0.5 and abs(z - 8) < 0.5 and 1.0 < y < 3.6:
            return (120, 30, 40)
        for ang in (0.4, 2.5, 4.6):
            lx, lz = 8 + math.cos(ang) * (y - 10) * 0.6, 8 + math.sin(ang) * (y - 10) * 0.6
            if 10.4 <= y < 14.5 and (x - lx) ** 2 + (z - lz) ** 2 < 0.6:
                return (60, 140, 50) if y > 11.5 else (160, 40, 60)
        return None
    return f, None


def melon_slice():
    def f(x, y, z):
        # a wedge: a half disc, thin
        if abs(z - 8) > 1.4 or y < 3:
            return None
        r = math.hypot(x - 8, y - 3)
        if r > 7.2 or y - 3 < 0:
            return None
        if r > 6.4:
            return (60, 140, 50)
        if r > 5.6:
            return (220, 240, 190)
        if abs(z - 8) > 1.0 and noise(x, y, 0, 5) < 0.08 and r < 5:
            return (40, 30, 30)
        return q((230, 60, 60), x, y, z)
    return f, None


def berries(colour, glowing=False, stem=(80, 110, 50)):
    pts = [(7, 6, 8), (9.6, 6.4, 7.4), (8.2, 8.6, 8.8), (6.4, 8.8, 7.0), (9.6, 9.0, 9.0), (8.0, 11.2, 7.8)]

    def f(x, y, z):
        for (cx, cy, cz) in pts:
            if ell(x, y, z, cx, cy, cz, 1.6, 1.6, 1.6) < 1:
                if ell(x, y, z, cx - 0.6, cy + 0.6, cz + 0.6, 0.6, 0.6, 0.6) < 1:
                    return mix(colour, (255, 255, 255), 0.5)
                return q(colour, x, y, z)
        if abs(x - 8) < 0.4 and abs(z - 8) < 0.4 and 11 < y < 14:
            return stem
        return None
    return f, (lambda c: glowing and c != stem)


def chorus():
    def f(x, y, z):
        d = ell(x, y, z, 8, 7.5, 8, 4.4, 4.4, 4.4)
        for (cx, cy, cz) in ((8, 12, 8), (12.2, 8, 8), (4, 7, 8.6), (8, 7, 12.2)):
            d = min(d, ell(x, y, z, cx, cy, cz, 1.8, 1.8, 1.8))
        if d < 1:
            return (210, 170, 220) if noise(x, y, z, 7) < 0.15 else q((150, 90, 160), x, y, z)
        return None
    return f, None


def bread():
    def f(x, y, z):
        d = ell(x, y, z, 8, 5.5, 8, 6.4, 3.4, 3.2)
        if d < 1 and y > 2.6:
            top = y > 6.5
            # diagonal slashes across the crust
            if top and abs(((x + z * 0.6) % 3.2) - 1.6) < 0.35:
                return (240, 210, 140)
            return q((200, 130, 50) if top else (220, 160, 80), x, y, z)
        return None
    return f, None


def cookie():
    def f(x, y, z):
        if 5.4 < y < 7.2 and math.hypot(x - 8, z - 8) < 5.2:
            if noise(x, 0, z, 9) < 0.12 and y > 6.4:
                return (70, 40, 20)
            return q((210, 150, 80), x, y, z)
        return None
    return f, None


def pie():
    def f(x, y, z):
        r = math.hypot(x - 8, z - 8)
        if 3 < y < 7.2 and r < 6.4:
            if y > 6.4 and r < 5.2:
                return q((230, 140, 40), x, y, z) if noise(x, 0, z, 11) > 0.1 else (250, 220, 170)
            return q((220, 170, 100), x, y, z) if r > 5.2 or y < 4.0 else (240, 190, 120)
        return None
    return f, None


def steak(meat, fat, cooked=False, bone=False):
    def f(x, y, z):
        d = ell(x, y, z, 8, 7, 8, 5.4, 1.8, 4.4) + 0.06 * math.sin(x * 1.7 + z)
        if d < 1:
            if cooked and y > 8.0 and abs(((x + z) % 2.6) - 1.3) < 0.3:
                return (60, 30, 15)
            if math.hypot(x - 8, z - 8) > 3.8 + 0.4 * math.sin(x):
                return fat
            return fat if noise(x, y, z, 13) < 0.06 else q(meat, x, y, z)
        if bone and abs(z - 8) < 0.6 and abs(y - 7) < 0.6 and 12.6 < x < 15.6:
            return (240, 230, 210)
        if bone and ell(x, y, z, 15.6, 7, 8, 0.9, 1.0, 1.0) < 1:
            return (240, 230, 210)
        return None
    return f, None


def drumstick(meat, cooked):
    def f(x, y, z):
        if ell(x, y, z, 8, 6.2, 8, 3.8, 4.4, 3.8) < 1 and y < 9.6:
            return q(meat, x, y, z) if not cooked or noise(x, y, z, 17) > 0.08 else shade(meat, 0.7)
        if math.hypot(x - 8, z - 8) < 0.8 and 9.0 < y < 13.6:
            return (240, 230, 210)
        if ell(x, y, z, 8, 14.0, 8, 1.3, 0.9, 1.3) < 1:
            return (240, 230, 210)
        return None
    return f, None


def fish(body, belly, fin, stripes=None, cooked=False):
    def f(x, y, z):
        # body along x, tail fin at the back, a dorsal fin on top
        d = ell(x, y, z, 7.6, 8, 8, 5.4, 2.6, 1.6)
        if d < 1:
            if ell(x, y, z, 11.4, 8.8, 9.3, 0.6, 0.6, 0.6) < 1 or ell(x, y, z, 11.4, 8.8, 6.7, 0.6, 0.6, 0.6) < 1:
                return (20, 20, 20)
            if stripes and int((x + 1) / 1.6) % 2 == 0:
                return stripes
            c = belly if y < 7.4 else body
            if cooked and abs(((x - y) % 2.2) - 1.1) < 0.25:
                return shade(c, 0.6)
            return q(c, x, y, z)
        if 1.0 < x < 3.0 and abs(z - 8) < 0.5 and abs(y - 8) < (3.0 - x) * 1.6 + 0.4:
            return fin
        if 5.0 < x < 9.0 and abs(z - 8) < 0.4 and 10.4 < y < 10.4 + (x - 5.0) * 0.5:
            return fin
        return None
    return f, None


def pufferfish():
    def f(x, y, z):
        d = ell(x, y, z, 8, 8, 8, 4.2, 4.2, 4.2)
        if d < 1:
            if ell(x, y, z, 11.6, 9.2, 9.4, 0.6, 0.6, 0.6) < 1 or ell(x, y, z, 11.6, 9.2, 6.6, 0.6, 0.6, 0.6) < 1:
                return (20, 20, 20)
            return q((240, 200, 60), x, y, z) if y > 7 else (250, 240, 200)
        # spikes
        for (dx, dy, dz) in ((0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1), (-1, 0, 0), (0.7, 0.7, 0), (-0.7, 0.7, 0), (0, 0.7, 0.7), (0, 0.7, -0.7)):
            px, py, pz = 8 + dx * 4.8, 8 + dy * 4.8, 8 + dz * 4.8
            if ell(x, y, z, px, py, pz, 0.6, 0.6, 0.6) < 1:
                return (220, 220, 200)
        return None
    return f, None


def bowl(liquid, bits=None):
    def f(x, y, z):
        r = math.hypot(x - 8, z - 8)
        # a bowl: the outside of a half sphere, hollowed, filled to a level
        outer = math.hypot(r, (y - 9) * 1.4) < 6.4 and y < 9
        inner = math.hypot(r, (y - 9) * 1.4) < 5.4
        if outer and not inner:
            return q((150, 100, 50), x, y, z)
        if inner and 7.6 < y < 8.6:
            if bits and noise(x, 0, z, 19) < 0.18:
                return bits
            return q(liquid, x, y, z, 0.08)
        if 3.4 < y < 4.4 and r < 2.6:
            return (120, 80, 40)
        return None
    return f, None


def rotten():
    def f(x, y, z):
        d = ell(x, y, z, 8, 7, 8, 5.0, 2.2, 4.0) + 0.15 * math.sin(x * 2.1) * math.sin(z * 1.7)
        if d < 1:
            n = noise(x, y, z, 23)
            return (90, 120, 50) if n < 0.25 else (150, 90, 60) if n < 0.45 else q((120, 70, 50), x, y, z)
        return None
    return f, None


def spider_eye():
    def f(x, y, z):
        if ell(x, y, z, 8, 7.5, 8, 4.0, 4.0, 4.0) < 1:
            if ell(x, y, z, 8, 8.2, 11.5, 1.4, 1.6, 1.0) < 1:
                return (20, 10, 20)
            return q((160, 30, 50), x, y, z) if noise(x, y, z, 29) > 0.12 else (230, 120, 140)
        return None
    return f, None


def kelp():
    def f(x, y, z):
        if 5.6 < y < 7.6 and abs(x - 8) < 3.6 and abs(z - 8) < 3.6:
            return (40, 70, 30) if int(x + z) % 3 else q((70, 100, 40), x, y, z)
        return None
    return f, None


def rabbit_meat(meat, cooked):
    def f(x, y, z):
        if ell(x, y, z, 7.4, 7, 8, 4.4, 2.6, 2.8) < 1:
            return q(meat, x, y, z) if not cooked or noise(x, y, z, 31) > 0.08 else shade(meat, 0.7)
        for zz in (6.6, 9.4):
            if ell(x, y, z, 11.8, 6.0, zz, 1.8, 0.9, 0.9) < 1:
                return q(meat, x, y, z)
        return None
    return f, None


GOLD = ((250, 200, 50), (255, 240, 140))
FOODS = {
    "apple": lambda: apple(),
    "golden_apple": lambda: apple(*GOLD, leaf=(250, 230, 120)),
    "enchanted_golden_apple": lambda: apple(*GOLD, glowing=True, leaf=(250, 230, 120)),
    "carrot": lambda: carrot(),
    "golden_carrot": lambda: carrot((250, 200, 50), (220, 160, 30), (250, 230, 120)),
    "potato": lambda: potato(),
    "baked_potato": lambda: potato((160, 110, 50), (120, 80, 40), (250, 220, 120)),
    "poisonous_potato": lambda: potato((170, 170, 80), (100, 140, 50)),
    "beetroot": beetroot,
    "melon_slice": melon_slice,
    "glistering_melon_slice": melon_slice,
    "sweet_berries": lambda: berries((200, 30, 50)),
    "glow_berries": lambda: berries((250, 170, 50), True),
    "chorus_fruit": chorus,
    "popped_chorus_fruit": chorus,
    "bread": bread,
    "cookie": cookie,
    "pumpkin_pie": pie,
    "beef": lambda: steak((200, 50, 50), (240, 200, 190)),
    "cooked_beef": lambda: steak((130, 70, 40), (200, 150, 100), True),
    "porkchop": lambda: steak((240, 150, 150), (250, 220, 210), bone=True),
    "cooked_porkchop": lambda: steak((200, 140, 90), (240, 200, 150), True, bone=True),
    "mutton": lambda: steak((210, 70, 60), (240, 210, 200), bone=True),
    "cooked_mutton": lambda: steak((140, 80, 50), (210, 160, 110), True, bone=True),
    "chicken": lambda: drumstick((240, 200, 180), False),
    "cooked_chicken": lambda: drumstick((210, 140, 60), True),
    "rabbit": lambda: rabbit_meat((230, 140, 130), False),
    "cooked_rabbit": lambda: rabbit_meat((190, 120, 70), True),
    "cod": lambda: fish((170, 150, 110), (220, 210, 180), (140, 120, 90)),
    "cooked_cod": lambda: fish((210, 170, 110), (240, 220, 170), (180, 140, 90), cooked=True),
    "salmon": lambda: fish((200, 70, 60), (240, 150, 120), (150, 50, 40)),
    "cooked_salmon": lambda: fish((230, 140, 90), (250, 190, 150), (190, 110, 70), cooked=True),
    "tropical_fish": lambda: fish((250, 130, 40), (250, 200, 150), (250, 250, 250), stripes=(250, 250, 250)),
    "pufferfish": pufferfish,
    "mushroom_stew": lambda: bowl((190, 140, 100), (220, 200, 170)),
    "rabbit_stew": lambda: bowl((170, 110, 60), (240, 140, 40)),
    "beetroot_soup": lambda: bowl((180, 30, 50)),
    "suspicious_stew": lambda: bowl((150, 120, 90), (240, 220, 60)),
    "rotten_flesh": rotten,
    "spider_eye": spider_eye,
    "dried_kelp": kelp,
}

FLAT = {"cookie", "pumpkin_pie", "beef", "cooked_beef", "porkchop", "cooked_porkchop", "mutton", "cooked_mutton", "mushroom_stew",
        "rabbit_stew", "beetroot_soup", "suspicious_stew", "dried_kelp", "rotten_flesh"}


def stand(shape):
    """lying flat -> standing up facing you (top toward +z)"""
    return lambda x, y, z: shape(x, z, 16 - y)


n = 0
for name, make in FOODS.items():
    if ONLY and name not in ONLY:
        continue
    shape, glow = make()
    if name in FLAT:
        shape = stand(shape)
    els = Food(name).build(shape, glow or (lambda c: False))
    n += 1
    print(f"{name}: {els} boxes")
print("made", n, "foods")
