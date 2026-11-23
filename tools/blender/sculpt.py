#!/usr/bin/env python3
"""Real shapes wearing Minecraft's own pictures: a round apple, a sword with rounded edges and a raised ridge, a round
potion bottle. Each item is a smooth solid (built from a distance field with marching cubes, then thinned out), the
vanilla item picture laid onto it pixel for pixel (crisp, the game's own texture), and soft shadows baked into the
vertices so the game's light rolls over it like a real object.

Runs with Blender's Python module:  python3 tools/blender/sculpt.py <pack dir> [names...] [--preview out.png]
"""
import math
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.measure import marching_cubes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import items as K  # noqa: E402  (loads Blender)
import voxel as V  # noqa: E402
import bpy  # noqa: E402
import bmesh  # noqa: E402

RES = 4  # samples per picture pixel, across
ZRES = 4  # samples per pixel, in depth


def up(a, sigma=0.0):
    """a per-pixel map at RES samples per pixel (optionally softened)"""
    b = np.kron(a.astype(float), np.ones((RES, RES)))
    return ndimage.gaussian_filter(b, sigma * RES) if sigma else b


# ---------------------------------------------------------------- shapes (distance fields: > 0 inside)
def flat_field(solid, half):
    """a flat item puffed into a smooth solid: half[y, x] is each pixel's half thickness; edges round off and
    the stair-step outline of the picture smooths into clean lines"""
    inside = up(solid, 0.45) > 0.5
    d_in = ndimage.distance_transform_edt(inside) / RES
    d_out = ndimage.distance_transform_edt(~inside) / RES
    t = np.maximum(up(np.where(solid, half, 0.0), 0.7), 0.25)
    h = np.where(inside, t * np.sqrt(np.clip(1 - np.clip(1 - d_in / t, 0, 1) ** 2, 0, 1)), -d_out)
    return lambda z: h - np.abs(z)


def round_field(solid):
    """a round item: each row of the picture is a round slice (smoothed from row to row), so an apple is an apple"""
    n = solid.shape[0]
    g = n * RES
    a = up(solid, 0.5) > 0.5
    cx = np.zeros(g)
    r = np.full(g, -1.0)
    for y in range(g):
        xs = np.nonzero(a[y])[0]
        if len(xs):
            cx[y] = (xs.min() + xs.max() + 1) / 2 / RES
            r[y] = (xs.max() + 1 - xs.min()) / 2 / RES
    ok = r > 0
    r_s = np.where(ok, ndimage.gaussian_filter1d(np.where(ok, r, 0), 1.2), -1)
    r_s = np.where(ok, np.maximum(r_s, 0.35), -1)
    xg = (np.arange(g) + 0.5) / RES

    def f(z):
        dx = xg[None, :, None] - cx[:, None, None]
        return np.where(ok[:, None, None], r_s[:, None, None] - np.sqrt(dx ** 2 + z ** 2), -1.0)
    return f, cx, r_s


def mesh_from_field(name, f, n, zmax, material, target=1300, three_d=False):
    g = n * RES
    nz = int(math.ceil(zmax * ZRES)) + 2
    zs = (np.arange(-nz, nz + 1)) / ZRES
    if three_d:
        vol = f(zs[None, None, :])
    else:
        hz = f(0)  # h(x, y) - |0| = h
        vol = hz[:, :, None] - np.abs(zs[None, None, :])
    vol = np.pad(vol, 1, constant_values=-1.0)
    verts, faces, _, _ = marching_cubes(vol, level=0.0)
    verts -= 1  # the padding
    # sample grid -> picture pixels (y down, x right) and depth
    py = (verts[:, 0] + 0.5) / RES
    px = (verts[:, 1] + 0.5) / RES
    pz = zs[0] + verts[:, 2] / ZRES
    s = 1.0 / n
    bm = bmesh.new()
    bv = [bm.verts.new((x * s, K.C + z * s, (n - y) * s)) for y, x, z in zip(py, px, pz)]
    for a, b, c in faces:
        try:
            bm.faces.new((bv[a], bv[b], bv[c]))
        except ValueError:
            pass
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = K.obj_from_bm(name, bm, material, smooth=True)
    # thin it out: far fewer faces, same shape
    K.modifier(ob, "DECIMATE", ratio=min(1.0, target / max(len(ob.data.polygons), 1)))
    # quads where they fit (the game draws quads)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.tris_convert_to_quads(face_threshold=math.radians(30), shape_threshold=math.radians(30))
    bpy.ops.object.mode_set(mode="OBJECT")
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


