param([switch]$Console)
$ErrorActionPreference = 'Stop'
# 以脚本位置定位，所有构建产物写入仓库外的同级目录。
$repoDir = $PSScriptRoot
$localDir = Join-Path (Split-Path $repoDir -Parent) 'minifps-local'
$pythonExe = Join-Path $localDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    throw '请先按 README 创建 minifps-local/.venv 并安装依赖。'
}
New-Item -ItemType Directory -Force -Path $localDir | Out-Null
$env:PYINSTALLER_CONFIG_DIR = Join-Path $localDir 'pyinstaller-cache'
$mode = if ($Console) { '--console' } else { '--windowed' }
& $pythonExe -m PyInstaller --noconfirm --onefile $mode `
    --name MiniFPS --noupx `
    --collect-all ursina --collect-all panda3d --collect-all direct `
    --collect-all gltf --collect-all simplepbr `
    --copy-metadata ursina `
    --distpath (Join-Path $localDir 'dist') `
    --workpath (Join-Path $localDir 'build') `
    --specpath $localDir `
    (Join-Path $repoDir 'src\minifps.py')
if ($LASTEXITCODE -ne 0) { throw "打包失败，退出码：$LASTEXITCODE" }
Write-Host "完成：$localDir\dist\MiniFPS.exe"


