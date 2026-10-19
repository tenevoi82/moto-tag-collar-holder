"""Prepare reproducible, fully resolved A1 mini / TPU 95A Bambu projects.

Uses the installed Bambu Studio profiles, including their G-code templates.
Does not connect to a printer or start a print.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
STUDIO = Path(r"C:\Program Files\Bambu Studio")
PROFILES = STUDIO / "resources/profiles/BBL"
OUTPUT = ROOT / "validation/bambu"
PRESETS = ROOT / "bambu_presets"


def resolve(category: str, name: str, chain=()) -> dict:
    if name in chain:
        raise ValueError(f"Circular profile inheritance: {chain} -> {name}")
    path = PROFILES / category / (name + ".json")
    local = json.loads(path.read_text(encoding="utf-8-sig"))
    result = {}
    parent = local.get("inherits")
    if parent:
        result.update(resolve(category, parent, chain + (name,)))
    for template in local.get("include", []):
        result.update(resolve(category, template, chain + (name,)))
    result.update(local)
    for field in ("inherits", "include"):
        result.pop(field, None)
    return result


def update(profile: dict, **values) -> None:
    for key, value in values.items():
        if isinstance(profile.get(key), list) and not isinstance(value, list):
            value = [str(value)]
        profile[key] = value


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def validate_project(path: Path, support_enabled: bool) -> dict:
    with ZipFile(path) as archive:
        assert archive.testzip() is None, "Damaged 3MF archive"
        config = json.loads(archive.read("Metadata/project_settings.config"))
        gcode = archive.read("Metadata/plate_1.gcode")
        recorded_md5 = archive.read("Metadata/plate_1.gcode.md5").decode().strip()
        assert hashlib.md5(gcode).hexdigest().lower() == recorded_md5.lower(), "G-code checksum mismatch"
        expected = {"printer_model": "Bambu Lab A1 mini", "wall_loops": "5",
                    "layer_height": "0.2", "sparse_infill_density": "40%",
                    "enable_support": "1" if support_enabled else "0",
                    "filament_type": ["TPU"], "nozzle_temperature": ["230"],
                    "filament_max_volumetric_speed": ["2"]}
        for key, value in expected.items():
            assert config[key] == value, (key, config[key], value)
        return {"archive_crc_valid": True, "gcode_md5_valid": True,
                "verified_embedded_settings": expected,
                "gcode_bytes": len(gcode), "project_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def prepare():
    machine = resolve("machine", "Bambu Lab A1 mini 0.4 nozzle")
    assert len(machine["machine_start_gcode"]) > 1000
    assert len(machine["machine_end_gcode"]) > 100
    process = resolve("process", "0.20mm Standard @BBL A1M")
    update(process, name="0.20mm TPU95A Moto Tag @BBL A1M", **{
        "from": "user", "setting_id": "", "instantiation": "true",
        "print_settings_id": "0.20mm TPU95A Moto Tag @BBL A1M",
        "layer_height": "0.2", "initial_layer_print_height": "0.2",
        "wall_loops": "5", "top_shell_layers": "5", "bottom_shell_layers": "5",
        "sparse_infill_density": "40%", "sparse_infill_pattern": "gyroid",
        "default_acceleration": "500", "outer_wall_acceleration": "500",
        "inner_wall_acceleration": "500", "initial_layer_acceleration": "500",
        "top_surface_acceleration": "500", "travel_acceleration": "1000",
        "initial_layer_speed": "15", "initial_layer_infill_speed": "15",
        "outer_wall_speed": "20", "inner_wall_speed": "25",
        "sparse_infill_speed": "25", "internal_solid_infill_speed": "25",
        "top_surface_speed": "20", "gap_infill_speed": "20",
        "bridge_speed": "15", "support_speed": "25", "support_interface_speed": "20",
        "travel_speed": "150", "brim_type": "outer_only", "brim_width": "8",
        "brim_object_gap": "0.1", "enable_prime_tower": "0",
        "enable_support": "1", "support_type": "tree(auto)",
        "support_style": "tree_slim", "support_on_build_plate_only": "1",
        "support_threshold_angle": "35", "support_top_z_distance": "0.3",
        "support_bottom_z_distance": "0.3", "support_object_xy_distance": "0.4",
        "support_interface_top_layers": "2", "support_interface_spacing": "0.5",
        "reduce_infill_retraction": "1",
    })
    filament = resolve("filament", "Generic TPU @BBL A1M")
    update(filament, name="TPU 95A Moto Tag @BBL A1M", **{
        "from": "user", "setting_id": "", "instantiation": "true",
        "filament_settings_id": ["TPU 95A Moto Tag @BBL A1M"],
        "filament_max_volumetric_speed": "2", "nozzle_temperature": "230",
        "nozzle_temperature_initial_layer": "230",
        "textured_plate_temp": "35", "textured_plate_temp_initial_layer": "35",
        "hot_plate_temp": "35", "hot_plate_temp_initial_layer": "35",
        "fan_min_speed": "40", "fan_max_speed": "60", "close_fan_the_first_x_layers": "3",
        "filament_retraction_length": "0.4",
        "compatible_printers": ["Bambu Lab A1 mini 0.4 nozzle"],
    })
    fit_process = dict(process)
    update(fit_process, name="0.20mm TPU95A Fit Test @BBL A1M",
           print_settings_id="0.20mm TPU95A Fit Test @BBL A1M", enable_support="0")
    for filename, value in (("machine.json", machine), ("process_holder.json", process),
                            ("process_fit.json", fit_process), ("filament_tpu95a.json", filament)):
        write_json(PRESETS / filename, value)


def slice_model(stem: str, process_name: str) -> dict:
    output_dir = OUTPUT / stem
    output_dir.mkdir(parents=True, exist_ok=True)
    project = ROOT / (stem + "_TPU95A_A1mini.3mf")
    args = [str(STUDIO / "bambu-studio.exe"), "--debug", "3", "--arrange", "1",
            "--curr-bed-type", "Textured PEI Plate", "--load-settings",
            f"{PRESETS / 'machine.json'};{PRESETS / process_name}", "--load-filaments",
            str(PRESETS / "filament_tpu95a.json"), "--slice", "0", "--outputdir", str(output_dir),
            "--export-3mf", project.name, str(ROOT / (stem + ".stl"))]
    print(f"Slicing {stem}...", flush=True)
    with (output_dir / "stdout.log").open("w", encoding="utf-8") as out, \
         (output_dir / "stderr.log").open("w", encoding="utf-8") as err:
        run = subprocess.run(args, cwd=output_dir, stdout=out, stderr=err,
                             creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), timeout=600)
    exported_project = output_dir / project.name
    if run.returncode == 0 and exported_project.exists():
        shutil.copy2(exported_project, project)
    report = {"model": stem, "process_exit_code": run.returncode,
              "project": str(project), "project_exists": project.exists()}
    result_file = output_dir / "result.json"
    if result_file.exists():
        report["slicer_result"] = json.loads(result_file.read_text(encoding="utf-8-sig"))
    if run.returncode or not project.exists() or report.get("slicer_result", {}).get("return_code") != 0:
        write_json(output_dir / "run_report.json", report)
        raise RuntimeError(f"Slicing failed: {report}")
    report["archive_validation"] = validate_project(project, stem != "fit_test")
    write_json(output_dir / "run_report.json", report)
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return report


if __name__ == "__main__":
    prepare()
    targets = sys.argv[1:] or ["fit_test", "moto_tag_collar_holder"]
    for target in targets:
        if target not in ("fit_test", "moto_tag_collar_holder", "moto_tag_collar_holder_grid", "moto_tag_collar_holder_grid_cap"):
            raise ValueError(target)
        slice_model(target, "process_fit.json" if target == "fit_test" else "process_holder.json")
