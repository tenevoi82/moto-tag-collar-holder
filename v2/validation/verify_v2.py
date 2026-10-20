"""Geometric checks of V2's actual STL meshes, including positive rear support.

This is not an elasticity, strength, print quality, acoustic or water ingress test.
"""
from pathlib import Path
import hashlib
import json
import math
import os
import re
import sys

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT.parent
os.environ['MPLCONFIGDIR'] = str(PROJECT / '.tools/matplotlib_cache')
sys.path.insert(0, str(PROJECT / '.tools/python_libs'))
import numpy as np
import trimesh
import manifold3d as mf

SOURCE = (ROOT / 'moto_tag_collar_holder_v2.scad').read_text(encoding='utf-8')
CAP = (ROOT / 'moto_tag_collar_holder_grid_v2.scad').read_text(encoding='utf-8')

def p(key, source=SOURCE):
    return float(re.search(r'^' + re.escape(key) + r'\s*=\s*([\d.]+)\s*;', source, re.M)[1])

def solid(mesh):
    result = mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                 np.asarray(mesh.faces, dtype=np.uint64)))
    assert result.status() == mf.Error.NoError
    return result

def checked_mesh(name, components):
    mesh = trimesh.load_mesh(ROOT/name, process=True)
    part = solid(mesh)
    result = dict(triangles=len(mesh.faces), watertight=bool(mesh.is_watertight),
                  winding_consistent=bool(mesh.is_winding_consistent),
                  components=len(part.decompose()), volume_mm3=float(mesh.volume),
                  extents_mm=mesh.extents.tolist())
    assert result['watertight'] and result['winding_consistent'] and mesh.volume > 0, result
    assert result['components'] == components, result
    return mesh, part, result