# ---------------------------------------------------------------- laying the picture on
def nearest_opaque(solid):
    """for every pixel, the nearest pixel that has colour (so the edge of the shape never samples empty picture)"""
    _, idx = ndimage.distance_transform_edt(~solid, return_indices=True)
    return idx


def lay_picture(ob, n, solid, mapping):
    """uv per corner from the shape's own point: mapping(x px, y px, z px) -> picture (u px, v px)"""
    me = ob.data
    uv = me.uv_layers.new(name="pic")
    near = nearest_opaque(solid)
    s = 1.0 / n
    for poly in me.polygons:
        for li in poly.loop_indices:
            p = me.vertices[me.loops[li].vertex_index].co
            x, y, z = p.x / s, (1 - p.z) / s, (p.y - K.C) / s
            u, v = mapping(x, y, z)  # (our textures bleed past the picture's edge, so no empty pixel shows)
            uv.data[li].uv = (u / n, 1 - v / n)


def flat_map(x, y, z):
    return x, y


def wrap_map(cx_rows, r_rows):
    def m(x, y, z):
        k = int(np.clip(round(y * RES - 0.5), 0, len(cx_rows) - 1))
        cx, r = cx_rows[k], max(r_rows[k], 0.3)
        th = math.atan2(x - cx, -z)
        if abs(th) > math.pi / 2:
            th = math.copysign(math.pi - abs(th), th)
        return cx + th / (math.pi / 2) * (r - 0.02), y
    return m


# ---------------------------------------------------------------- textures
def skin_texture(name, col, solid, outline=True, suffix="skin"):
    """our own copy of the picture: for round items without its flat outline (the real shading draws the edges),
    and with every colour bled a few pixels out into the empty space, so a face crossing the picture's edge never
    shows an empty (black) pixel"""
    out = col.copy() if outline else V.no_outline(col, solid)
    near = nearest_opaque(solid)
    bled = out[near[0], near[1]]
    img = (np.clip(bled, 0, 1) * 255).astype(np.uint8)
    img[..., 3] = 255
    p = os.path.join(K.PACK, "assets", K.NS, "textures", "item", "obj")
    os.makedirs(p, exist_ok=True)
    Image.fromarray(img, "RGBA").save(os.path.join(p, f"{name}_{suffix}.png"))
    return f"{K.NS}:item/obj/{name}_{suffix}"


def tex_mat(name, tex, tint=-1):
    m = K.mat(name, edge=0.0, tint=tint)
    m["tex"] = tex
    return m


# ---------------------------------------------------------------- the items
def sword_half(solid, col):
    n = solid.shape[0]
    stick = V.is_stick(col)
    d = V.depth_steps(solid)
    half = np.zeros((n, n))
    for y in range(n):
        for x in range(n):
            if not solid[y, x]:
                continue
            u = x - y
            # a thin blade with a sharp edge and a raised middle; a solid guard, grip and pommel
            half[y, x] = 0.85 if stick[y, x] else ((0.22 if d[y, x] <= 1 else 0.55) if u >= -1 else 1.1)
    return half


def tool_half(solid, col):
    stick = V.is_stick(col)
    d = V.depth_steps(solid)
    return np.where(stick, 0.85, np.where(d <= 1, 0.5, 0.9))


