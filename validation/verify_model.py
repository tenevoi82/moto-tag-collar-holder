"""Reproducible geometric checks, not a physical certification or a slicer.
Run with Python and numpy, trimesh, manifold3d, matplotlib installed.
The optional local dependencies folder is populated in this project.
"""
from pathlib import Path
import sys, json, re, math, os

ROOT = Path(__file__).resolve().parent.parent
os.environ['MPLCONFIGDIR'] = str(ROOT / '.tools/matplotlib_cache')
sys.path.insert(0, str(ROOT / '.tools/python_libs'))
import numpy as np
import trimesh
import manifold3d as mf

source = (ROOT / 'moto_tag_collar_holder.scad').read_text(encoding='utf-8')
def param(name):
    return float(re.search(r'^' + name + r'\s*=\s*([\d.]+)\s*;', source, re.M)[1])

d, t = param('diametr_metki'), param('tolshchina_metki')
sw = param('shirina_osheynika') + param('zazor_remnya_po_shirine')
st = param('tolshchina_osheynika') + param('zazor_remnya_po_tolshchine')
wall, er = param('tolshchina_stenki_ushka'), param('skruglenie_naruzhnyh_krayov')
loop_x = d/2 + param('bokovoy_zazor_metki') + param('tolshchina_stenki_koltsa') - param('otstup_ushka_ot_kraya')
span = loop_x + param('dlina_ushka')/2
bend = param('radius_izgiba_osheynika')
sag = bend-math.sqrt(bend*bend-span*span)
seat = param('osevaya_dobavka_bortika') + param('osevoy_pripusk_metki')/2
base = max(wall+st+param('zazor_nad_izognutym_remnem')+sag-seat, st+2*wall+0.5-seat)
tagback = base + param('osevaya_dobavka_bortika') + param('osevoy_pripusk_metki')/2
lift = ((sw+2*wall)/2-er*(2-math.sqrt(2)))/math.sqrt(2)
bore = d/2 + param('bokovoy_zazor_metki')
throat = bore - param('predpolagaemoe_skruglenie_metki') - param('radialnoe_suzhenie_bortika')

def as_manifold(mesh):
    return mf.Manifold(mf.Mesh64(np.asarray(mesh.vertices, dtype=np.float64),
                                 np.asarray(mesh.faces, dtype=np.uint64)))

def basics(path, components):
    mesh = trimesh.load_mesh(path, process=True)
    model = as_manifold(mesh)
    result = {
        'triangles': len(mesh.faces), 'vertices': len(mesh.vertices),
        'watertight': bool(mesh.is_watertight),
        'winding_consistent': bool(mesh.is_winding_consistent),
        'positive_volume': bool(mesh.volume > 0),
        'connected_bodies': len(model.decompose()),
        'manifold_status': str(model.status()),
        'volume_mm3': float(mesh.volume),
        'bounds_mm': mesh.bounds.tolist(), 'extents_mm': mesh.extents.tolist(),
    }
    assert result['watertight'] and result['winding_consistent'], result
    assert result['positive_volume'] and result['connected_bodies'] == components, result
    assert model.status() == mf.Error.NoError, result
    return mesh, model, result

printed, pm, main_result = basics(ROOT / 'moto_tag_collar_holder.stl', 1)
coupon, cm, coupon_result = basics(ROOT / 'fit_test.stl', 2)

installed = printed.copy()
installed.apply_translation([0, 0, -lift])
installed.apply_transform(trimesh.transformations.rotation_matrix(-math.pi/4,[1,0,0]))
im = as_manifold(installed)
installed.export(ROOT / 'validation/holder_installed.stl')
tag = trimesh.load_mesh(ROOT / 'validation/tag_reference.stl', process=True)
tm = as_manifold(tag)

collar = mf.Manifold.cube([70,param('shirina_osheynika'),param('tolshchina_osheynika')])
collar = collar.translate([-35,-param('shirina_osheynika')/2,
                          wall+param('zazor_remnya_po_tolshchine')/2])
button = mf.Manifold.cylinder(4,14.5,14.5,96).translate([0,0,tagback+t])
# Air exits through the +Y sector; x width=4, z gap excludes both surfaces.
air = mf.Manifold.cube([4,24,1.0]).translate([-2,0,wall+st+sag+0.1])
clashes = {
    'assumed_tag_overlap_mm3': (im ^ tm).volume(),
    'straight_collar_overlap_mm3': (im ^ collar).volume(),
    'front_central_d29_keepout_overlap_mm3': (im ^ button).volume(),
    'rear_lateral_air_corridor_overlap_mm3': (im ^ air).volume(),
}
assert all(abs(v)<1e-5 for v in clashes.values()), clashes

layer_z = np.arange(0.1, printed.bounds[1,2], 0.2)
layer_areas = [pm.slice(float(z)).area() for z in layer_z]
assert all(a>0 for a in layer_areas)
sampled_vol = sum(layer_areas)*0.2