def main():
    hashes = json.loads((ROOT/'validation/export_hashes.json').read_text(encoding='utf-8'))
    for group in hashes.values():
        for name, expected in group.items():
            assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, 'Re-export changed input/output: '+name
    mesh, _, body_info = checked_mesh('moto_tag_collar_holder_v2.stl', 1)
    cap_print, _, cap_print_info = checked_mesh('moto_tag_collar_holder_grid_cap_v2.stl', 1)
    cap, cm, cap_info = checked_mesh('validation/cap_installed.stl', 1)
    plate, _, plate_info = checked_mesh('moto_tag_collar_holder_grid_v2.stl', 2)
    tag, tm, tag_info = checked_mesh('validation/tag_reference.stl', 1)
    wall, slot = p('tolshchina_stenki_ushka'), p('tolshchina_osheynika')+p('zazor_remnya_po_tolshchine')
    outer = p('diametr_metki')/2+p('bokovoy_zazor_metki')+p('tolshchina_stenki_koltsa')
    loop_x = outer-p('otstup_ushka_ot_kraya')
    span = loop_x+p('dlina_ushka')/2
    sag = p('radius_izgiba_osheynika')-math.sqrt(p('radius_izgiba_osheynika')**2-span**2)
    base = max(wall+slot+p('zazor_nad_izognutym_remnem')+sag,slot+2*wall+.5)
    seat = base+p('tolshchina_zadney_opory')
    top = seat+p('tolshchina_metki')+p('utoplenie_metki_speredi')
    width = p('shirina_osheynika')+p('zazor_remnya_po_shirine')+2*wall
    lift = (width/2-p('skruglenie_naruzhnyh_krayov')*(2-math.sqrt(2)))/math.sqrt(2)
    body = mesh.copy()
    body.apply_translation([0,0,-lift])
    body.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/4,[1,0,0]))
    bm = solid(body)
    body.export(ROOT/'validation/holder_installed.stl')
    assert abs(tag.extents[2]-8.2)<.001
    assert abs(tag.bounds[0,2]-seat)<.001
    assert abs(body.bounds[1,2]-top)<.001
    assert abs(mesh.bounds[0,2])<.001
    assert abs(cap_print.bounds[0,2])<.001

    # Nominal contact is intentional; allow tiny STL rounding overlap at the seat.
    nominal_overlap = (bm ^ tm).volume()
    assert nominal_overlap < .05, nominal_overlap
    assert (bm ^ tm.translate([0,0,.002])).volume() < 1e-5
    rear_stop = {str(d): float((bm ^ tm.translate([0,0,-d])).volume()) for d in (.1,.2,.5,2.4)}
    assert rear_stop['0.1'] > 20 and rear_stop['0.2'] > 40, rear_stop

    # Check an entire 360-degree annulus inside the floor, including under the channel.
    floor_probe = (mf.Manifold.cylinder(1,16,16,192)-mf.Manifold.cylinder(1,11.35,11.35,192)).translate([0,0,base+.2])
    floor_coverage = (bm ^ floor_probe).volume()/floor_probe.volume()
    assert floor_coverage > .99999, floor_coverage
    hole_probe = mf.Manifold.cylinder(2.1,10.8,10.8,96).translate([0,0,base-.05])
    assert abs((bm ^ hole_probe).volume()) < 1e-6
    air_probe = mf.Manifold.cube([2,13,.45]).translate([-1,9,seat-.55])
    assert abs((bm ^ air_probe).volume()) < 1e-6
    assert base-(wall+slot+sag) >= 1.19999

    flat_radius = p('diametr_metki')/2-p('predpolagaemoe_skruglenie_metki')
    bearing_probe = mf.Manifold.cylinder(.02,flat_radius,flat_radius,192).translate([0,0,seat-.025])
    bearing_area = (bm ^ bearing_probe).volume()/.02
    assert bearing_area > 250, bearing_area
    collar = mf.Manifold.cube([100,p('shirina_osheynika'),p('tolshchina_osheynika')]).translate(
        [-50,-p('shirina_osheynika')/2,wall+p('zazor_remnya_po_tolshchine')/2])
    button = mf.Manifold.cylinder(2,7.25,7.25,96).translate([0,0,seat+p('tolshchina_metki')])
    collisions = dict(body_collar=(bm^collar).volume(), cap_body=(cm^bm).volume(),
                      cap_tag=(cm^tm).volume(), cap_collar=(cm^collar).volume(),
                      cap_button_envelope=(cm^button).volume())
    assert all(abs(v)<1e-5 for v in collisions.values()), collisions
    insertion = []
    for dz in np.arange(0,34.01,.5):
        volume = float((cm.translate([0,0,float(dz)])^bm).volume())
        assert abs(volume)<1e-5, (dz,volume)
        insertion.append(volume)
    grid_bottom = cap.bounds[1,2]-p('tolshchina_setki',CAP)
    gap = grid_bottom-tag.bounds[1,2]
    assert abs(gap-2.5)<.001
    cell = p('shag_setki',CAP)-p('shirina_peremychki_setki',CAP)
    assert cell*math.sqrt(2) < p('tolshchina_metki')

    # Check actual plate contains the transformed meshes, not an old body or cap.
    shifted_body = mesh.copy(); shifted_body.apply_translation([-p('polurasstoyanie_mezhdu_detalyami',CAP),0,0])
    shifted_cap = cap_print.copy(); shifted_cap.apply_translation([p('polurasstoyanie_mezhdu_detalyami',CAP),0,0])
    intended_plate = solid(shifted_body)+solid(shifted_cap)
    actual_plate = solid(plate)
    mismatch = (intended_plate-actual_plate).volume()+(actual_plate-intended_plate).volume()
    assert abs(mismatch)<.05, mismatch

    report = dict(version=2, source_and_mesh_hashes_verified=True,
                  body=body_info, cap=cap_info, cap_print=cap_print_info, plate=plate_info,
                  reference=tag_info,
                  dimensions_mm=dict(tag_thickness=p('tolshchina_metki'), ring_rear=base,
                                     ring_height=top-base, body_height=top, tag_back=seat,
                                     tag_front=seat+p('tolshchina_metki'), front_recess=top-seat-p('tolshchina_metki'),
                                     rear_support_thickness=p('tolshchina_zadney_opory'), rear_hole_diameter=p('diametr_zadnego_otverstiya'),
                                     residual_floor_under_channel=p('tolshchina_zadney_opory')-p('glubina_zvukovogo_kanala'),
                                     underside_to_curved_collar=base-(wall+slot+sag), cap_face_gap=gap),
                  rear_support=dict(nominal_rounding_overlap_mm3=nominal_overlap,
                                    estimated_bearing_area_for_assumed_flat_face_mm2=bearing_area,
                                    continuous_floor_probe_coverage=floor_coverage,
                                    downward_reference_overlap_mm3=rear_stop),
                  assembly_collisions_mm3=collisions, cap_insertion_samples=len(insertion),
                  plate_symmetric_difference_mm3=mismatch,
                  limitations=['Reference rounding is assumed; actual tag profile is not measured.',
                               'Rigid contact tests establish a geometric stop, not resistance to TPU deformation.',
                               'No physical test of V2, force, fatigue, sound, button operation or rain resistance.'])
    (ROOT/'validation/geometry_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2),flush=True)
    render(body, bm, tag, tm, cap)

def render(body,bm,tag,tm,cap):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.path import Path as MPath
    from matplotlib.patches import PathPatch
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    def section(ax,part,color):
        # X=0 section: horizontal axis Y, vertical axis Z, crossing the sound channel.
        paths=[]
        for contour in part.rotate([0,90,0]).slice(0).to_polygons():
            points=np.asarray(contour)[:,[1,0]]
            points=np.vstack([points,points[0]])
            codes=np.full(len(points),MPath.LINETO);codes[0]=MPath.MOVETO;codes[-1]=MPath.CLOSEPOLY
            paths.append(MPath(points,codes))
        ax.add_patch(PathPatch(MPath.make_compound_path(*paths),facecolor=color,edgecolor='#24324a',lw=.6))
    oldbody=trimesh.load_mesh(PROJECT/'validation/holder_installed.stl',process=True)
    oldtag=trimesh.load_mesh(PROJECT/'validation/tag_reference.stl',process=True)
    fig,axes=plt.subplots(1,2,figsize=(12,6),facecolor='#f5f7fa')
    for ax,bb,tt,title in zip(axes,[solid(oldbody),bm],[solid(oldtag),tm],
                            ['V1: упругие кромки, задний вырез','V2: широкая задняя опора']):
        section(ax,bb,'#596578');section(ax,tt,'#6292da')
        ax.set(xlim=(-21,21),ylim=(-1,24),xlabel='Y, мм',ylabel='Z, мм',title=title)
        ax.set_aspect('equal');ax.grid(alpha=.15);ax.set_axisbelow(True)
    axes[1].annotate('Опора 2,0 мм',xy=(-13,11.2),xytext=(-19,21.8),arrowprops=dict(arrowstyle='->'),fontsize=10)
    axes[1].annotate('Под каналом\nостаётся 1,4 мм',xy=(15,11),xytext=(1,4),arrowprops=dict(arrowstyle='->'),fontsize=10)
    fig.suptitle('Разрез фактических STL через звуковой канал',fontsize=16)
    fig.text(.5,.035,'Синий — условный профиль метки. Разрез не моделирует деформацию TPU.',ha='center',fontsize=10)
    fig.tight_layout(rect=(0,.07,1,.93));fig.savefig(ROOT/'comparison.png',dpi=160);plt.close(fig)

    def draw(ax,mesh,color):
        light=np.array([-.3,-.5,.8]);light/=np.linalg.norm(light)
        shade=.4+.6*np.maximum(0,mesh.face_normals@light)
        colors=np.ones((len(mesh.faces),4));colors[:,:3]=np.array(color)[None,:]*shade[:,None]
        ax.add_collection3d(Poly3DCollection(mesh.triangles,facecolors=colors,edgecolors='none',rasterized=True))
    fig=plt.figure(figsize=(15,5),facecolor='#f5f7fa')
    for i,title in enumerate(['Корпус V2: передняя сторона','Корпус V2: задняя опора','Сборка V2 с решёткой']):
        ax=fig.add_subplot(1,3,i+1,projection='3d');draw(ax,body,[.1,.59,.54])
        if i==2:
            draw(ax,tag,[.2,.37,.73]);draw(ax,cap,[.85,.44,.17])
        ax.set(xlim=(-24,24),ylim=(-24,24),zlim=(-1,27),title=title)
        ax.set_box_aspect([48,48,28]);ax.view_init(elev=-55 if i==1 else 40,azim=-60)
        ax.set_axis_off()
    fig.tight_layout(rect=(0,0,1,.90));fig.savefig(ROOT/'preview.png',dpi=160,bbox_inches='tight');plt.close(fig)

if __name__=='__main__':
    main()
