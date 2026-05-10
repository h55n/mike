# uninstall.ps1 — Mike Uninstaller
# Run: Right-click → Run with PowerShell

$AppName    = "Mike"
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\$AppName"
$DestExe    = Join-Path $InstallDir "Mike.exe"

Write-Host ""
Write-Host "  Uninstalling Mike..." -ForegroundColor Cyan

# Kill running instance
Get-Process -Name "Mike" -ErrorAction SilentlyContinue | Stop-Process -Force

# Remove exe + install dir
if (Test-Path $InstallDir) {
    Remove-Item -Path $InstallDir -Recurse -Force
    Write-Host "  Removed install directory." -ForegroundColor Gray
}

# Remove Desktop shortcut
$DesktopLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "$AppName.lnk"
if (Test-Path $DesktopLnk) { Remove-Item $DesktopLnk -Force }

# Remove Start Menu
$StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$AppName"
if (Test-Path $StartMenuDir) { Remove-Item $StartMenuDir -Recurse -Force }

# Remove startup registry
$RegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Remove-ItemProperty -Path $RegPath -Name $AppName -ErrorAction SilentlyContinue

# Remove uninstall entry
$UninstRegPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
Remove-Item -Path $UninstRegPath -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "  Mike uninstalled." -ForegroundColor Green
Read-Host "  Press Enter to close"
