# build_and_install.ps1 - One-click: build Mike.exe + install as Windows app
# Run: Right-click -> Run with PowerShell
#      OR: powershell -ExecutionPolicy Bypass -File build_and_install.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

$AppName    = "Mike"
$ExeName    = "Mike.exe"
$Version    = "2.0.0"
$Publisher  = "Antigravity"

Write-Host ""
Write-Host "  =====================================" -ForegroundColor Cyan
Write-Host "        Mike - Build & Install       " -ForegroundColor Cyan
Write-Host "  =====================================" -ForegroundColor Cyan
Write-Host ""

# Locate Python in venv
$VenvPython = Join-Path $ScriptDir "venv\Scripts\python.exe"
$VenvPip    = Join-Path $ScriptDir "venv\Scripts\pip.exe"
$VenvPyInst = Join-Path $ScriptDir "venv\Scripts\pyinstaller.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "  [ERROR] venv not found at: $VenvPython" -ForegroundColor Red
    Write-Host "  Create it: python -m venv venv; venv\Scripts\pip install -r requirements.txt" -ForegroundColor Yellow
    Read-Host "  Press Enter to exit"
    exit 1
}

Write-Host "  Python : $VenvPython" -ForegroundColor Gray
Write-Host ""

# Step 1: Kill any running Mike instance
Write-Host "  [1/6] Stopping any running Mike instance..." -ForegroundColor White
Get-Process -Name "Mike" -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "        Killing PID $($_.Id)" -ForegroundColor Gray
    $_ | Stop-Process -Force
}
Start-Sleep -Milliseconds 800

# Step 2: Install / update Python deps
Write-Host "  [2/6] Installing Python dependencies..." -ForegroundColor White
& $VenvPip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [ERROR] pip install failed." -ForegroundColor Red
    Read-Host "  Press Enter to exit"; exit 1
}
Write-Host "        Dependencies OK" -ForegroundColor Green

# Step 3: Generate assets from SVGs
Write-Host "  [3/6] Generating assets from SVGs..." -ForegroundColor White
& $VenvPython generate_assets.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [WARN] Asset generation had errors - continuing anyway" -ForegroundColor Yellow
}

# Verify ICO was created properly
$IcoPath = Join-Path $ScriptDir "assets\mike.ico"
if (-not (Test-Path $IcoPath) -or (Get-Item $IcoPath).Length -lt 1000) {
    Write-Host "  [WARN] mike.ico missing or tiny - icon may look wrong in Explorer" -ForegroundColor Yellow
}

# Step 4: PyInstaller build
Write-Host "  [4/6] Building Mike.exe (this takes ~2 min)..." -ForegroundColor White
if (-not (Test-Path $VenvPyInst)) {
    Write-Host "  [ERROR] pyinstaller not found in venv. Run: pip install pyinstaller" -ForegroundColor Red
    Read-Host "  Press Enter to exit"; exit 1
}

$OldErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $VenvPyInst mike.spec --noconfirm --clean 2>&1 | ForEach-Object {
    if ($_ -match "ERROR|WARN") { Write-Host "        $_" -ForegroundColor Yellow }
}
$ErrorActionPreference = $OldErrorActionPreference

$SrcExe = Join-Path $ScriptDir "dist\$ExeName"
if (-not (Test-Path $SrcExe)) {
    Write-Host "  [ERROR] Build failed - dist\Mike.exe not found." -ForegroundColor Red
    Read-Host "  Press Enter to exit"; exit 1
}
$ExeSize = [math]::Round((Get-Item $SrcExe).Length / 1MB, 1)
Write-Host "        Build OK - Mike.exe ($ExeSize MB)" -ForegroundColor Green

# Step 5: Install
Write-Host "  [5/6] Installing Mike..." -ForegroundColor White

