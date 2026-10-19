"""Audit saved Bambu G-code and render actual extruded toolpaths.

The raster audit finds complete model islands starting without a previous
model layer or nearby support. It is not a strength/adhesion simulation.
"""
from pathlib import Path
import json
import math
import os
import re
import sys
from collections import deque, Counter
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".tools/python_libs"))
os.environ["MPLCONFIGDIR"] = str(ROOT / ".tools/matplotlib_cache")
import numpy as np
from PIL import Image, ImageDraw
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection


def parse_gcode(path):
    layers, layer = [], None
    x = y = 0.
    role, width = "Custom", 0.42
    relative = True
    extruder = 0.
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("; CHANGE_LAYER"):
            layer = {"z": 0., "paths": []}
            layers.append(layer)
        elif line.startswith("; Z_HEIGHT:"):
            layer["z"] = float(line.split(":")[1])
        elif line.startswith("; FEATURE:"):
            role = line.split(":", 1)[1].strip()
        elif line.startswith("; LINE_WIDTH:"):
            width = float(line.split(":")[1])
        elif line.startswith("M83"):
            relative = True
        elif line.startswith("M82"):
            relative = False
        elif line.startswith("G92 E"):
            extruder = float(re.search(r"E([-\d.]+)", line)[1])
        elif re.match(r"G[0123] ", line):
            command = line.split()[0]
            args = {k: float(v) for k, v in re.findall(r"([XYIJEF])([-\d.]+)", line.split(";")[0])}
            nx, ny = args.get("X", x), args.get("Y", y)
            extrusion = args.get("E", 0.) if relative else args.get("E", extruder)-extruder
            if "E" in args:
                extruder = extruder + args["E"] if relative else args["E"]
            if layer and extrusion > 0.000001 and math.hypot(nx-x, ny-y) > 0.00001:
                points = [(x, y), (nx, ny)]
                if command in ("G2", "G3") and ("I" in args or "J" in args):
                    cx, cy = x+args.get("I", 0), y+args.get("J", 0)
                    radius = math.hypot(x-cx, y-cy)
                    a, b = math.atan2(y-cy, x-cx), math.atan2(ny-cy, nx-cx)
                    delta = ((b-a) % (2*math.pi)) if command == "G3" else -((a-b) % (2*math.pi))
                    count = max(2, int(abs(delta)*radius/0.08)+1)
                    points = [(cx+radius*math.cos(a+delta*i/count), cy+radius*math.sin(a+delta*i/count))
                              for i in range(count+1)]
                    points[0], points[-1] = (x, y), (nx, ny)
                layer["paths"].append((role, width, points))
            x, y = nx, ny
    return layers


def dilate(mask, distance, resolution):
    radius = int(math.ceil(distance/resolution))
    padded = np.pad(mask, radius)
    result = np.zeros_like(mask)
    h, w = mask.shape
    for dy in range(-radius, radius+1):
        for dx in range(-radius, radius+1):
            if dx*dx+dy*dy <= radius*radius:
                result |= padded[radius+dy:radius+dy+h, radius+dx:radius+dx+w]
    return result


