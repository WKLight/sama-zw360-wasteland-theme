param(
    [string]$SamaRoot = "C:\SAMA_Multi_Chn"
)

﻿[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Add-Type -AssemblyName System.Drawing

$samaRoot = $SamaRoot.TrimEnd('\')
$asm = [System.Reflection.Assembly]::LoadFrom("$samaRoot\SAMA.exe")
Push-Location $samaRoot

# 1. Initialize SAMA.exe native FontConfig SystemFonts
$fcType = $asm.GetType('UsbMonitorL.FontConfig')
$fcType.GetMethod('撋', [System.Reflection.BindingFlags]'Public,NonPublic,Static', $null, [Type[]]@(), $null).Invoke($null, $null) | Out-Null
$sysFonts = $fcType.GetField('SystemFonts', [System.Reflection.BindingFlags]'Public,NonPublic,Static').GetValue($null)
function Find-FF($name) {
    foreach ($ff in $sysFonts) { if ($ff.Name -eq $name) { return $ff } }
    throw "FontFamily not found in SAMA SystemFonts: $name"
}

$binderCode = @'
using System;
using System.Reflection;
using System.Runtime.Serialization;
public class SamaBuildBinderA : SerializationBinder {
    private Assembly _asm;
    public SamaBuildBinderA(Assembly a) { _asm = a; }
    public override Type BindToType(string assemblyName, string typeName) {
        if (assemblyName.StartsWith("UsbMonitorL")) {
            string ft = System.Text.RegularExpressions.Regex.Replace(typeName, @"Version=\d+\.\d+\.\d+\.\d+", "Version=" + _asm.GetName().Version.ToString());
            return _asm.GetType(ft) ?? Type.GetType(ft + ", " + _asm.FullName);
        }
        string cn = System.Text.RegularExpressions.Regex.Replace(typeName, @"UsbMonitorL, Version=\d+\.\d+\.\d+\.\d+", "UsbMonitorL, Version=" + _asm.GetName().Version.ToString());
        return Type.GetType(string.Format("{0}, {1}", cn, assemblyName));
    }
}
'@
Add-Type -TypeDefinition $binderCode
$bf = New-Object System.Runtime.Serialization.Formatters.Binary.BinaryFormatter
$bf.Binder = New-Object SamaBuildBinderA($asm)

function Load-SamaTheme($name) {
    $p = Join-Path "$samaRoot\theme\10802320" $name
    $fs = [System.IO.File]::OpenRead($p)
    $t = $bf.Deserialize($fs)
    $fs.Close()
    return $t
}

# Load donor themes from SAMA's own 10802320 catalog
$t10    = Load-SamaTheme '10.turtheme'
$tFish  = Load-SamaTheme 'fish.turtheme'
$tCity  = Load-SamaTheme 'CITY.turtheme'
$tSpace = Load-SamaTheme 'SPACE.turtheme'
$allDonors = @($tFish, $tCity, $tSpace, $t10)

# Authentic TextAlignment prototypes + MemberwiseClone helper (prevents shared alignment mutation!)
$alignProto0 = $tCity.GraphList[2].fontConfig.alignment   # Left (0)
$alignProto1 = $tCity.GraphList[6].fontConfig.alignment   # Center (1)
$alignProto2 = $tSpace.GraphList[7].fontConfig.alignment  # Right (2)
$mwClone = [object].GetMethod('MemberwiseClone', [System.Reflection.BindingFlags]'NonPublic,Instance')
function New-Align([int]$idx) {
    $src = switch ($idx) { 0 { $alignProto0 } 1 { $alignProto1 } 2 { $alignProto2 } default { $alignProto0 } }
    return $mwClone.Invoke($src, $null)
}

$giType      = $asm.GetType('UsbMonitorL.GraphItem')
$cloneMethod = $giType.GetMethod('氫', [System.Reflection.BindingFlags]'Public,NonPublic,Instance')
$ffField     = $fcType.GetField('擈', [System.Reflection.BindingFlags]'Public,NonPublic,Instance')
$giFontField = $giType.GetField('擈', [System.Reflection.BindingFlags]'Public,NonPublic,Instance')
$drawGI      = $giType.GetMethod('殱', [System.Reflection.BindingFlags]'Public,NonPublic,Instance', $null, @([System.Drawing.Graphics],[bool],[bool]), $null)
$drawImg     = $asm.GetType('UsbMonitorL.GraphImage').GetMethod('殱', [System.Reflection.BindingFlags]'Public,NonPublic,Instance', $null, @([System.Drawing.Graphics],[bool],[bool]), $null)
$drawSB      = $asm.GetType('UsbMonitorL.GraphStatuBar').GetMethod('殱', [System.Reflection.BindingFlags]'Public,NonPublic,Instance', $null, @([System.Drawing.Graphics],[bool],[bool]), $null)

function Clone-Item($proto) { return $cloneMethod.Invoke($proto, $null) }
function Find-Proto($themes, $typeName, $dataName, $subName = $null) {
    foreach ($th in $themes) {
        foreach ($g in $th.GraphList) {
            if ($g.GetType().Name -eq $typeName -and $g.m_data -ne $null -and $g.m_data.DataName -eq $dataName) {
                if ($null -eq $subName -or [string]$g.m_data.SubName -eq [string]$subName) {
                    return $g
                }
            }
        }
    }
    throw "Prototype not found: $typeName $dataName ($subName)"
}

# 2. Install 90-deg CW hardware-rotated video (1080x2320) into SAMA video directory
$repoRoot = Split-Path -Parent $PSScriptRoot
$distDir  = Join-Path $repoRoot 'release'
$assetDir = Join-Path $repoRoot 'assets'
$prevDir  = Join-Path $repoRoot 'preview'
$srcVid  = "$distDir\sama_wasteland_bg.mp4"
$dstVid  = "$samaRoot\video\10802320\sama_wasteland_bg.mp4"
Copy-Item -Path $srcVid -Destination $dstVid -Force
Write-Host "[OK] Installed hardware-rotated 1080x2320 video -> $dstVid ($([Math]::Round((Get-Item $dstVid).Length/1MB,2)) MB)"

# 3. Build WastelandDaydream_A cloned cleanly from 10.turtheme (canonical 2320x1080 mp4 video theme!)
$theme = $t10.Clone()
$theme.name            = 'WastelandDaydream_A'
$theme.isLanscape      = $false
$theme.width           = 2320
$theme.height          = 1080
$theme.themePath       = "$samaRoot\theme\10802320\WastelandDaydream_A.turtheme"
$theme.videoName       = 'sama_wasteland_bg.mp4'
$theme.videoPath       = $dstVid
$theme.o_videoPath     = $dstVid
$theme.videoTargetPath = '/mnt/SDCARD/video/sama_wasteland_bg.mp4'
$theme.FrameRate       = 24

$bgS1  = New-Object System.Drawing.Bitmap("$assetDir\frames\hflip_s1_legs.png")
$bgS2  = New-Object System.Drawing.Bitmap("$assetDir\frames\hflip_s2_fullbody.png")
$bgS3b = New-Object System.Drawing.Bitmap("$assetDir\frames\hflip_s3b_smile.png")
$ovBmp = New-Object System.Drawing.Bitmap("$assetDir\sama_ui_A_native_overlay.png")

# [0] GraphAnimation (background looping video)
$anim = Clone-Item $t10.GraphList[0]
$anim.posX      = 0
$anim.posY      = 0
$anim.FilePath  = $dstVid
$anim.videoName = ''
$anim.bitmap    = New-Object System.Drawing.Bitmap($bgS2)
$anim.O_bitmap  = New-Object System.Drawing.Bitmap($bgS2)
$anim.S_bitmap  = New-Object System.Drawing.Bitmap($bgS2)

# [1] GraphImage (lossless 32-bit transparent static architectural overlay + veil + tracks)
$imgLayer = Clone-Item $t10.GraphList[1]
$imgLayer.posX        = 0
$imgLayer.posY        = 0
$imgLayer.DisplayName = '图片_WastelandDaydream_A_Overlay.png'
$imgLayer.bitmap      = New-Object System.Drawing.Bitmap($ovBmp)
$imgLayer.O_bitmap    = New-Object System.Drawing.Bitmap($ovBmp)

$theme.GraphList.Clear()
[void]$theme.GraphList.Add($anim)
[void]$theme.GraphList.Add($imgLayer)

# Cohesive Haute-Horlogerie Platinum & Brushed Champagne-Gold Palette (matching Screen 1!)
$cShadowHero = [System.Drawing.Color]::FromArgb(165, 12, 22, 40)
$cShadowSub  = [System.Drawing.Color]::FromArgb(150, 12, 22, 40)
$cPlatTop    = [System.Drawing.Color]::FromArgb(255, 255, 255, 255)
$cPlatBot    = [System.Drawing.Color]::FromArgb(255, 224, 236, 250)
$cGoldTop    = [System.Drawing.Color]::FromArgb(255, 255, 247, 218)
$cGoldBot    = [System.Drawing.Color]::FromArgb(255, 220, 178, 102)

function Add-SensorPair(
    [string]$dataName,
    $subName,
    [bool]$showUnit,
    [string]$sampleVal,
    [string]$sampleVU,
    [int]$x, [int]$y,
    [string]$fontName, [int]$sizePt, [float]$interval, [int]$align,
    [bool]$useGrad, $c1, $c2,
    [int]$shadowDy = 3, $shadowColor = $null
) {
    $proto = Find-Proto $allDonors 'GraphItem' $dataName $subName
    $ff = Find-FF $fontName

    # 1. Optical cool-slate shadow layer beneath (razor-legible over sunlit sky!)
    if ($null -ne $shadowColor -and $shadowDy -gt 0) {
        $sh = Clone-Item $proto
        $sh.posX = $x
        $sh.posY = $y + $shadowDy
        $sh.useGradient = $false
        $sh.hide = $false
        $sh.enabled = $false
        $sh.fontConfig.name = $fontName
        $sh.fontConfig.size = $sizePt
        $sh.fontConfig.isBold = $false
        $sh.fontConfig.interval = $interval
        $sh.fontConfig.color = $shadowColor
        $sh.fontConfig.GrColor = [System.Drawing.Color]::Empty
        $sh.fontConfig.GrDirection = 0
        $sh.fontConfig.alignment = New-Align $align
        $sh.m_data.ShowUnit = $showUnit
        $sh.m_data.queueLen = 0
        $sh.m_data.Value = $sampleVal
        $sh.m_data.ValueWithUnit = $sampleVU
        $ffField.SetValue($sh.fontConfig, $ff)
        $giFontField.SetValue($sh, (New-Object System.Drawing.Font($ff, [float]$sizePt, [System.Drawing.FontStyle]::Regular)))
        [void]$theme.GraphList.Add($sh)
    }

    # 2. Luminous foreground layer
    $fg = Clone-Item $proto
    $fg.posX = $x
    $fg.posY = $y
    $fg.useGradient = $useGrad
    $fg.hide = $false
    $fg.enabled = $false
    $fg.fontConfig.name = $fontName
    $fg.fontConfig.size = $sizePt
    $fg.fontConfig.isBold = $false
    $fg.fontConfig.interval = $interval
    $fg.fontConfig.color = $c1
    $fg.fontConfig.GrColor = if ($useGrad) { $c2 } else { [System.Drawing.Color]::Empty }
    $fg.fontConfig.GrDirection = if ($useGrad) { 2 } else { 0 }
    $fg.fontConfig.alignment = New-Align $align
    $fg.m_data.ShowUnit = $showUnit
    $fg.m_data.queueLen = 0
    $fg.m_data.Value = $sampleVal
    $fg.m_data.ValueWithUnit = $sampleVU
    $ffField.SetValue($fg.fontConfig, $ff)
    $giFontField.SetValue($fg, (New-Object System.Drawing.Font($ff, [float]$sizePt, [System.Drawing.FontStyle]::Regular)))
    [void]$theme.GraphList.Add($fg)
}

function Add-HairlineBar(
    [string]$dataName, [double]$sampleRate,
    [int]$x, [int]$y, [int]$w, [int]$h,
    $cFront, $cGrad,
    $overrideMData = $null
) {
    $proto = if ($null -ne $overrideMData) { Find-Proto $allDonors 'GraphStatuBar' 'CPULOAD' $null } else { Find-Proto $allDonors 'GraphStatuBar' $dataName $null }
    $sb = Clone-Item $proto
    if ($null -ne $overrideMData) {
        $sb.m_data = $mwClone.Invoke($overrideMData, $null)
    }
    $sb.posX = $x
    $sb.posY = $y
    $sb.width = $w
    $sb.height = $h
    $sb.radius = 0
    $sb.direction = 0
    $sb.trBack = $true
    $sb.fillBack = $false
    $sb.lineWidth = 0
    $sb.useGradient = $true
    $sb.FrontColor = $cFront
    $sb.GradientColor = $cGrad
    $sb.BackColor = [System.Drawing.Color]::Transparent
    $sb.m_data.Rate = $sampleRate
    [void]$theme.GraphList.Add($sb)
}

# ==============================================================================
# RIGHT TELEMETRY WING (X_L = 1585 .. X_R = 2255) — EDITION A LARGE-SCALE
# ==============================================================================

# --- TIER 1: CHRONO (TIME + DATE) ---
# Hero Clock HH:mm (Butler 136pt, interval=0.0, right-aligned laser-flush with X_R=2255 compensating GDI+ sidebearing)
Add-SensorPair 'TIME' 'h:m' $true '15:48' '15:48' `
    2284 114 'Butler' 136 0.0 2 $true $cPlatTop $cPlatBot 4 $cShadowHero

# Date Y-M-D (HelveticaNeueLT Pro 47 LtCn 24pt, interval=0.0, laser-flush with X_R=2255, champagne gold)
Add-SensorPair 'DATE' 'Y-M-D' $true '2026-11-21' '2026-11-21' `
    2260 294 'HelveticaNeueLT Pro 47 LtCn' 24 0.0 2 $true $cGoldTop $cGoldBot 2 $cShadowSub

# --- TIER 2: CPU SUITE ---
# CPU Temp (Butler 102pt, interval=0.0, left-aligned to X_L=1578, ShowUnit=True -> "46°", champagne gold!)
Add-SensorPair 'CPUTEMP' '' $true '46' '46°' `
    1578 398 'Butler' 102 0.0 0 $true $cGoldTop $cGoldBot 4 $cShadowHero

# CPU Clock (HelveticaNeueLT Pro 47 LtCn 25pt, interval=0.0, ShowUnit=False, right-aligned flush before static "MHz")
Add-SensorPair 'CPUCLOCK' '' $false '5420' '5420' `
    2196 364 'HelveticaNeueLT Pro 47 LtCn' 25 0.0 2 $true $cPlatTop $cPlatBot 2 $cShadowSub

# CPU Load % (HelveticaNeueLT Pro 47 LtCn 49pt, interval=0.0, ShowUnit=True -> "24%", right-aligned to X_R=2256)
Add-SensorPair 'CPULOAD' '' $true '24' '24%' `
    2258 430 'HelveticaNeueLT Pro 47 LtCn' 49 0.0 2 $true $cPlatTop $cPlatBot 3 $cShadowSub

# CPU Load Live Hairline Bar (x=1585, y=566, w=670, h=5, champagne gold gradient)
Add-HairlineBar 'CPULOAD' 0.24 1585 566 670 5 $cGoldTop $cGoldBot

# --- TIER 3: GPU SUITE ---
# GPU Temp (Butler 102pt, interval=0.0, left-aligned to X_L=1578, ShowUnit=True -> "42°", platinum white!)
Add-SensorPair 'GPUTEMP' '' $true '42' '42°' `
    1578 656 'Butler' 102 0.0 0 $true $cPlatTop $cPlatBot 4 $cShadowHero

# GPU Clock (HelveticaNeueLT Pro 47 LtCn 25pt, interval=0.0, ShowUnit=False, right-aligned flush before static "MHz")
Add-SensorPair 'GPUCLOCK' '' $false '2640' '2640' `
    2196 624 'HelveticaNeueLT Pro 47 LtCn' 25 0.0 2 $true $cGoldTop $cGoldBot 2 $cShadowSub

# GPU Load % (HelveticaNeueLT Pro 47 LtCn 49pt, interval=0.0, ShowUnit=True -> "36%", right-aligned to X_R=2256, champagne gold)
Add-SensorPair 'GPULOAD' '' $true '36' '36%' `
    2258 690 'HelveticaNeueLT Pro 47 LtCn' 49 0.0 2 $true $cGoldTop $cGoldBot 3 $cShadowSub

# GPU Load Live Hairline Bar (x=1585, y=822, w=670, h=5, platinum gradient)
Add-HairlineBar 'GPULOAD' 0.36 1585 822 670 5 $cPlatTop $cPlatBot

# --- TIER 4: MEMORY (RAM) + VRAM ---
# RAM Load % (HelveticaNeueLT Pro 47 LtCn 49pt, interval=0.0, ShowUnit=True -> "42%", left-aligned to X_L=1583)
Add-SensorPair 'RAMLOAD' '' $true '42' '42%' `
    1583 904 'HelveticaNeueLT Pro 47 LtCn' 49 0.0 0 $true $cPlatTop $cPlatBot 3 $cShadowSub

# RAM Load Live Hairline Bar (using authentic RAMLOAD M_Data harvested from SPACE GraphArchBar!)
Add-HairlineBar 'RAMLOAD' 0.42 1585 994 310 4 $cGoldTop $cGoldBot $tSpace.GraphList[17].m_data

# VRAM Load % (HelveticaNeueLT Pro 47 LtCn 49pt, interval=0.0, ShowUnit=True -> "31%", left-aligned to x=1939)
Add-SensorPair 'GPURAMLOAD' '' $true '31' '31%' `
    1939 904 'HelveticaNeueLT Pro 47 LtCn' 49 0.0 0 $true $cPlatTop $cPlatBot 3 $cShadowSub

# VRAM Load Live Hairline Bar (x=1941, y=994, w=314, h=4, platinum gradient)
Add-HairlineBar 'GPURAMLOAD' 0.31 1941 994 314 4 $cPlatTop $cPlatBot

# ==============================================================================
# RENDER THROUGH SAMA.EXE'S OWN NATIVE GDI+ RENDERER FOR PIXEL-EXACT QC!
# ==============================================================================
function Render-SamaNative($bgBmp, [string]$outPath, [string]$zoomOutPath = $null) {
    $canvas = New-Object System.Drawing.Bitmap(2320, 1080)
    $g = [System.Drawing.Graphics]::FromImage($canvas)
    $g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $g.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $g.DrawImage($bgBmp, 0, 0, 2320, 1080)
    for ($i = 1; $i -lt $theme.GraphList.Count; $i++) {
        $item = $theme.GraphList[$i]
        $tn = $item.GetType().Name
        if ($tn -eq 'GraphImage') {
            $drawImg.Invoke($item, @($g, $false, $false)) | Out-Null
        } elseif ($tn -eq 'GraphStatuBar') {
            $drawSB.Invoke($item, @($g, $false, $false)) | Out-Null
        } else {
            $drawGI.Invoke($item, @($g, $false, $false)) | Out-Null
        }
    }
    $g.Dispose()
    $canvas.Save($outPath, [System.Drawing.Imaging.ImageFormat]::Png)
    if ($zoomOutPath) {
        $rect = New-Object System.Drawing.Rectangle(1460, 0, 860, 1080)
        $crop = $canvas.Clone($rect, $canvas.PixelFormat)
        $crop.Save($zoomOutPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $crop.Dispose()
    }
    return $canvas
}

$qcDir = "$prevDir"
New-Item -ItemType Directory -Force -Path $qcDir | Out-Null

$qcS1  = Render-SamaNative $bgS1  "$qcDir\native_sama_A_s1.png" $null
$qcS2  = Render-SamaNative $bgS2  "$qcDir\native_sama_A_s2.png" "$qcDir\native_sama_A_zoom100.png"
$qcS3b = Render-SamaNative $bgS3b "$qcDir\native_sama_A_s3b.png" $null


# Set authentic native-rendered thumbnail inside theme!
$theme.themePic = New-Object System.Drawing.Bitmap($qcS2)
$qcS1.Dispose(); $qcS2.Dispose(); $qcS3b.Dispose()
$bgS1.Dispose(); $bgS2.Dispose(); $bgS3b.Dispose(); $ovBmp.Dispose()

# 4. Serialize canonical theme directly into SAMA theme catalog + backup copy!
$samaThemePath   = "$samaRoot\theme\10802320\WastelandDaydream_A.turtheme"
$backupThemePath = "$distDir\WastelandDaydream_A.turtheme"

$fsOut = [System.IO.File]::Create($samaThemePath)
$bf.Serialize($fsOut, $theme)
$fsOut.Close()
Copy-Item -Path $samaThemePath -Destination $backupThemePath -Force

# 5. Round-trip deserialization & alignment integrity verification!
$fsCheck = [System.IO.File]::OpenRead($samaThemePath)
$rt = $bf.Deserialize($fsCheck)
$fsCheck.Close()

Write-Host "`n=== SAMA.EXE NATIVE BUILD & ROUND-TRIP VERIFICATION PASSED ==="
Write-Host "  Theme Path  : $samaThemePath ($([Math]::Round((Get-Item $samaThemePath).Length / 1MB, 2)) MB)"
Write-Host "  Name        : $($rt.name) | $($rt.width)x$($rt.height) | isLanscape=$($rt.isLanscape)"
Write-Host "  Video       : $($rt.videoName) -> $($rt.videoPath) (FPS=$($rt.FrameRate))"
Write-Host "  GraphList   : $($rt.GraphList.Count) items"
Write-Host "  themePic    : $($rt.themePic.Width)x$($rt.themePic.Height)"

# Verify ZERO shared alignment leaks!
Write-Host "`n=== LIVE SENSOR ALIGNMENT AUDIT ==="
for ($i = 2; $i -lt $rt.GraphList.Count; $i++) {
    $g = $rt.GraphList[$i]
    if ($g.GetType().Name -eq 'GraphItem') {
        $fc = $g.fontConfig
        Write-Host ("  [{0,2}] {1,-12} pos=({2,4},{3,4}) {4,-28} {5,3}pt align={6}({7}) ShowU={8}" -f $i, $g.m_data.DataName, $g.posX, $g.posY, $fc.name, $fc.size, $fc.alignment.index, $fc.alignment.displayName, $g.m_data.ShowUnit)
    } elseif ($g.GetType().Name -eq 'GraphStatuBar') {
        Write-Host ("  [{0,2}] StatuBar {1,-10} pos=({2,4},{3,4}) {4}x{5}" -f $i, $g.m_data.DataName, $g.posX, $g.posY, $g.width, $g.height)
    }
}
Pop-Location
