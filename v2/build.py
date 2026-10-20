"""Rebuild V2 locally. Does not connect to a printer or start a print.

python v2/build.py --stage export
python v2/build.py --stage verify
python v2/build.py --stage slice
python v2/build.py --stage audit
python v2/build.py --stage all
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
VALIDATION = ROOT / 'validation'

def export():
    inputs = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in ROOT.rglob('*.scad')}
    candidates = [Path(r'C:\Program Files\OpenSCAD\openscad.com'),
                  PROJECT / '.tools/openscad-2021.01/openscad.com']
    found = shutil.which('openscad.com') or shutil.which('openscad')
    if found:
        candidates.append(Path(found))
    cad = next((p for p in candidates if p.exists()), None)
    if cad is None:
        raise RuntimeError('OpenSCAD CLI not found')
    VALIDATION.mkdir(exist_ok=True)
    jobs = [
        ('moto_tag_collar_holder_v2.scad', 'moto_tag_collar_holder_v2.stl', []),
        ('validation/tag_reference.scad', 'validation/tag_reference.stl', []),
        ('moto_tag_collar_holder_grid_v2.scad', 'moto_tag_collar_holder_grid_cap_v2.stl', ['-D', 'vid_modeli="nakladka"']),
        ('moto_tag_collar_holder_grid_v2.scad', 'validation/cap_installed.stl', ['-D', 'vid_modeli="nakladka_v_sborke"']),
        ('moto_tag_collar_holder_grid_v2.scad', 'moto_tag_collar_holder_grid_v2.stl', ['-D', 'vid_modeli="stol"']),
        ('fit_test_v2.scad', 'validation/fit_test.csg', []),
    ]
    def run(job):
        source, output, options = job
        target = ROOT / output
        print('Exporting ' + output, flush=True)
        result = subprocess.run([str(cad), *options, '-o', str(target), str(ROOT / source)],
                                cwd=ROOT, capture_output=True, text=True, encoding='utf-8',
                                errors='replace', timeout=900,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        log = result.stdout + result.stderr
        (VALIDATION / (target.stem + '.log')).write_text(log, encoding='utf-8')
        if result.returncode or 'ERROR:' in log or 'WARNING:' in log or not target.exists():
            raise RuntimeError(output + '\n' + log)
        print('Exported ' + output, flush=True)
        return dict(source=source, output=output, returncode=result.returncode)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(run, jobs))
    (VALIDATION / 'export_report.json').write_text(json.dumps(results, indent=2) + '\n', encoding='utf-8')
    assert inputs == {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in ROOT.rglob('*.scad')}, 'SCAD sources changed during export'
    outputs = {result['output']: hashlib.sha256((ROOT/result['output']).read_bytes()).hexdigest()
               for result in results if result['output'].endswith('.stl')}
    (VALIDATION / 'export_hashes.json').write_text(json.dumps(dict(inputs=inputs, outputs=outputs), indent=2) + '\n', encoding='utf-8')

def verify():
    subprocess.run([sys.executable, str(VALIDATION / 'verify_v2.py')], cwd=PROJECT, check=True)

def slice_models():
    # Verify current source/mesh correspondence before producing new printer files.
    verify()
    spec = importlib.util.spec_from_file_location('prepare_bambu_v2', PROJECT / 'prepare_bambu.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    module.OUTPUT = VALIDATION / 'bambu'
    module.PRESETS = ROOT / 'bambu_presets'
    module.prepare()
    # The V2 fit test is the complete supported body; omit V1's unsupported-test profile.
    (module.PRESETS/'process_fit.json').unlink()
    results = [module.slice_model(stem, 'process_holder.json') for stem in (
        'moto_tag_collar_holder_v2', 'moto_tag_collar_holder_grid_cap_v2',
        'moto_tag_collar_holder_grid_v2')]
    (VALIDATION / 'slicing_report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=['export', 'verify', 'slice', 'audit', 'all'], default='all')
    stage = parser.parse_args().stage
    if stage in ('export', 'all'):
        export()
    if stage == 'verify':
        verify()
    if stage in ('slice', 'all'):
        slice_models()
    if stage in ('audit', 'all'):
        subprocess.run([sys.executable, str(VALIDATION/'check_prints.py')], cwd=PROJECT, check=True)