def make(name):
    if name in ("potion", "splash_potion", "lingering_potion"):
        layers = [(V.sprite("potion_overlay"), 0, "minecraft:item/potion_overlay"), (V.sprite(name), -1, f"minecraft:item/{name}")]
    else:
        layers = [(V.sprite(name), -1, f"minecraft:item/{name}")]
    n = layers[0][0].shape[0]
    col = np.zeros((n, n, 4))
    owner = np.full((n, n), -1)
    for li, (arr, _, _) in enumerate(layers):
        m = arr[..., 3] > 0.5
        col[m] = arr[m]
        owner[m] = li
    solid = owner >= 0
    rnd = name in V.ROUND
    if rnd:
        f, cxr, rr = round_field(solid)
        zmax = float(rr.max()) + 0.5
    else:
        half = sword_half(solid, col) if name.endswith("_sword") else tool_half(solid, col) if name.endswith(V.TOOLS) \
            else V.inflate(0.8)(solid, col, None)
        f = flat_field(solid, half)
        zmax = float(half.max()) + 0.5
    if len(layers) > 1:
        top = owner == len(layers) - 1
        base = tex_mat("body", skin_texture(name, col, solid))
    else:
        base = tex_mat("body", skin_texture(name, col, solid, outline=not rnd))
    ob = mesh_from_field(name, f, n, zmax, base, target=2600 if rnd else 1600, three_d=rnd)
    mapping = wrap_map(cxr, rr) if rnd else flat_map
    lay_picture(ob, n, solid, mapping)
    if len(layers) > 1:
        # which picture each face shows: the liquid (coloured by the game) or the bottle
        lq = layers[0][0][..., 3] > 0.5
        liquid = tex_mat("liquid", skin_texture(name, layers[0][0], lq, suffix="liquid"), tint=layers[0][1])
        ob.data.materials.append(liquid)
        uv = ob.data.uv_layers["pic"]
        for poly in ob.data.polygons:
            u, v = np.mean([uv.data[li].uv for li in poly.loop_indices], axis=0)
            iu, iv = int(np.clip(u * n, 0, n - 1)), int(np.clip((1 - v) * n, 0, n - 1))
            if owner[iv, iu] == 0:
                poly.material_index = 1
    big = name.endswith(V.TOOLS)
    return ob, (V.held(True) if big else V.held(False, fp_scale=0.4, fp_lift=5.4) if rnd else V.held(False))


TEST = ["diamond_sword", "iron_pickaxe", "apple", "potion"]


def preview(ob, out):
    """the item as the game shows it: its picture times the baked shadows, under soft light"""
    for m in ob.data.materials:
        nt = m.node_tree
        nt.nodes.clear()
        tex = nt.nodes.new("ShaderNodeTexImage")
        ns, path = m["tex"].split(":")
        if ns == "minecraft":
            import io
            tex.image = bpy.data.images.load(_extract(path))
        else:
            tex.image = bpy.data.images.load(os.path.join(K.PACK, "assets", ns, "textures", path + ".png"))
        tex.interpolation = "Closest"
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "pic"
        nt.links.new(uvn.outputs[0], tex.inputs[0])
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "final"
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(tex.outputs["Color"], mix.inputs[6])
        nt.links.new(vc.outputs["Color"], mix.inputs[7])
        last = mix.outputs[2]
        if m.get("tint", -1) >= 0:
            tint = nt.nodes.new("ShaderNodeMix")
            tint.data_type = "RGBA"
            tint.blend_type = "MULTIPLY"
            tint.inputs["Factor"].default_value = 1.0
            tint.inputs[7].default_value = (0.93, 0.02, 0.05, 1)
            nt.links.new(last, tint.inputs[6])
            last = tint.outputs[2]
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Roughness"].default_value = 1.0
        bsdf.inputs["Specular IOR Level"].default_value = 0.0
        out_n = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(last, bsdf.inputs["Base Color"])
        nt.links.new(bsdf.outputs[0], out_n.inputs[0])
    K.render_preview(ob, out, keep_materials=True)


def _extract(path):
    p = f"/tmp/claude-0/mctex/{path}.png"
    if not os.path.exists(p):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(V._jar.read(f"assets/minecraft/textures/{path}.png"))
    return p


if __name__ == "__main__":
    K.configure(sys.argv)
    K.white_texture()
    pics = []
    for name in (sorted(K.ONLY) if K.ONLY else TEST):
        K.reset()
        ob, display = make(name)
        K.bake_and_export(ob, name, display, False, particle=f"minecraft:item/{name}", soft=0.0)
        print("made", name, len(ob.data.polygons), "faces")
        if K.PREVIEW:
            p = f"/tmp/claude-0/sculpt_{name}.png"
            preview(ob, p)
            pics.append(p)
    if K.PREVIEW and pics:
        ims = [Image.open(p).convert("RGB") for p in pics]
        sheet = Image.new("RGB", (420 * len(ims), 420))
        for i, im in enumerate(ims):
            sheet.paste(im, (420 * i, 0))
        sheet.save(K.PREVIEW)
