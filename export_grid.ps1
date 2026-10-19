$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$cadExe = Join-Path $PSScriptRoot '.tools\openscad-2021.01\openscad.com'
if (-not (Test-Path -LiteralPath $cadExe)) {
    $cadCommand = Get-Command openscad.com,openscad -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cadCommand) { throw 'OpenSCAD CLI not found.' }
    $cadExe = $cadCommand.Source
}
New-Item -ItemType Directory -Path 'validation\grid' -Force | Out-Null
function Export-Grid([string]$Part,[string]$OutputFile,[string]$LogFile) {
    & $cadExe -D ('output_part="' + $Part + '"') -o $OutputFile 'moto_tag_collar_holder_grid.scad' 2>&1 | Tee-Object -FilePath $LogFile
    if ($LASTEXITCODE -ne 0) { throw "OpenSCAD failed: $Part" }
}
Export-Grid 'cap' 'moto_tag_collar_holder_grid_cap.stl' 'validation\grid\openscad_cap.log'
Export-Grid 'cap_installed' 'validation\grid\cap_installed.stl' 'validation\grid\openscad_cap_installed.log'
Export-Grid 'plate' 'moto_tag_collar_holder_grid.stl' 'validation\grid\openscad_plate.log'
