# SPDX-License-Identifier: GPL-3.0-or-later
# Build DellTemp for Windows: onedir app, Inno Setup EXE, and WiX MSI.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Version = python -c "import sys; sys.path.insert(0, r'src'); from delltemp import __version__; print(__version__)"
Write-Host "Building DellTemp $Version"

python -m pip install -q -r requirements.txt pyinstaller
if ($LASTEXITCODE -ne 0) { throw "pip install failed" }

python -m PyInstaller --noconfirm --clean --distpath dist --workpath build\pyinstaller packaging\delltemp.spec
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

$Inno = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (-not (Test-Path $Inno)) {
    $Inno = "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
}
if (Test-Path $Inno) {
    & $Inno "/DMyAppVersion=$Version" packaging\delltemp.iss
} else {
    Write-Warning "Inno Setup not found; skipping EXE installer. Install from https://jrsoftware.org/isinfo.php"
}

$Heat = "${env:ProgramFiles(x86)}\WiX Toolset v3.14\bin\heat.exe"
if (-not (Test-Path $Heat)) {
    $Heat = "${env:ProgramFiles(x86)}\WiX Toolset v3.11\bin\heat.exe"
}
$Candle = Join-Path (Split-Path $Heat) "candle.exe"
$Light = Join-Path (Split-Path $Heat) "light.exe"
if ((Test-Path $Heat) -and (Test-Path $Candle) -and (Test-Path $Light)) {
    $Harvest = "build\harvested.wxs"
    & $Heat dir "dist\DellTemp" -cg AppFiles -gg -sfrag -srd -sreg -dr INSTALLFOLDER -out $Harvest
    & $Candle -nologo -arch x64 `
        "-dProductVersion=$Version" `
        "-dIconFile=$Root\packaging\delltemp.ico" `
        "packaging\delltemp.wxs" $Harvest -o build\
    & $Light -nologo `
        "build\delltemp.wixobj" "build\harvested.wixobj" `
        -o "dist\DellTemp-$Version.msi"
} else {
    Write-Warning "WiX Toolset not found; skipping MSI. Install the WiX v3 toolset to build it locally."
}

Write-Host "Windows outputs in dist\"
Get-ChildItem dist | Format-Table Name, Length
