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

    def build(self, shape, glow=lambda c: False, scale=1.0, layer_light=True):
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
            k = 0.8 + 0.34 * round((iy + 1) / N * 6) / 6 if layer_light else 1.0
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


# ---------------------------------------------------------------- batch 3: gems, ores, ingots
def facet(c, nx, ny, nz):
    """a facet's colour from which way it faces: light from above-left-front, a white glint on the brightest"""
    k = 0.55 + 0.45 * max(0.0, (-0.45 * nx + 0.75 * ny + 0.5 * nz))
    out = shade(c, 0.7 + 0.6 * k)
    return mix(out, (255, 255, 255), 0.45) if k > 0.95 else out


def cut_gem(c, glow_core=None):
    """a brilliant cut: a crown (flat table, sloped facets) over a pointed pavilion"""
    def f(x, y, z):
        dx, dz = x - 8, z - 8
        r = math.hypot(dx, dz)
        ang = math.atan2(dz, dx)
        sector = round(ang / (math.pi / 4)) * (math.pi / 4)  # eight facets around
        rr = r * math.cos(ang - sector)
        top, girdle, bottom = 11.0, 8.0, 2.2
        if girdle <= y <= top:
            lim = 5.4 - (y - girdle) * 0.9
            if rr < lim:
                if y > top - STEP:
                    return facet(c, 0, 1, 0)
                return facet(c, math.cos(sector) * 0.7, 0.7, math.sin(sector) * 0.7)
        if bottom <= y < girdle:
            lim = 5.4 * (y - bottom) / (girdle - bottom)
            if rr < lim:
                if glow_core and rr < lim * 0.35:
                    return glow_core
                return facet(shade(c, 0.85), math.cos(sector) * 0.7, -0.7, math.sin(sector) * 0.7)
        return None
    return f, (lambda col: glow_core is not None and col == glow_core)


def big_gem(c, core):
    """a clean cut: a flat table on top, four broad crown facets, a deep four-sided pavilion, a glowing heart"""
    def f(x, y, z):
        dx, dz = x - 8, z - 8
        m = abs(dx) + abs(dz) * 0.9
        top, girdle, bottom = 11.6, 8.4, 2.0
        if girdle <= y <= top:
            lim = 5.6 - (y - girdle) * 0.95
            if m < lim:
                if y > top - 0.6:
                    return facet(c, 0, 1, 0)
                return facet(c, math.copysign(0.6, dx), 0.75, math.copysign(0.6, dz))
        if bottom <= y < girdle:
            lim = 5.6 * (y - bottom) / (girdle - bottom)
            if m < lim:
                if m < lim * 0.3 and y > 5:
                    return core
                return facet(shade(c, 0.85), math.copysign(0.6, dx), -0.6, math.copysign(0.6, dz))
        return None
    return f, (lambda col: col == core)


def emerald_cut(c):
    """a step-cut emerald: an octagonal slab with bevelled steps"""
    def f(x, y, z):
        ax, ay, az = abs(x - 8), abs(y - 8), abs(z - 8)
        if az > 2.2 or ax > 3.6 or ay > 5.4 or ax + ay > 7.6:
            return None
        step = az > 1.4 or ax > 3.0 or ay > 4.8 or ax + ay > 7.0
        n = (math.copysign(0.6, x - 8) if ax > 3.0 else 0, math.copysign(0.6, y - 8) if ay > 4.8 else 0, math.copysign(1, z - 8))
        return facet(shade(c, 0.9) if step else c, *n)
    return f, None


def crystal(c, glowing=True, points=((8, 2, 8, 2.0, 12.0, 0, 0),)):
    """pointed hexagonal crystals: (x, y, z, radius, length, tilt x, tilt z)"""
    def f(x, y, z):
        for (cx, cy, cz, r, ln, tx, tz) in points:
            ry = y - cy
            if not 0 <= ry <= ln:
                continue
            px, pz = x - cx - tx * ry, z - cz - tz * ry
            tip = ln * 0.72
            lim = r if ry < tip else r * (ln - ry) / (ln - tip)
            if max(abs(px), abs(pz), (abs(px) + abs(pz)) * 0.7) < lim:
                side = 1 if px + pz > 0 else -1
                col = facet(c, side * 0.6, 0.5 if ry > tip else 0, -side * 0.4)
                if abs(px) < lim * 0.35 and abs(pz) < lim * 0.35:
                    col = mix(col, (255, 255, 255), 0.35)
                return col
        return None
    return f, (lambda col: glowing)


