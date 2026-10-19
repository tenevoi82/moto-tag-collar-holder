$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$cadExe = Join-Path $PSScriptRoot '.tools\openscad-2021.01\openscad.com'
if (-not (Test-Path -LiteralPath $cadExe)) {
    $cadCommand = Get-Command openscad.com,openscad -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $cadCommand) { throw 'OpenSCAD CLI not found.' }
    $cadExe = $cadCommand.Source
}
New-Item -ItemType Directory -Path 'validation' -Force | Out-Null
function Export-Model([string]$SourceFile,[string]$OutputFile,[string]$LogFile) {
    & $cadExe -o $OutputFile $SourceFile 2>&1 | Tee-Object -FilePath $LogFile
    if ($LASTEXITCODE -ne 0) { throw "OpenSCAD failed: $SourceFile" }
}
Export-Model 'moto_tag_collar_holder.scad' 'moto_tag_collar_holder.stl' 'validation\openscad_main.log'
Export-Model 'fit_test.scad' 'fit_test.stl' 'validation\openscad_fit.log'
Export-Model 'validation\tag_reference.scad' 'validation\tag_reference.stl' 'validation\openscad_reference.log'
python 'validation\verify_model.py'
if ($LASTEXITCODE -ne 0) { throw 'Geometric verification failed; inspect console output.' }
