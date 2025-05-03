# build.ps1

# Stop on any error
$ErrorActionPreference = "Stop"

# Activate the virtual environment
$venvActivate = ".venv\Scripts\Activate.ps1"
if (-Not (Test-Path $venvActivate)) {
    Write-Error "Virtual environment not found at $venvActivate"
    exit 1
}
. $venvActivate

# Build using pyinstaller
pyinstaller main.py `
    --name "block-adobe" `
    --noconfirm `
    --onefile `
    --uac-admin `
    --windowed