def lump(c, spots=None, spot_c=None, rx=4.6, ry=3.8, rz=4.0, rough=0.28, seed=1):
    """a rough chunk of rock or ore, flecked with metal"""
    def f(x, y, z):
        d = ell(x, y, z, 8, 7.6, 8, rx, ry, rz) + rough * (noise(x // 1.5, y // 1.5, z // 1.5, seed) - 0.5)
        if d < 1:
            if spots and noise(x // 1, y // 1, z // 1, seed + 5) < spots:
                return spot_c
            n = noise(x // 2, y // 2, z // 2, seed + 9)
            return shade(c, 0.85 if n < 0.3 else 1.08 if n > 0.75 else 1.0)
        return None
    return f, None


def ingot(c, stamp=None):
    """a cast bar: wider at the bottom, a bevelled top, a stamped mark"""
    def f(x, y, z):
        h = y - 5
        if not 0 <= h <= 4.0:
            return None
        hx, hz = 6.4 - h * 0.45, 3.4 - h * 0.35
        if abs(x - 8) > hx or abs(z - 8) > hz:
            return None
        if h > 3.4:
            if stamp and abs(x - 8) < 1.6 and abs(z - 8) < 0.8:
                return shade(c, 0.7)
            return mix(c, (255, 255, 255), 0.3)
        edge = abs(x - 8) > hx - 0.6 or abs(z - 8) > hz - 0.6
        return facet(c, math.copysign(0.7, x - 8) if abs(x - 8) > hx - 0.6 else 0, 0.3, math.copysign(0.7, z - 8) if abs(z - 8) > hz - 0.6 else 0.6) if edge else c
    return f, None


def nugget(c):
    def f(x, y, z):
        d = ell(x, y, z, 8, 6.4, 8, 2.8, 2.0, 2.4) + 0.3 * (noise(x // 1, y // 1, z // 1, 41) - 0.5)
        if d < 1:
            return mix(c, (255, 255, 255), 0.4) if y > 7.6 and x < 8 else c
        return None
    return f, None


def dust(c, glowing=False):
    """a little heap of powder"""
    def f(x, y, z):
        r = math.hypot(x - 8, z - 8)
        if y > 4 and y - 4 < 3.4 - r * 0.62 + 0.4 * noise(x // 1, 0, z // 1, 43):
            return shade(c, 0.85 + 0.3 * noise(x // 1, y // 1, z // 1, 47))
        return None
    return f, (lambda col: glowing)


def orb(c, c2, glowing=True, pupil=None):
    def f(x, y, z):
        d = ell(x, y, z, 8, 8, 8, 4.0, 4.0, 4.0)
        if d < 1:
            if pupil and ell(x, y, z, 8, 8, 11.6, 1.2, 2.2, 0.8) < 1:
                return pupil
            swirl = math.sin(math.atan2(z - 8, x - 8) * 3 + (y - 8) * 0.8) > 0.4
            col = c2 if swirl else c
            if ell(x, y, z, 6.8, 9.8, 10.6, 1.0, 1.0, 1.0) < 1:
                col = mix(col, (255, 255, 255), 0.6)
            return col
        return None
    return f, (lambda col: glowing and col != pupil)


def star():
    def f(x, y, z):
        dx, dy, dz = x - 8, y - 8, z - 8
        r = math.hypot(dx, dy)
        a = math.atan2(dy, dx)
        arm = 2.0 + 4.6 * max(0.0, math.cos(2.5 * a)) ** 3
        if r < arm and abs(dz) < 1.6 - r * 0.15:
            return mix((255, 255, 230), (200, 220, 255), r / 7)
        if r < 1.8 and abs(dz) < 2.2:
            return (255, 255, 255)
        return None
    return f, (lambda col: True)


def rod(c, c2, glowing=False):
    def f(x, y, z):
        if 1.0 < y < 15.0 and math.hypot(x - 8, z - 8) < 1.1:
            return c2 if int(y * 1.2) % 3 == 0 else c
        return None
    return f, (lambda col: glowing)


def bricks(c, mortar):
    def f(x, y, z):
        if 5.0 < y < 9.0 and abs(x - 8) < 5.2 and abs(z - 8) < 2.6:
            if y > 8.6 or abs(x - 8) > 4.8 or abs(z - 8) > 2.2:
                return shade(c, 0.85)
            return c if noise(x // 2, y // 2, z // 2, 53) > 0.2 else shade(c, 0.9)
        return None
    return f, None


def blob(c, c2=None, glowing=False):
    def f(x, y, z):
        d = ell(x, y, z, 8, 7.2, 8, 4.0, 3.4, 4.0)
        if d < 1:
            if d < 0.35 and c2:
                return c2
            if ell(x, y, z, 6.6, 9.2, 10.2, 1.0, 0.8, 1.0) < 1:
                return mix(c, (255, 255, 255), 0.6)
            return c
        return None
    return f, (lambda col: glowing)


def shard(c, glowing=False):
    return crystal(c, glowing, ((8, 3, 8, 1.6, 9.0, 0.15, 0.0), (6.6, 3.5, 8.6, 1.0, 6.0, -0.25, 0.1), (9.6, 3.5, 7.4, 1.0, 5.0, 0.35, -0.1)))


BATCH3 = {
    "diamond": lambda: big_gem((110, 240, 230), (220, 255, 255)),
    "emerald": lambda: emerald_cut((40, 200, 90)),
    "lapis_lazuli": lambda: lump((40, 70, 190), 0.08, (240, 210, 90), 3.6, 2.8, 3.2, 0.4, 3),
    "amethyst_shard": lambda: shard((170, 110, 230), True),
    "quartz": lambda: crystal((240, 236, 230), False, ((8, 3, 8, 1.8, 10.0, 0.1, 0), (6.4, 3.4, 8.4, 1.2, 7.0, -0.25, 0.05))),
    "echo_shard": lambda: shard((30, 90, 110), True),
    "prismarine_shard": lambda: shard((100, 180, 160)),
    "prismarine_crystals": lambda: crystal((180, 240, 220), True, ((7, 4, 8, 1.6, 6, 0, 0), (9.6, 4, 7.6, 1.4, 5, 0.2, 0), (8, 4, 10, 1.2, 4, 0, 0.2))),
    "coal": lambda: lump((40, 40, 44), 0.05, (90, 90, 100), seed=5),
    "charcoal": lambda: lump((60, 50, 40), 0.06, (100, 80, 60), seed=7),
    "flint": lambda: lump((70, 70, 76), None, None, 3.6, 3.4, 2.6, 0.5, 11),
    "clay_ball": lambda: blob((170, 176, 190)),
    "raw_iron": lambda: lump((200, 170, 150), 0.12, (230, 230, 235), seed=13),
    "raw_gold": lambda: lump((230, 180, 60), 0.12, (255, 240, 140), seed=17),
    "raw_copper": lambda: lump((200, 110, 70), 0.12, (100, 190, 150), seed=19),
    "iron_ingot": lambda: ingot((216, 218, 224), True),
    "gold_ingot": lambda: ingot((250, 205, 60), True),
    "copper_ingot": lambda: ingot((220, 120, 80), True),
    "netherite_ingot": lambda: ingot((76, 66, 72), True),
    "netherite_scrap": lambda: lump((90, 70, 70), 0.1, (255, 140, 40), 3.8, 3.0, 3.4, 0.5, 23),
    "iron_nugget": lambda: nugget((216, 218, 224)),
    "gold_nugget": lambda: nugget((250, 205, 60)),
    "redstone": lambda: dust((220, 20, 20), True),
    "glowstone_dust": lambda: dust((250, 220, 110), True),
    "gunpowder": lambda: dust((90, 90, 90)),
    "sugar": lambda: dust((245, 245, 245)),
    "blaze_powder": lambda: dust((250, 170, 40), True),
    "bone_meal": lambda: dust((240, 240, 230)),
    "ender_pearl": lambda: orb((20, 110, 100), (60, 200, 170)),
    "ender_eye": lambda: orb((40, 140, 90), (120, 220, 120), True, (20, 30, 20)),
    "heart_of_the_sea": lambda: orb((30, 80, 200), (100, 200, 250)),
    "nether_star": star,
    "blaze_rod": lambda: rod((250, 190, 40), (250, 230, 120), True),
    "brick": lambda: bricks((170, 80, 60), (200, 190, 180)),
    "nether_brick": lambda: bricks((70, 30, 40), (100, 60, 60)),
    "slime_ball": lambda: blob((110, 200, 90), (80, 160, 70)),
    "magma_cream": lambda: blob((220, 120, 40), (250, 200, 60), True),
}
FOODS_ONLY = None

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


def tilt(shape, deg=55):
    """lying flat -> tipped up toward you by deg degrees (about x, around the middle)"""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)

    def f(x, y, z):
        y0, z0 = y - 8, z - 8
        return shape(x, 8 + y0 * ca + z0 * sa - 2.5, 8 - y0 * sa + z0 * ca)
    return f


FACETED = {"diamond", "emerald", "amethyst_shard", "quartz", "echo_shard", "prismarine_shard", "prismarine_crystals", "iron_ingot",
           "gold_ingot", "copper_ingot", "netherite_ingot", "nether_star"}
TILTED = {"iron_ingot", "gold_ingot", "copper_ingot", "netherite_ingot", "redstone", "glowstone_dust", "gunpowder", "sugar",
          "blaze_powder", "bone_meal", "brick", "nether_brick", "iron_nugget", "gold_nugget"}


def stand(shape):
    """lying flat -> standing up facing you (top toward +z)"""
    return lambda x, y, z: shape(x, z, 16 - y)


def layered_gem(name, c, core, profile, glow_core=True):
    """a gem from square layers turned 45 degrees: each side of a layer is one clean, evenly lit facet"""
    faces_c = {"up": mix(c, (255, 255, 255), 0.45), "down": shade(c, 0.55), "north": shade(c, 0.85), "south": mix(c, (255, 255, 255), 0.2),
               "east": shade(c, 0.7), "west": c}
    tex = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    uv = {}
    for i, (k, col) in enumerate(list(faces_c.items()) + [("core", core)]):
        for dx in range(2):
            for dy in range(2):
                tex.putpixel((i * 2 + dx, dy), col + (255,))
        uv[k] = [i * 2 + 0.1, 0.1, i * 2 + 1.9, 1.9]
    els = []
    for (y0, y1, half) in profile:
        faces = {k: {"uv": uv[k], "texture": "#t"} for k in faces_c}
        els.append({"from": [8 - half, y0, 8 - half], "to": [8 + half, y1, 8 + half], "faces": faces, "shade": False,
                    "rotation": {"angle": 45, "axis": "y", "origin": [8, 8, 8]}})
    if glow_core:
        els.append({"from": [7.2, 4.0, 7.2], "to": [8.8, 8.6, 8.8], "faces": {k: {"uv": uv["core"], "texture": "#t"} for k in faces_c},
                    "forge_data": {"block_light": 15, "sky_light": 15}, "shade": False,
                    "rotation": {"angle": 45, "axis": "y", "origin": [8, 8, 8]}})
    tname = f"item/food/{name}"
    tex.save(os.path.join(PACK, "assets", NS, "textures", tname + ".png"))
    s_ = 0.55
    display = {
        "thirdperson_righthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.5] * 3},
        "thirdperson_lefthand": {"rotation": [0, 0, 0], "translation": [0, 3, 1], "scale": [0.5] * 3},
        "firstperson_righthand": {"rotation": [10, -70, 15], "translation": [0, 4.6, 0], "scale": [s_] * 3},
        "firstperson_lefthand": {"rotation": [10, 70, -15], "translation": [0, 4.6, 0], "scale": [s_] * 3},
        "ground": {"rotation": [0, 0, 0], "translation": [0, 2, 0], "scale": [0.5] * 3},
        "fixed": {"rotation": [0, 180, 0], "scale": [1, 1, 1]},
        "head": {"rotation": [0, 180, 0], "translation": [0, 13, 7], "scale": [1, 1, 1]},
    }
    with open(os.path.join(PACK, "assets", NS, "models", "item3d", name + ".json"), "w") as f:
        json.dump({"textures": {"t": f"{NS}:{tname}", "particle": f"{NS}:{tname}"}, "display": display, "elements": els}, f,
                  separators=(",", ":"))
    gui = "minecraft:item/" + name
    with open(os.path.join(PACK, "assets", "minecraft", "models", "item", name + ".json"), "w") as f:
        json.dump({"loader": "forge:separate_transforms", "textures": {"particle": gui}, "base": {"parent": f"{NS}:item3d/{name}"},
                   "perspectives": {"gui": {"parent": "minecraft:item/generated", "textures": {"layer0": gui}}}}, f, separators=(",", ":"))


# the pavilion narrows to a point below; the crown steps in to a flat table on top
DIAMOND_PROFILE = [(2.0, 3.2, 0.6), (3.2, 4.4, 1.5), (4.4, 5.6, 2.4), (5.6, 6.8, 3.3), (6.8, 8.0, 4.1), (8.0, 9.0, 4.4),
                   (9.0, 10.0, 3.7), (10.0, 10.9, 3.0), (10.9, 11.6, 2.2)]

n = 0
for name, make in list(FOODS.items()) + list(BATCH3.items()):
    if name == "diamond":
        if not ONLY or name in ONLY:
            layered_gem("diamond", (110, 240, 230), (230, 255, 255), DIAMOND_PROFILE)
            n += 1
        continue
    if ONLY and name not in ONLY:
        continue
    shape, glow = make()
    if name in FLAT:
        shape = stand(shape)
    if name in TILTED:
        shape = tilt(shape)
    els = Food(name).build(shape, glow or (lambda c: False), layer_light=name not in FACETED,
                           scale=0.8 if name == "emerald" else 1.15 if name in ("diamond", "iron_nugget", "gold_nugget") else 1.0)
    n += 1
    print(f"{name}: {els} boxes")
print("made", n, "foods")
