"""Audit the published holder; does not simulate TPU deformation or retention force.

Run: python validation/audit_model.py
Dependencies: numpy, trimesh, manifold3d (or the project's .tools/python_libs).
"""
from pathlib import Path
from itertools import product
import ast
import json
import math
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.tools/python_libs'))
import numpy as np
import trimesh
import manifold3d as mf

SOURCE = (ROOT / 'moto_tag_collar_holder.scad').read_text(encoding='utf-8')
CAP = (ROOT / 'moto_tag_collar_holder_grid.scad').read_text(encoding='utf-8')

def number(key, source=SOURCE):
    return float(re.search(r'^' + re.escape(key) + r'\s*=\s*([\d.]+)\s*;', source, re.M)[1])

def solid(mesh):
    result = mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                 np.asarray(mesh.faces, dtype=np.uint64)))
    assert result.status() == mf.Error.NoError
    return result

def nearby_error(points, target, tolerance=0.001):
    """Check every vertex against the other mesh, allowing serialization rounding."""
    cells = {}
    for point in target:
        key = tuple(np.floor(point / tolerance).astype(int))
        cells.setdefault(key, []).append(point)
    offsets = list(product((-1, 0, 1), repeat=3))
    maximum = 0.0
    for point in points:
        key = np.floor(point / tolerance).astype(int)
        candidates = [v for offset in offsets
                      for v in cells.get(tuple(key + offset), [])]
        assert candidates, 'Mesh has an unmatched vertex'
        distance = float(np.linalg.norm(np.asarray(candidates) - point, axis=1).min())
        assert distance < tolerance, distance
        maximum = max(maximum, distance)
    return maximum

def compare_project(stem):
    stl = trimesh.load_mesh(ROOT / (stem + '.stl'), process=True)
    path = ROOT / (stem + '_TPU95A_A1mini.3mf')
    meshes, scales = [], []
    ns = '{http://schemas.microsoft.com/3dmanufacturing/core/2015/02}'
    with zipfile.ZipFile(path) as archive:
        for name in archive.namelist():
            if not name.endswith('.model'):
                continue
            root = ET.fromstring(archive.read(name))
            for element in root.iter():
                if 'transform' in element.attrib:
                    transform = np.array([float(v) for v in element.attrib['transform'].split()])
                    scales.append(np.linalg.svd(transform[:9].reshape(3, 3), compute_uv=False))
            for mesh in root.iter(ns + 'mesh'):
                vertices = [[float(v.attrib[k]) for k in ('x', 'y', 'z')]
                            for v in mesh.find(ns + 'vertices')]
                faces = [[int(v.attrib[k]) for k in ('v1', 'v2', 'v3')]
                         for v in mesh.find(ns + 'triangles')]
                meshes.append(trimesh.Trimesh(vertices=vertices, faces=faces, process=True))
    # These four projects each store one mesh object, including the two-body plates.
    assert len(meshes) == 1
    embedded = meshes[0]
    assert all(np.max(np.abs(s - 1)) < 1e-6 for s in scales), scales
    embedded.apply_translation(stl.bounds.mean(axis=0) - embedded.bounds.mean(axis=0))
    error = max(nearby_error(embedded.vertices, stl.vertices),
                nearby_error(stl.vertices, embedded.vertices))
    volume_error = abs(embedded.volume / stl.volume - 1)
    assert len(embedded.faces) == len(stl.faces)
    assert volume_error < 1e-5
    return dict(stl=stem + '.stl', project=path.name,
                triangles=len(stl.faces), scale_singular_values=[s.tolist() for s in scales],
                max_vertex_distance_after_translation_mm=error,
                relative_volume_difference=volume_error,
                verdict='Meshes agree within 0.001 mm; transforms have no scaling.')

