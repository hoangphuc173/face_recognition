$ErrorActionPreference = "Stop"
$Root = Get-Location
$BackendDir = Join-Path $Root "backend"
$LayerDir = Join-Path $BackendDir "layer_v2"
$PythonDir = Join-Path $LayerDir "python"

Write-Host "Building Lambda Layer..."
if (Test-Path $LayerDir) {
    # Use cmd /c rmdir for more robust deletion on Windows
    cmd /c "rmdir /s /q ""$LayerDir"""
}
New-Item -ItemType Directory -Path $PythonDir -Force

Write-Host "Installing dependencies (Linux binaries)..."
# Install Linux binaries for Lambda (Python 3.11)
pip install -r "$BackendDir\requirements.txt" -t "$PythonDir" --platform manylinux2014_x86_64 --only-binary=:all: --implementation cp --python-version 3.11 --abi cp311 --upgrade

Write-Host "Layer built at $LayerDir"