def audit(stem):
    directory = ROOT / "validation/bambu" / stem
    layers = parse_gcode(directory / "plate_1.gcode")
    all_points = np.array([p for layer in layers for role, _, path in layer["paths"]
                           if role != "Custom" for p in path])
    minimum, maximum = all_points.min(0)-2, all_points.max(0)+2
    resolution = 0.1
    shape = tuple((np.ceil((maximum-minimum)/resolution).astype(int)+1)[::-1])
    prev_model = np.zeros(shape, dtype=bool)
    support_history = deque()
    unsupported, support_starts = [], []
    by_role = Counter()
    previous_model_z = None
    for number, layer in enumerate(layers, 1):
        images = [Image.new("1", shape[::-1]), Image.new("1", shape[::-1])]
        draws = [ImageDraw.Draw(img) for img in images]
        for role, width, points in layer["paths"]:
            by_role[role] += 1
            if role == "Custom":
                continue
            support = role.startswith("Support") or role == "Brim"
            pixels = [tuple((np.asarray(p)-minimum)/resolution) for p in points]
            draws[int(support)].line(pixels, fill=1, width=max(1, math.ceil(width/resolution)))
        model, support = (np.asarray(img, dtype=bool) for img in images)
        while support_history and layer["z"]-support_history[0][0] > .75:
            support_history.popleft()
        recent_support = np.zeros(shape, dtype=bool)
        for support_z, support_mask in support_history:
            if support_z < layer["z"]-.1:
                recent_support |= support_mask
        anchored = dilate(prev_model, .5, resolution) if previous_model_z is not None and layer["z"]-previous_model_z < .4 else np.zeros(shape, bool)
        supported = dilate(recent_support, .5, resolution)
        remaining = model.copy()
        # Components are footprints of actual extrusion lines, not mesh sections.
        for row, col in zip(*np.nonzero(model)):
            if not remaining[row, col]:
                continue
            component, queue = [], deque([(row, col)])
            remaining[row, col] = False
            while queue:
                ry, rx = queue.popleft()
                component.append((ry, rx))
                for dy, dx in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)):
                    yy, xx = ry+dy, rx+dx
                    if 0 <= yy < shape[0] and 0 <= xx < shape[1] and remaining[yy,xx]:
                        remaining[yy,xx] = False
                        queue.append((yy,xx))
            yy, xx = np.array(component).T
            if len(component) < 8 or layer["z"] <= .21 or anchored[yy,xx].any():
                continue
            item = {"layer": number, "z_mm": layer["z"], "footprint_mm2": round(len(component)*resolution**2, 3)}
            (support_starts if supported[yy,xx].any() else unsupported).append(item)
        if model.any():
            prev_model, previous_model_z = model, layer["z"]
        if support.any():
            support_history.append((layer["z"], support))

    report = {"layer_change_count_including_support_layers": len(layers),
              "extrusion_roles": dict(by_role), "supported_new_model_components": support_starts,
              "unanchored_component_candidates": unsupported,
              "audit_resolution_mm": resolution,
              "audit_limits": "Raster footprints detect whole new islands only; 0.5 mm XY tolerance and 0.75 mm support history. Not a guarantee of local overhang quality, support removal or physical adhesion."}
    (directory / "toolpath_audit.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    fig = plt.figure(figsize=(12, 8), facecolor="#f5f5f2")
    ax = fig.add_subplot(121, projection="3d")
    for is_support, color in ((True, "#2988ba"), (False, "#d07829")):
        segments = []
        for layer in layers:
            for role, width, points in layer["paths"]:
                if role == "Custom" or (role.startswith("Support") or role == "Brim") != is_support:
                    continue
                for a,b in zip(points[:-1],points[1:]):
                    segments.append([(*a,layer["z"]),(*b,layer["z"])])
        ax.add_collection3d(Line3DCollection(segments, colors=color, linewidths=.25, alpha=.75))
    ax.set(xlim=(minimum[0],maximum[0]),ylim=(minimum[1],maximum[1]),zlim=(0,layers[-1]["z"]))
    ax.set_box_aspect((maximum[0]-minimum[0],maximum[1]-minimum[1],layers[-1]["z"]))
    ax.view_init(elev=20, azim=-70)
    ax.set_title("Actual G-code: model orange, supports blue")
    ax.set_xlabel("X mm"); ax.set_ylabel("Y mm"); ax.set_zlabel("Z mm")
    chosen = [min(layers, key=lambda layer:abs(layer["z"]-z)) for z in (.2,2.6,3.2,6.0)]
    grid = fig.add_gridspec(2,4)
    for index, layer in enumerate(chosen):
        axis = fig.add_subplot(grid[index//2,2+index%2])
        for is_support,color in ((True,"#2988ba"),(False,"#d07829")):
            lines = [points for role,_,points in layer["paths"] if role != "Custom" and
                     (role.startswith("Support") or role == "Brim") == is_support]
            axis.add_collection(LineCollection(lines, colors=color, linewidths=.4))
        axis.set_xlim(minimum[0],maximum[0]);axis.set_ylim(minimum[1],maximum[1])
        axis.set_aspect("equal");axis.set_title(f"Z = {layer['z']:.2f} mm")
        axis.tick_params(labelsize=7)
    fig.subplots_adjust(wspace=.6, hspace=.25)
    fig.savefig(directory / "toolpaths.png",dpi=160,bbox_inches="tight")
    plt.close(fig)
    print(stem, json.dumps(report), flush=True)
    return report


if __name__ == "__main__":
    for stem in (sys.argv[1:] or ("fit_test", "moto_tag_collar_holder")):
        audit(stem)
