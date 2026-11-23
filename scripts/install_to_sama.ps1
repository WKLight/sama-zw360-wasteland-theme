<#
.SYNOPSIS
    One-click installer for WastelandDaydream_A on SAMA ZW360 Ultra (6.8" Curved OLED, 2320x1080).
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\scripts\install_to_sama.ps1 -SamaRoot "H:\SAMA_Multi_Chn"
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$SamaRoot
)

$ErrorActionPreference = 'Stop'
$SamaRoot = $SamaRoot.TrimEnd('\')
$repoRoot = Split-Path -Parent $PSScriptRoot

$exePath   = Join-Path $SamaRoot 'SAMA.exe'
$themeDir  = Join-Path $SamaRoot 'theme\10802320'
$videoDir  = Join-Path $SamaRoot 'video\10802320'

if (-not (Test-Path $exePath)) {
    throw "SAMA.exe not found in '$SamaRoot'. Please pass the root folder of SAMA_Multi_Chn."
}

New-Item -ItemType Directory -Force -Path $themeDir | Out-Null
New-Item -ItemType Directory -Force -Path $videoDir | Out-Null

$srcTheme = Join-Path $repoRoot 'release\WastelandDaydream_A.turtheme'
$srcVideo = Join-Path $repoRoot 'release\sama_wasteland_bg.mp4'

Copy-Item -Path $srcTheme -Destination (Join-Path $themeDir 'WastelandDaydream_A.turtheme') -Force
Copy-Item -Path $srcVideo -Destination (Join-Path $videoDir 'sama_wasteland_bg.mp4') -Force

Write-Host "`n[OK] Installed WastelandDaydream_A successfully!" -ForegroundColor Green
Write-Host "  Theme : $themeDir\WastelandDaydream_A.turtheme"
Write-Host "  Video : $videoDir\sama_wasteland_bg.mp4"
Write-Host "`nNext steps:"
Write-Host "  1. Restart SAMA.exe and select 'WastelandDaydream_A' in the 6.8-inch theme list."
Write-Host "  2. In SAMA Settings -> Hardware Sensors, ensure CPU temp is bound to 'CPU (Tctl/Tdie)' (AMD) or 'CPU Package' (Intel) and GPU to your discrete GPU."
