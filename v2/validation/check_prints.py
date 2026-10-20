"""Compare V2 project meshes and inspect actual sliced toolpaths.

Run after python v2/build.py --stage slice. Never connects to a printer.
"""
from pathlib import Path
import contextlib
import importlib.util
import json

ROOT = Path(__file__).resolve().parent.parent

def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    result.ROOT = ROOT
    return result

mesh_audit = module('v2_mesh_audit', ROOT.parent/'validation/audit_model.py')
paths_audit = module('v2_paths_audit', ROOT.parent/'validation/inspect_bambu.py')

reports = []
for stem in ('moto_tag_collar_holder_v2', 'moto_tag_collar_holder_grid_cap_v2', 'moto_tag_collar_holder_grid_v2'):
    print('Checking embedded mesh: '+stem, flush=True)
    mesh = mesh_audit.compare_project(stem)
    print('Checking G-code islands: '+stem, flush=True)
    with (ROOT/'validation/bambu'/stem/'audit_stdout.log').open('w',encoding='utf-8') as log, contextlib.redirect_stdout(log):
        paths = paths_audit.audit(stem)
    assert not paths['unanchored_component_candidates'], paths
    assert paths['extrusion_roles'].get('Support',0)>0
    reports.append(dict(model=stem,mesh=mesh,toolpaths=paths))
    print('Passed: '+stem,flush=True)
(ROOT/'validation/print_checks.json').write_text(json.dumps(reports,indent=2)+'\n',encoding='utf-8')