def main():
    parameter_reads = 0
    for script in ('verify_model.py', 'verify_grid.py'):
        tree = ast.parse((ROOT / 'validation' / script).read_text(encoding='utf-8'))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in ('param', 'base', 'cap') and node.args
                    and isinstance(node.args[0], ast.Constant)):
                number(node.args[0].value, CAP if node.func.id == 'cap' else SOURCE)
                parameter_reads += 1

    d, t = number('diametr_metki'), number('tolshchina_metki')
    wall = number('tolshchina_stenki_ushka')
    slot = number('tolshchina_osheynika') + number('zazor_remnya_po_tolshchine')
    outer = d / 2 + number('bokovoy_zazor_metki') + number('tolshchina_stenki_koltsa')
    span = outer - number('otstup_ushka_ot_kraya') + number('dlina_ushka') / 2
    bend = number('radius_izgiba_osheynika')
    sag = bend - math.sqrt(bend ** 2 - span ** 2)
    seat = number('osevaya_dobavka_bortika') + number('osevoy_pripusk_metki') / 2
    base = max(wall + slot + number('zazor_nad_izognutym_remnem') + sag - seat,
               slot + 2 * wall + 0.5 - seat)
    height = t + 2 * seat
    top, tagback = base + height, base + seat

    # Derive installed pose from the published STL instead of trusting a cached view.
    body_mesh = trimesh.load_mesh(ROOT / 'moto_tag_collar_holder.stl', process=True)
    width = number('shirina_osheynika') + number('zazor_remnya_po_shirine') + 2 * wall
    lift = (width / 2 - number('skruglenie_naruzhnyh_krayov') * (2 - math.sqrt(2))) / math.sqrt(2)
    body_mesh.apply_translation([0, 0, -lift])
    body_mesh.apply_transform(trimesh.transformations.rotation_matrix(-math.pi / 4, [1, 0, 0]))
    body = solid(body_mesh)
    tag = trimesh.load_mesh(ROOT / 'validation/tag_reference.stl', process=True)
    assert abs(tag.extents[2] - t) < 0.001
    assert abs(tag.bounds[0, 2] - tagback) < 0.001

    def travel(reference, direction):
        assert abs((body ^ reference).volume()) < 1e-7
        lo, hi = 0., 1.
        assert (body ^ reference.translate([0, 0, direction * hi])).volume() > 1e-7
        for _ in range(24):
            middle = (lo + hi) / 2
            if (body ^ reference.translate([0, 0, direction * middle])).volume() < 1e-7:
                lo = middle
            else:
                hi = middle
        return lo

    reference = solid(tag)
    down, up = travel(reference, -1), travel(reference, 1)
    # Hypothesis only: same rounded profile, total thickness increased to measured 8.2.
    thicker = tag.copy()
    center = tag.bounds[:, 2].mean()
    thicker.vertices[:, 2] += np.where(thicker.vertices[:, 2] < center, -0.1, 0.1)
    thick_solid = solid(thicker)
    measured_face = top - 3.5
    measured_pose = thick_solid.translate([0, 0, measured_face - thicker.bounds[1, 2]])
    report = dict(
        date='2026-10-20',
        source_parameters=dict(design_tag_thickness_mm=t, measured_tag_thickness_mm=8.2,
                               radial_clearance_per_side_mm=number('bokovoy_zazor_metki'),
                               axial_height_allowance_mm=number('osevoy_pripusk_metki')),
        levels_mm=dict(holder_rear=0., ring_rear=base, ring_front=top, ring_height=height,
                       nominal_tag_back=tagback, nominal_tag_front=tagback+t,
                       nominal_front_recess=top-tagback-t,
                       conditional_measured_front=measured_face,
                       conditional_measured_back=measured_face-8.2,
                       conditional_extension_behind_ring=base-(measured_face-8.2)),
        rigid_reference=dict(assumed_edge_radius_mm=number('predpolagaemoe_skruglenie_metki'),
                             down_travel_mm=down, up_travel_mm=up, total_travel_mm=down+up,
                             total_travel_with_assumed_8_2mm_profile_mm=travel(thick_solid,-1)+travel(thick_solid,1),
                             overlap_at_hypothesized_measured_pose_mm3=(body ^ measured_pose).volume()),
        lip=dict(minimum_opening_diameter_mm=2*(d/2+number('bokovoy_zazor_metki')-number('predpolagaemoe_skruglenie_metki')-number('radialnoe_suzhenie_bortika')),
                 overlap_with_assumed_flat_face_mm=number('radialnoe_suzhenie_bortika')-number('bokovoy_zazor_metki'),
                 rear_sector_removed_degrees=number('sektor_okna_dinamika')),
        validation_parameter_reads=parameter_reads,
        print_projects=[compare_project(stem) for stem in (
            'fit_test', 'moto_tag_collar_holder', 'moto_tag_collar_holder_grid_cap', 'moto_tag_collar_holder_grid')],
        limitations=[
            'Measured blue face may differ from the overall thickness measurement datum.',
            'Rigid reference is an assumed rounded disc, not the measured tag surface.',
            'A collision at measured depth means the rigid reference cannot reproduce that pose without changes or deformation.',
            'No simulation of TPU elasticity, printed lip damage, support residue, forces or fatigue.',
            '3MF checks concern embedded meshes and transforms, not a revalidation of G-code.'
        ])
    (ROOT / 'validation/model_audit.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