report = {
    'main_STL': main_result, 'fit_test_STL': coupon_result,
    'installed_extents_mm': installed.extents.tolist(),
    'installed_bounds_mm': installed.bounds.tolist(),
    'nominal_dimensions_mm': {
        'bore_diameter':2*bore,'minimum_lip_opening':2*throat,
        'collar_slot':[sw,st],
        'slot_between_rib_peaks':st-2*param('vysota_reber_prizhima'),
        'minimum_tag_back_to_collar_top':tagback-(wall+st),
        'design_collar_bend_radius':bend,
        'analytic_collar_crown_allowance':sag,
        'analytic_air_gap_after_bend':tagback-(wall+st+sag),
        'height_above_slot_top':base+t+param('osevoy_pripusk_metki')+
                                2*param('osevaya_dobavka_bortika')-(wall+st),
    },
    'clearance_checks':clashes,
    'geometric_layer_sections': {
        'interval_mm':0.2,'count':len(layer_z),'empty_internal_layers':0,
        'integrated_volume_relative_error':abs(sampled_vol/pm.volume()-1),
    },
    'limitations':[
        'Tag edge radius 0.8 mm is an assumed rounded-disc reference, not a scan.',
        'Curved-collar clearance is an analytic crown allowance; local leather bending and TPU loop deflection require physical fitting.',
        'Physical fit-test feedback is recorded separately in FIT_TEST_RESULT.md; this script does not test forces, fatigue, acoustics, wet leather or animal use.',
        'This script checks geometry only. Bambu G-code and support audit results are separate in validation/bambu and BAMBU_CHECK.md.',
        'CGAL Simple=yes and topology/Boolean checks passed; no separate exhaustive triangle intersection test.',
    ]
}
(ROOT/'validation/geometry_report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))

# Mesh-derived technical views. No image generation: these are actual STL faces.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def add_mesh(ax, mesh, color, alpha=1):
    light = np.array([-0.3,-0.5,0.8]); light/=np.linalg.norm(light)
    intensity = 0.45+0.55*np.maximum(0,mesh.face_normals@light)
    rgba = np.ones((len(mesh.faces),4))
    rgba[:,:3]=np.asarray(color)[None,:]*intensity[:,None]
    rgba[:,3]=alpha
    ax.add_collection3d(Poly3DCollection(mesh.triangles,facecolors=rgba,
                                       edgecolors='none',rasterized=True))

fig = plt.figure(figsize=(15,9), facecolor='#f5f7fa')
for i,(az,el,title) in enumerate([
    (-60,30,'Main holder / front'),(120,150,'Rear / speaker relief'),
    (-60,6,'Assembly: straight collar + assumed tag'),
    (-55,25,'STL print orientation: 45 degrees')]):
    ax=fig.add_subplot(2,2,i+1,projection='3d')
    mesh=printed if i==3 else installed
    add_mesh(ax,mesh,[0.12,0.62,0.58])
    if i==2:
        add_mesh(ax,tag,[0.55,0.68,0.94],0.45)
        strap=trimesh.creation.box([60,param('shirina_osheynika'),param('tolshchina_osheynika')])
        strap.apply_translation([0,0,wall+param('zazor_remnya_po_tolshchine')/2+
                                 param('tolshchina_osheynika')/2])
        add_mesh(ax,strap,[0.58,0.34,0.16],0.35)
    bounds=mesh.bounds; center=bounds.mean(axis=0); extent=mesh.extents
    if i==2: extent=np.maximum(extent,[62,38,20])
    for setlim,c,e in zip([ax.set_xlim,ax.set_ylim,ax.set_zlim],center,extent):
        setlim(c-e*0.56,c+e*0.56)
    ax.set_box_aspect(extent.copy())
    ax.view_init(elev=el,azim=az)
    ax.set_title(title,fontsize=12,pad=4)
    ax.set_xlabel('X mm');ax.set_ylabel('Y mm');ax.set_zlabel('Z mm')
    ax.grid(False)
fig.suptitle('Moto Tag / TPU 95A / actual exported geometry',fontsize=18)
fig.tight_layout()
fig.savefig(ROOT/'preview.png',dpi=160)

# Accurate center section through the front/rear lips and a loop station.
fig,axes=plt.subplots(1,2,figsize=(13,5),facecolor='#f5f7fa')
for ax,x,title in zip(axes,[0,loop_x],['Ring section: X = 0',f'Loop section: X = {loop_x:g}']):
    # Map installed X to slicing Z, retain installed Y and Z as plot X/Y.
    rotated=installed.copy()
    rotated.vertices=installed.vertices[:,[1,2,0]]
    contours=as_manifold(rotated).slice(x).to_polygons()
    for contour in contours:
        c=np.asarray(contour); c=np.vstack([c,c[0]])
        ax.plot(c[:,0],c[:,1],color='#087f77',linewidth=1.5)
    ax.plot([-param('shirina_osheynika')/2,param('shirina_osheynika')/2],
            [wall+st,wall+st],'--',color='#a36b35',label='Maximum collar top')
    ax.set_aspect('equal');ax.set_title(title);ax.set_xlabel('Y mm');ax.set_ylabel('Z mm')
    ax.grid(alpha=.2);ax.legend(fontsize=8)
fig.tight_layout();fig.savefig(ROOT/'validation/sections.png',dpi=160)
