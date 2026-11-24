#!/usr/bin/env python3
"""Renders Minecraft JSON item models (boxes with textures, as made by tools/models.py) in Blender, side by side,
lit roughly like the game, for checking a model outside the game.

    python3 tools/blender/preview_json.py <pack dir> <out.png> name [name...]
"""
import json
import math
import os
import sys

import bpy  # noqa: must come before bmesh
import bmesh
from mathutils import Matrix, Vector
from PIL import Image

PACK, OUT, NAMES = sys.argv[1], sys.argv[2], sys.argv[3:]
NS = "lifelikemotion"
TINT = (0.22, 0.42, 0.9, 1)  # a sample potion colour (water)


def tex_path(ref):
    """a texture file: from the pack, or the game's own (from the jar; animated strips cut to their first frame)"""
    ns, path = ref.split(":") if ":" in ref else ("minecraft", ref)
    p = os.path.join(PACK, "assets", ns, "textures", path + ".png")
    if os.path.exists(p):
        return p
    import io
    import zipfile
    out = f"/tmp/claude-0/mctex/{ns}/{path}.png"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with zipfile.ZipFile(os.environ.get("MC_JAR", "/tmp/mcjar/client.jar")) as z:
        im = Image.open(io.BytesIO(z.read(f"assets/{ns}/textures/{path}.png"))).convert("RGBA")
    im.crop((0, 0, im.width, im.width)).save(out)
    return out


def corners_for(face, f, t):
    """the face's four corners in Minecraft space, in uv order: (u0,v0) (u1,v0) (u1,v1) (u0,v1)"""
    x0, y0, z0 = f
    x1, y1, z1 = t
    return {
        "north": [(x1, y1, z0), (x0, y1, z0), (x0, y0, z0), (x1, y0, z0)],
        "south": [(x0, y1, z1), (x1, y1, z1), (x1, y0, z1), (x0, y0, z1)],
        "east": [(x1, y1, z1), (x1, y1, z0), (x1, y0, z0), (x1, y0, z1)],
        "west": [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
        "up": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
        "down": [(x0, y0, z1), (x1, y0, z1), (x1, y0, z0), (x0, y0, z0)],
    }[face]


def load(name):
    with open(os.path.join(PACK, "assets", NS, "models", "item3d", name + ".json")) as fh:
        model = json.load(fh)
    order = []
    mats = {}
    for key, ref in model["textures"].items():
        if key == "particle":
            continue
        img = bpy.data.images.load(tex_path(ref))
        for tinted in (False, True):
            mats[(key, tinted)] = make_mat(f"{name}_{key}_{tinted}", img, tinted)
            order.append((key, tinted))
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("uv")
    s = 1 / 16
    for el in model["elements"]:
        rot = el.get("rotation")
        R = Matrix.Identity(4)
        if rot:
            o = Vector(rot["origin"])
            R = Matrix.Translation(o) @ Matrix.Rotation(math.radians(rot["angle"]), 4, rot["axis"].upper()) \
                @ Matrix.Translation(-o)
        for face, fd in el["faces"].items():
            u0, v0, u1, v1 = [c / 16 for c in fd["uv"]]
            cs = corners_for(face, el["from"], el["to"])
            vs = []
            for c in cs:
                p = R @ Vector(c)
                vs.append(bm.verts.new((p.x * s, 1 - p.z * s, p.y * s)))  # MC -> Blender axes
            try:
                fc = bm.faces.new(vs)
            except ValueError:
                continue
            fc.material_index = order.index((fd["texture"][1:], "tintindex" in fd))
            for loop, (u, v) in zip(fc.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                loop[uvl].uv = (u, 1 - v)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for k in order:
        me.materials.append(mats[k])
    return ob


def make_mat(mname, img, tinted):
    if True:
        m = bpy.data.materials.new(mname)
        m.use_nodes = True
        nt = m.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        bsdf.inputs["Roughness"].default_value = 1.0
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = img
        tx.interpolation = "Closest"
        last = tx.outputs["Color"]
        if tinted:
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0
            mix.inputs[7].default_value = TINT
            nt.links.new(last, mix.inputs[6])
            last = mix.outputs[2]
        nt.links.new(last, bsdf.inputs["Base Color"])
        nt.links.new(tx.outputs["Alpha"], bsdf.inputs["Alpha"])
        return m


def render(ob, out):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 64
    sc.cycles.use_denoising = False
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = 420
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.42, 0.5, 0.62, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    sc.world = w
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    sc.collection.objects.link(cam)
    sc.camera = cam
    bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    ctr = sum(bb, Vector()) / 8
    size = max((max(v[i] for v in bb) - min(v[i] for v in bb)) for i in range(3))
    cam.location = ctr + Vector((size * 1.1, -size * 1.8, size * 1.0))
    cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 2.0
    sun.rotation_euler = (0.7, 0.2, -0.5)
    sc.collection.objects.link(sun)
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


pics = []
for n in NAMES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob = load(n)
    p = f"/tmp/claude-0/pv_{n}.png"
    render(ob, p)
    pics.append(p)
ims = [Image.open(p).convert("RGB") for p in pics]
sheet = Image.new("RGB", (420 * len(ims), 420))
for i, im in enumerate(ims):
    sheet.paste(im, (420 * i, 0))
sheet.save(OUT)
