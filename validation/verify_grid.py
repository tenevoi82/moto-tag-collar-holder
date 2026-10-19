"""Validate grille fit/assembly geometry and render actual exported meshes."""
from pathlib import Path
import sys, os, json, math, re
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'.tools/python_libs'))
os.environ['MPLCONFIGDIR']=str(ROOT/'.tools/matplotlib_cache')
import numpy as np
import trimesh
import manifold3d as mf

BASE=(ROOT/'moto_tag_collar_holder.scad').read_text(encoding='utf-8')
CAP=(ROOT/'moto_tag_collar_holder_grid.scad').read_text(encoding='utf-8')
def number(text,key):
    return float(re.search(r'^'+key+r'\s*=\s*([\d.]+)\s*;',text,re.M)[1])
def base(key):return number(BASE,key)
def cap(key):return number(CAP,key)
def manifold(mesh):
    return mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices,dtype=np.float64),np.asarray(mesh.faces,dtype=np.uint64)))
def check(path,count):
    mesh=trimesh.load_mesh(path,process=True)
    solid=manifold(mesh)
    result=dict(watertight=bool(mesh.is_watertight),winding_consistent=bool(mesh.is_winding_consistent),
                manifold_status=str(solid.status()),bodies=len(solid.decompose()),
                volume_mm3=float(mesh.volume),extents_mm=mesh.extents.tolist(),triangles=len(mesh.faces))
    assert result['watertight'] and result['winding_consistent'] and mesh.volume>0,result
    assert solid.status()==mf.Error.NoError and result['bodies']==count,result
    return mesh,solid,result

printed,pm,printed_info=check(ROOT/'moto_tag_collar_holder_grid_cap.stl',1)
installed,im,installed_info=check(ROOT/'validation/grid/cap_installed.stl',1)
plate,_,plate_info=check(ROOT/'moto_tag_collar_holder_grid.stl',2)
body=trimesh.load_mesh(ROOT/'validation/holder_installed.stl',process=True)
tag=trimesh.load_mesh(ROOT/'validation/tag_reference.stl',process=True)
bm,tm=manifold(body),manifold(tag)
tag_front=float(tag.bounds[1,2])
grid_bottom=float(installed.bounds[1,2])-cap('grid_thickness')
collar=mf.Manifold.cube([100,base('collar_width'),base('collar_thickness')]).translate(
    [-50,-base('collar_width')/2,base('loop_wall')+base('collar_thickness_clearance')/2])
button=mf.Manifold.cylinder(2.0,7.25,7.25,96).translate([0,0,tag_front])
old_report=json.loads((ROOT/'validation/geometry_report.json').read_text(encoding='utf-8'))
air_z=base('loop_wall')+base('collar_thickness')+base('collar_thickness_clearance')+old_report['nominal_dimensions_mm']['analytic_collar_crown_allowance']+.1
air=mf.Manifold.cube([4,24,1]).translate([-2,0,air_z])
collisions=dict(cap_with_body_mm3=float((im^bm).volume()),cap_with_tag_mm3=float((im^tm).volume()),
                cap_with_collar_mm3=float((im^collar).volume()),
                button_2mm_keepout_mm3=float((im^button).volume()),
                rear_air_corridor_mm3=float((im^air).volume()))
assert all(abs(x)<1e-4 for x in collisions.values()),collisions
insertion=[]
for dz in np.arange(0,31,1.0):
    volume=float((im.translate([0,0,float(dz)])^bm).volume())
    assert abs(volume)<1e-4,(dz,volume)
    insertion.append(dict(offset_z_mm=float(dz),overlap_mm3=volume))
holes=[]
pitch=cap('grid_pitch')
inner_r=base('tag_diameter')/2+base('tag_radial_clearance')+base('ring_wall_thickness')+cap('cap_radial_clearance')
for ix in range(-2,3):
    for iy in range(-2,3):
        x,y=ix*pitch,iy*pitch
        if math.hypot(x,y)+.5>=inner_r:continue
        probe=mf.Manifold.cylinder(cap('grid_thickness')+2,.4,.4,32).translate([x,y,grid_bottom-1])
        volume=float((im^probe).volume())
        assert abs(volume)<1e-5,(x,y,volume)
        holes.append([x,y])
bar_probe=mf.Manifold.cylinder(cap('grid_thickness'),.35,.35,32).translate([pitch/2,0,grid_bottom])
assert (im^bar_probe).volume()>.5
gap=cap('grid_pitch')-cap('grid_bar_width')
assert math.sqrt(2)*gap<base('tag_thickness')
report=dict(cap_print_mesh=printed_info,cap_installed_mesh=installed_info,complete_plate_mesh=plate_info,
            collisions=collisions,nominal_face_gap_mm=grid_bottom-tag_front,
            cell_width_mm=gap,cell_max_diagonal_mm=math.sqrt(2)*gap,
            fully_open_cells_probed=len(holes),straight_installation_checks=insertion,
            mechanical_retention='Both base and cap have separate closed loops captured by the same collar; no independent snap latch.',
            limits=['No force/fatigue/pull-off/drop/rain testing of cap. TPU can deform or tear.',
                    '2.5 mm nominal front clearance is geometric; check actual button and deflection on fitting.',
                    '1 mm sampled insertion checks are not a continuous collision simulation.',
                    'Cell aperture comparison assumes undeformed grille and tag geometry.'])
(ROOT/'validation/grid/geometry_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,indent=2),flush=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
def draw(ax,mesh,color,alpha=1):
    light=np.array([-.3,-.5,.8]);light/=np.linalg.norm(light)
    shade=.4+.6*np.maximum(0,mesh.face_normals@light)
    rgba=np.ones((len(mesh.faces),4));rgba[:,:3]=np.array(color)[None,:]*shade[:,None];rgba[:,3]=alpha
    ax.add_collection3d(Poly3DCollection(mesh.triangles,facecolors=rgba,edgecolors='none',rasterized=True))
fig=plt.figure(figsize=(13,9),facecolor='#f5f7fa')
for i,title in enumerate(['Grille cap / front','Assembly with tag','Exploded: collar locks both parts','Print plate: original holder + grille cap']):
    ax=fig.add_subplot(2,2,i+1,projection='3d')
    if i==0:
        draw(ax,installed,[.85,.44,.17]);limits=np.array([[-25,-23,0],[25,23,26]])
    elif i==1:
        draw(ax,body,[.10,.59,.54]);draw(ax,tag,[.20,.37,.73]);draw(ax,installed,[.85,.44,.17]);limits=np.array([[-25,-23,0],[25,23,26]])
    elif i==2:
        exploded=installed.copy();exploded.apply_translation([0,0,14])
        draw(ax,body,[.10,.59,.54]);draw(ax,tag,[.20,.37,.73]);draw(ax,exploded,[.85,.44,.17]);limits=np.array([[-26,-24,0],[26,24,40]])
    else:
        draw(ax,plate,[.10,.59,.54]);limits=plate.bounds+np.array([[-3,-3,-1],[3,3,2]])
    ax.set(xlim=limits[:,0],ylim=limits[:,1],zlim=limits[:,2])
    ax.set_box_aspect(limits[1]-limits[0]);ax.view_init(elev=40 if i==0 else 28,azim=-60)
    ax.set_title(title,fontsize=11);ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm')
fig.tight_layout();fig.savefig(ROOT/'grid_preview.png',dpi=150);plt.close(fig)