$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\$AppName"
$DestExe    = Join-Path $InstallDir $ExeName
$ConfigSrc  = Join-Path $ScriptDir "config.json"
$ConfigDir  = Join-Path $env:LOCALAPPDATA "Mike"
$ConfigDest = Join-Path $ConfigDir "config.json"
$IconDest   = Join-Path $InstallDir "mike.ico"

# Create install dir and copy exe
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path $SrcExe -Destination $DestExe -Force
Write-Host "        Exe -> $DestExe" -ForegroundColor Gray

# Copy icon
if (Test-Path $IcoPath) {
    Copy-Item -Path $IcoPath -Destination $IconDest -Force
}

# Config - preserve existing (don't wipe API key)
New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null
if (-not (Test-Path $ConfigDest)) {
    Copy-Item -Path $ConfigSrc -Destination $ConfigDest -Force
    Write-Host "        Config created - set Groq API key in: $ConfigDest" -ForegroundColor Yellow
} else {
    Write-Host "        Existing config preserved" -ForegroundColor Green
}

# Desktop shortcut
$WShell = New-Object -ComObject WScript.Shell
$DesktopLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "$AppName.lnk"
$Shortcut = $WShell.CreateShortcut($DesktopLnk)
$Shortcut.TargetPath       = $DestExe
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description      = "Mike - AI Voice Dictation"
if (Test-Path $IconDest) { $Shortcut.IconLocation = $IconDest }
$Shortcut.Save()
Write-Host "        Desktop shortcut created" -ForegroundColor Gray

# Start Menu shortcut
$StartMenuDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$AppName"
New-Item -ItemType Directory -Force -Path $StartMenuDir | Out-Null
$StartLnk = Join-Path $StartMenuDir "$AppName.lnk"
$Shortcut2 = $WShell.CreateShortcut($StartLnk)
$Shortcut2.TargetPath       = $DestExe
$Shortcut2.WorkingDirectory = $InstallDir
$Shortcut2.Description      = "Mike - AI Voice Dictation"
if (Test-Path $IconDest) { $Shortcut2.IconLocation = $IconDest }
$Shortcut2.Save()
Write-Host "        Start Menu entry created" -ForegroundColor Gray

# Windows startup registry
$RegRun = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $RegRun -Name $AppName -Value "`"$DestExe`" --startup"
Write-Host "        Startup registry set - Mike starts with Windows" -ForegroundColor Gray

# Apps & Features uninstall entry
$UninstKey = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\$AppName"
if (-not (Test-Path $UninstKey)) { New-Item -Path $UninstKey -Force | Out-Null }
Set-ItemProperty -Path $UninstKey -Name "DisplayName"     -Value $AppName
Set-ItemProperty -Path $UninstKey -Name "DisplayVersion"  -Value $Version
Set-ItemProperty -Path $UninstKey -Name "Publisher"       -Value $Publisher
Set-ItemProperty -Path $UninstKey -Name "DisplayIcon"     -Value $IconDest
Set-ItemProperty -Path $UninstKey -Name "InstallLocation" -Value $InstallDir
Set-ItemProperty -Path $UninstKey -Name "UninstallString" -Value "powershell -ExecutionPolicy Bypass -File `"$ScriptDir\uninstall.ps1`""
Set-ItemProperty -Path $UninstKey -Name "NoModify"        -Value 1 -Type DWord
Set-ItemProperty -Path $UninstKey -Name "NoRepair"        -Value 1 -Type DWord

# Step 6: Launch
Write-Host "  [6/6] Launching Mike..." -ForegroundColor White
Start-Process -FilePath $DestExe

Write-Host ""
Write-Host "  [OK] Mike v$Version installed and running!" -ForegroundColor Green
Write-Host ""
Write-Host "  Location : $DestExe"          -ForegroundColor Gray
Write-Host "  Config   : $ConfigDest"       -ForegroundColor Gray
Write-Host "  Startup  : Auto-starts with Windows" -ForegroundColor Gray
Write-Host "  Uninstall: Run uninstall.ps1" -ForegroundColor Gray
Write-Host ""
