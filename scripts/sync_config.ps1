$src = "config.json"
$dst = Join-Path $env:LOCALAPPDATA "Mike\config.json"
New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
Copy-Item $src $dst -Force
Write-Host "Config synced to $dst"
