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

PACK = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("LM_PACK", "")
JAR = os.environ.get("MC_JAR", "/tmp/mcjar/client.jar")
ONLY = set(sys.argv[2:])
NS = "lifelikemotion"
STEP = 0.5
TINT = (253, 253, 253)
TINT2 = (252, 252, 252)
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
    def __init__(self, name, gui=None, overrides=None, gui_layers=None, gui_parent=None, write_item=True):
        self.name = name
        self.gui_parent = gui_parent
        self.write_item = write_item
        self.gui = gui
        self.overrides = overrides
        self.gui_layers = gui_layers

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
        # hidden voxels are kept so the boxes can run straight through the inside.
        # A colour can be (r, g, b, alpha) for glass, or TINT for the part the game colours (potions, tipped arrows)
        lit = {}
        for (ix, iy, iz), c in grid.items():
            k = 0.8 + 0.34 * round((iy + 1) / N * 6) / 6 if layer_light else 1.0
            tint = 1 if c == TINT else 2 if c == TINT2 else 0
            a = c[3] if len(c) == 4 else 255
            rgb = shade(c[:3], k)
            lit[(ix, iy, iz)] = (rgb + (a,), glow(c[:3]), tint)
        clear = {v for v, key in lit.items() if key[0][3] < 255}
        translucent = bool(clear)
        colours = sorted({v for v in lit.values()})
        tex = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        uv = {}
        per_row = 64
        for i, key in enumerate(colours):
            px, py = (i % per_row) * 2, (i // per_row) * 2
            if py >= 128:
                raise RuntimeError(f"{self.name}: too many colours")
            for dx in range(2):
                for dy in range(2):
                    tex.putpixel((px + dx, py + dy), key[0])
            s_ = 16 / 128
            uv[key] = [px * s_ + 0.02, py * s_ + 0.02, (px + 2) * s_ - 0.02, (py + 2) * s_ - 0.02]

        def blocks(cell, other):
            """does a neighbour hide this face? empty never does; glass hides only glass"""
            if other not in grid:
                return False
            if other in clear and cell not in clear:
                return False
            return True

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
            for name, d in (("west", (-1, 0, 0)), ("east", (1, 0, 0)), ("up", (0, 1, 0)), ("down", (0, -1, 0)),
                            ("south", (0, 0, 1)), ("north", (0, 0, -1))):
                if any(not blocks(cell, (cell[0] + d[0], cell[1] + d[1], cell[2] + d[2])) for cell in cells):
                    faces[name] = {"uv": u, "texture": "#t"}
                    if key[2]:
                        faces[name]["tintindex"] = key[2] - 1
            if not faces:
                continue
            e = {"from": [ix * STEP, iy * STEP, iz * STEP], "to": [(jx + 1) * STEP, (iy + 1) * STEP, (jz + 1) * STEP],
                 "faces": faces, "shade": False}
            if key[1]:
                e["forge_data"] = {"block_light": 15, "sky_light": 15}
            els.append(e)
        self.translucent = translucent
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
        if self.translucent:
            model["render_type"] = "minecraft:translucent"
        mp = os.path.join(PACK, "assets", NS, "models", "item3d", self.name + ".json")
        with open(mp, "w") as f:
            json.dump(model, f, separators=(",", ":"))
        gui = "minecraft:item/" + (self.gui or self.name)
        item = {"loader": "forge:separate_transforms", "textures": {"particle": gui}, "base": {"parent": f"{NS}:item3d/{self.name}"},
                "perspectives": {"gui": {"parent": self.gui_parent or "minecraft:item/generated", "textures": self.gui_layers or {"layer0": gui}}}}
        if self.gui_parent:
            item["perspectives"]["gui"].pop("textures")
        if not self.write_item:
            return len(els)
        if self.overrides:
            item["overrides"] = self.overrides
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

# ---------------------------------------------------------------- batch 4: potions, buckets, books, gear
GLASS = (200, 235, 245, 110)


def bottle(liquid, kind="potion", glowing=False):
    """a glass bottle (round, splash = squat with a ring, lingering = tall neck) with liquid inside and a cork"""
    neck_top = {"potion": 12.6, "splash": 11.6, "lingering": 13.6, "empty": 12.6}[kind]
    ry = 3.4 if kind != "splash" else 3.0

    def f(x, y, z):
        r = math.hypot(x - 8, z - 8)
        body = ell(x, y, z, 8, 6.2, 8, 3.8, ry, 3.8)
        if body < 1:
            if liquid and body < 0.72 and y < 7.4:
                return liquid
            if body > 0.72:
                if ell(x, y, z, 6.6, 7.6, 11.2, 0.8, 1.2, 0.6) < 1:
                    return (255, 255, 255, 200)
                return GLASS
            return None
        if 8.6 <= y < neck_top and r < 1.5:
            if r < 0.9 and liquid and kind == "lingering" and y < 10:
                return liquid
            return GLASS if r > 0.9 else None
        if neck_top <= y < neck_top + 1.4 and r < 1.3:
            return (170, 120, 70)
        if kind == "splash" and 9.6 < y < 10.4 and 1.5 <= r < 2.1:
            return (200, 200, 210)
        return None
    return f, (lambda c: glowing and c == liquid[:3])


def bucket(fill=None, fill_glow=False, fish=None):
    """a tin bucket with a rim and a handle; full of something, or with a fish in water"""
    def f(x, y, z):
        r = math.hypot(x - 8, z - 8)
        top_r = 4.6
        lim = 3.4 + (y - 3) / 8 * (top_r - 3.4)
        if 3 <= y < 11 and r < lim:
            if r > lim - 0.7 or y < 3.7:
                if y > 10.2:
                    return (230, 232, 238)
                return (190, 194, 202) if int(y) % 3 else (160, 164, 172)
            if fill and y > 9.4:
                if fish and math.hypot(x - 8, z - 8.5) < 1.8 and abs(z - 8) < 1.4 and y > 10.2:
                    return fish
                return fill
            return None
        # handle: an arc over the top
        if abs(z - 8) < 0.4:
            a = math.atan2(y - 10.4, x - 8)
            d = math.hypot(x - 8, y - 10.4)
            if 0 < a < math.pi and abs(d - 4.4) < 0.35:
                return (120, 124, 132)
        if fish and 11.0 <= y < 12.6 and abs(z - 8) < 0.4 and 6.6 < x < 9.6:
            return fish
        return None
    return f, (lambda c: fill_glow and fill and c == fill[:3])


def book(cover, pages=(240, 232, 210), extra=None, rune=None):
    """a thick book standing up: covers, a spine, page edges; a quill, a ribbon or glowing runes"""
    def f(x, y, z):
        if not (3 <= x < 13 and 1.5 <= y < 14.5 and 5.6 <= z < 10.4):
            if extra == "quill" and 11 <= x < 12 and 9 <= y < 16 and 10.4 <= z < 11.2:
                return (240, 240, 240) if y > 12 else (60, 60, 60)
            if extra == "ribbon" and 9.0 <= x < 10.0 and 0.0 <= y < 1.5 and 7.6 <= z < 8.4:
                return (200, 40, 40)
            return None
        if x < 4.0:
            return shade(cover, 0.8)
        if z < 6.3 or z >= 9.7:
            if rune and 6 < x < 11 and 4 < y < 12 and (int(x) + int(y)) % 3 == 0:
                return rune
            if 5 < x < 12 and abs(y - 8) < 0.4:
                return (220, 180, 70)
            return cover
        if y < 2.2 or y >= 13.8 or x >= 12.3:
            return pages if int(y * 2 + z) % 2 else shade(pages, 0.88)
        return None
    return f, (lambda c: rune is not None and c == rune)


def dial(face, rim, hand_angle, hand=(200, 40, 40), back=(160, 40, 40), night=None):
    """a round dial facing you: rim, face, a needle (compass) or a hand over a day/night disc (clock)"""
    a = math.radians(hand_angle)

    def f(x, y, z):
        dx, dy = x - 8, y - 8
        r = math.hypot(dx, dy)
        if r > 5.6 or abs(z - 8) > 1.4:
            return None
        if r > 4.8:
            return rim if z > 7.0 else shade(rim, 0.8)
        if z < 8.6:
            if night is not None:
                # the clock: a day/night disc turned with the time (sun half up, moon half down)
                t = math.atan2(dy, dx) - a
                return night[0] if math.sin(t) > 0 else night[1]
            return face
        # the needle: a line from the centre (red end toward the angle, grey behind)
        ax, ay = math.sin(a), math.cos(a)
        along = dx * ax + dy * ay
        across = abs(-dx * ay + dy * ax)
        if z < 9.4 and across < 0.55 - abs(along) * 0.07 and abs(along) < 4.2:
            return hand if along > 0 else back
        if z < 9.4 and r < 0.7:
            return (230, 230, 230)
        return None
    return f, (lambda c: False)


def coil(c, c2=None, thick=0.7):
    def f(x, y, z):
        d = math.hypot(math.hypot(x - 8, z - 8) - 3.4, (y - 7) * 1.2)
        if d < thick + 0.3:
            return c2 if c2 and int(math.atan2(z - 8, x - 8) * 4) % 2 else c
        if 6 < y < 8 and 11 < x < 14 and abs(z - 8) < 0.5:
            return c
        return None
    return f, None


def sheet(c, curl=True, marks=None):
    def f(x, y, z):
        if not (3 <= x < 13 and 2 <= y < 14):
            return None
        zc = 8 + (math.sin((x - 3) / 10 * math.pi) * 1.2 if curl else 0)
        if abs(z - zc) < 0.4:
            if marks and (int(y) % 3 == 0) and 4.5 < x < 11.5:
                return marks
            return c
        return None
    return f, None


def feather():
    def f(x, y, z):
        if abs(z - 8) > 0.4:
            return None
        t = (y - 2) / 12
        if 0 <= t <= 1 and abs(x - 8 - math.sin(t * 2) * 0.8) < 0.35:
            return (220, 220, 220)
        if 0.2 <= t <= 1:
            w = 2.6 * math.sin((t - 0.2) / 0.8 * math.pi) ** 0.7
            if abs(x - 8 - math.sin(t * 2) * 0.8) < w:
                return (245, 245, 245) if int((x + y) * 1.2) % 4 else (215, 215, 220)
        return None
    return f, None


def arrow(head=(200, 200, 210), glowing=False, tint=False):
    def f(x, y, z):
        if abs(z - 8) > 0.45 or abs(x - 8) > 2.4:
            return None
        if 2 <= y < 12.4 and abs(x - 8) < 0.45:
            return (150, 110, 70)
        if 12.4 <= y < 15.4 and abs(x - 8) < (15.4 - y) * 0.7:
            return TINT if tint else head
        if 2 <= y < 5 and abs(x - 8) < 1.8 - (y - 2) * 0.2:
            return (240, 240, 240)
        return None
    return f, (lambda c: glowing and c == head)


def bone():
    def f(x, y, z):
        if 3 <= y < 13 and math.hypot(x - 8, z - 8) < 0.9:
            return (236, 230, 214)
        for (cx, cy) in ((7.0, 2.6), (9.0, 2.6), (7.0, 13.4), (9.0, 13.4)):
            if ell(x, y, z, cx, cy, 8, 1.3, 1.3, 1.1) < 1:
                return (236, 230, 214)
        return None
    return f, None


def stick():
    def f(x, y, z):
        if 1 <= y < 15 and math.hypot(x - 8, z - 8) < 0.75:
            return (130, 95, 55) if int(y) % 4 else (105, 75, 45)
        if 8 <= y < 10 and 8.5 < x < 10.5 and abs(z - 8) < 0.4:
            return (110, 80, 48)
        return None
    return f, None


def totem():
    def f(x, y, z):
        if abs(z - 8) > 1.2:
            return None
        if ell(x, y, z, 8, 11, 8, 2.6, 2.4, 1.2) < 1:
            if 9.4 < y < 11 and abs(abs(x - 8) - 1.1) < 0.5:
                return (40, 200, 90)
            return (240, 200, 80)
        if 3 <= y < 9 and abs(x - 8) < 2.2:
            return (220, 170, 60) if int(y) % 2 else (240, 200, 90)
        if 6 <= y < 8.6 and 2.6 <= abs(x - 8) < 5.4:
            return (230, 190, 70)
        if 1 <= y < 3 and abs(abs(x - 8) - 1.1) < 0.7:
            return (220, 170, 60)
        return None
    return f, (lambda c: c == (40, 200, 90))


def ball(c, c2=None, glowing=False, r=3.0):
    def f(x, y, z):
        d = ell(x, y, z, 8, 7.5, 8, r, r, r)
        if d < 1:
            if ell(x, y, z, 6.8, 8.8, 10.2, 0.9, 0.8, 0.9) < 1:
                return mix(c, (255, 255, 255), 0.6)
            if c2 and noise(x // 1, y // 1, z // 1, 61) < 0.2:
                return c2
            return c
        return None
    return f, (lambda col: glowing)


def egg():
    def f(x, y, z):
        if ell(x, y, z, 8, 7.4, 8, 2.6, 3.4 if y > 7.4 else 2.8, 2.6) < 1:
            if noise(x // 1, y // 1, z // 1, 67) < 0.1:
                return (200, 170, 130)
            return (240, 226, 196)
        return None
    return f, None


def rocket():
    def f(x, y, z):
        r = math.hypot(x - 8, z - 8)
        if 2 <= y < 11 and r < 1.8:
            return (200, 40, 40) if int(y) % 3 else (240, 240, 240)
        if 11 <= y < 13.4 and r < 1.8 - (y - 11) * 0.7:
            return (60, 60, 60)
        if 0 <= y < 2 and r < 0.5:
            return (150, 150, 150)
        return None
    return f, None


def name_tag():
    def f(x, y, z):
        if abs(z - 8) > 0.5:
            return None
        if 3 <= x < 13 and 5 <= y < 11 and not (x < 4.5 and abs(y - 8) > 1.6):
            if ell(x, y, 8, 4.6, 8, 8, 0.6, 0.6, 1) < 1:
                return None
            return (210, 180, 130) if 5 < x < 12 and 6 < y < 10 else (180, 150, 100)
        if abs(math.hypot(x - 3.2, y - 8) - 1.4) < 0.3:
            return (150, 150, 150)
        return None
    return f, None


def saddle():
    def f(x, y, z):
        d = ell(x, y, z, 8, 7, 8, 5.2, 3.0, 3.6)
        if d < 1 and y > 6:
            if y < 7.2:
                return (110, 60, 30)
            return (150, 85, 45) if abs(x - 8) > 1 else (130, 70, 38)
        if abs(abs(x - 8) - 3.4) < 0.4 and 2 < y < 7 and abs(z - 8) < 0.6:
            return (90, 50, 25)
        if abs(abs(x - 8) - 3.4) < 0.9 and 1.4 < y < 2.6 and abs(z - 8) < 0.6:
            return (190, 190, 200)
        return None
    return f, None


def hide(c, c2):
    def f(x, y, z):
        if abs(z - 8 - math.sin(x * 0.6) * 0.5) > 0.45:
            return None
        if ell(x, y, 8, 8, 8, 8, 5.2, 5.6, 1) < 1 + 0.15 * math.sin(math.atan2(y - 8, x - 8) * 5):
            return c2 if noise(x // 2, y // 2, 0, 71) < 0.2 else c
        return None
    return f, None


def shell():
    def f(x, y, z):
        d = math.hypot(x - 8, y - 7.6)
        a = math.atan2(y - 7.6, x - 8)
        if d < 5 and abs(z - 8) < 2.2 - d * 0.25:
            ring = (d + a * 0.6) % 1.6
            return (240, 220, 200) if ring > 0.4 else (200, 120, 90)
        return None
    return f, None


def tear():
    def f(x, y, z):
        r = math.hypot(x - 8, z - 8)
        if 4 <= y < 12 and r < (2.6 * math.sin((y - 4) / 8 * math.pi * 0.85) if y < 10 else 1.8 - (y - 10) * 0.8):
            return (220, 240, 255) if r < 0.8 else (180, 220, 240)
        return None
    return f, (lambda c: True)


def ink(c, glowing=False):
    def f(x, y, z):
        if ell(x, y, z, 8, 7, 8, 3.4, 3.0, 3.0) < 1:
            return c if y < 8.4 else shade(c, 1.3)
        if 3 <= y < 4.2 and abs(x - 8) < 2.4 and abs(z - 8) < 0.8 and int(x) % 2 == 0:
            return shade(c, 0.8)
        return None
    return f, (lambda col: glowing)


def honeycomb():
    def f(x, y, z):
        if abs(z - 8) > 1.4 or math.hypot(x - 8, y - 8) > 5.2:
            return None
        cx, cy = x - 8, y - 8
        if abs(math.sin(cx * 1.4)) < 0.25 or abs(math.sin((cx * 0.5 + cy * 0.87) * 1.4)) < 0.25:
            return (220, 150, 30)
        return (250, 200, 60) if z > 8.6 else (230, 170, 40)
    return f, None


def map_paper(inked=False):
    def f(x, y, z):
        if abs(z - 8 - math.sin(x * 0.5) * 0.5) > 0.4 or not (2 <= x < 14 and 2 <= y < 14):
            return None
        if x < 2.8 or x >= 13.2:
            return (200, 170, 120)
        if inked and noise(x // 2, y // 2, 0, 73) < 0.4:
            return (120, 170, 90)
        return (236, 220, 180)
    return f, None


def fire_charge():
    def f(x, y, z):
        if ell(x, y, z, 8, 7.5, 8, 3.2, 3.2, 3.2) < 1:
            n = noise(x // 1, y // 1, z // 1, 79)
            return (250, 200, 60) if n > 0.6 else (230, 110, 30) if n > 0.25 else (90, 40, 30)
        return None
    return f, (lambda c: c != (90, 40, 30))


def fish_bucket(fish):
    return bucket((60, 110, 220, 200), False, fish)


BATCH4 = {
    "potion": lambda: bottle(TINT),
    "splash_potion": lambda: bottle(TINT, "splash"),
    "lingering_potion": lambda: bottle(TINT, "lingering"),
    "glass_bottle": lambda: bottle(None, "empty"),
    "experience_bottle": lambda: bottle((120, 250, 80), "potion", True),
    "honey_bottle": lambda: bottle((240, 170, 40), "potion"),
    "dragon_breath": lambda: bottle((220, 120, 200), "potion", True),
    "bucket": lambda: bucket(),
    "water_bucket": lambda: bucket((60, 110, 220, 200)),
    "lava_bucket": lambda: bucket((250, 120, 30), True),
    "milk_bucket": lambda: bucket((250, 250, 245)),
    "powder_snow_bucket": lambda: bucket((240, 246, 255)),
    "cod_bucket": lambda: fish_bucket((180, 150, 110)),
    "salmon_bucket": lambda: fish_bucket((200, 70, 60)),
    "pufferfish_bucket": lambda: fish_bucket((240, 200, 60)),
    "tropical_fish_bucket": lambda: fish_bucket((250, 130, 40)),
    "axolotl_bucket": lambda: fish_bucket((240, 150, 190)),
    "tadpole_bucket": lambda: fish_bucket((80, 60, 40)),
    "book": lambda: book((140, 70, 40)),
    "writable_book": lambda: book((110, 80, 50), extra="quill"),
    "written_book": lambda: book((90, 60, 40), extra="ribbon"),
    "enchanted_book": lambda: book((110, 40, 120), rune=(220, 140, 255)),
    "knowledge_book": lambda: book((160, 40, 40), rune=(250, 210, 90)),
    "name_tag": name_tag,
    "lead": lambda: coil((170, 130, 90), (140, 100, 70)),
    "string": lambda: coil((240, 240, 240), None, 0.35),
    "saddle": saddle,
    "paper": lambda: sheet((240, 236, 220)),
    "map": lambda: map_paper(),
    "feather": feather,
    "leather": lambda: hide((150, 85, 45), (120, 65, 35)),
    "rabbit_hide": lambda: hide((200, 160, 120), (170, 130, 95)),
    "phantom_membrane": lambda: hide((200, 210, 190), (170, 190, 160)),
    "bone": bone,
    "stick": stick,
    "arrow": lambda: arrow(),
    "spectral_arrow": lambda: arrow((250, 220, 80), True),
    "tipped_arrow": lambda: arrow(tint=True),
    "egg": egg,
    "snowball": lambda: ball((250, 252, 255), (225, 235, 245)),
    "totem_of_undying": totem,
    "fire_charge": fire_charge,
    "firework_rocket": rocket,
    "ink_sac": lambda: ink((40, 40, 60)),
    "glow_ink_sac": lambda: ink((60, 200, 190), True),
    "scute": lambda: hide((80, 170, 60), (60, 140, 50)),
    "nautilus_shell": shell,
    "ghast_tear": tear,
    "honeycomb": honeycomb,
    "rabbit_foot": lambda: ball((200, 160, 120), (170, 130, 95), r=2.6),
}
GUI_LAYERS = {
    "potion": {"layer0": "minecraft:item/potion_overlay", "layer1": "minecraft:item/potion"},
    "splash_potion": {"layer0": "minecraft:item/potion_overlay", "layer1": "minecraft:item/splash_potion"},
    "lingering_potion": {"layer0": "minecraft:item/potion_overlay", "layer1": "minecraft:item/lingering_potion"},
    "tipped_arrow": {"layer0": "minecraft:item/tipped_arrow_head", "layer1": "minecraft:item/tipped_arrow_base"},
}


def dials():
    """compass and recovery compass (32 needles each) and clock (64 hands): every state is its own 3D model"""
    import zipfile as _z
    made = 0
    for base, count, face, rim, kind in (("compass", 32, (220, 214, 200), (120, 124, 132), "compass"),
                                         ("recovery_compass", 32, (30, 50, 60), (60, 90, 110), "compass"),
                                         ("clock", 64, None, (236, 190, 60), "clock")):
        for i in range(count):
            nm = f"{base}_{i:02d}"
            if kind == "compass":
                ang = (i - 16) / 32 * 360
                shape = dial(face, rim, ang, (220, 40, 40) if base == "compass" else (100, 240, 230), (170, 170, 175))
            else:
                ang = i / 64 * 360
                shape = dial(None, rim, ang, night=((120, 190, 250), (30, 40, 90)))
            fd = Food(nm)
            fd.build(shape[0], shape[1] or (lambda c: False))
            made += 1
        # the item itself: our model of its starting state, the game's own list of states
        vanilla = json.loads(_z.ZipFile(JAR).read(f"assets/minecraft/models/item/{base}.json"))
        start = vanilla["textures"]["layer0"].split("/")[-1]
        item = {"loader": "forge:separate_transforms", "textures": {"particle": f"minecraft:item/{start}"},
                "base": {"parent": f"{NS}:item3d/{start}"},
                "perspectives": {"gui": {"parent": "minecraft:item/generated", "textures": {"layer0": f"minecraft:item/{start}"}}},
                "overrides": vanilla["overrides"]}
        with open(os.path.join(PACK, "assets", "minecraft", "models", "item", base + ".json"), "w") as f:
            json.dump(item, f, separators=(",", ":"))
    return made


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
TILTED = {"bucket", "water_bucket", "lava_bucket", "milk_bucket", "powder_snow_bucket", "cod_bucket", "salmon_bucket", "pufferfish_bucket",
          "tropical_fish_bucket", "axolotl_bucket", "tadpole_bucket", "lead", "string", "saddle", "iron_ingot", "gold_ingot", "copper_ingot", "netherite_ingot", "redstone", "glowstone_dust", "gunpowder", "sugar",
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

def main():
    n = 0
    if not ONLY or "dials" in ONLY:
        n += dials()
    for name, make in list(FOODS.items()) + list(BATCH3.items()) + list(BATCH4.items()):
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
        els = Food(name, gui_layers=GUI_LAYERS.get(name)).build(shape, glow or (lambda c: False), layer_light=name not in FACETED,
                               scale=0.8 if name == "emerald" else 0.75 if "book" in name else 1.15 if name in ("diamond", "iron_nugget", "gold_nugget") else 1.0)
        n += 1
        print(f"{name}: {els} boxes")
    print("made", n, "foods")


if __name__ == "__main__":
    main()
