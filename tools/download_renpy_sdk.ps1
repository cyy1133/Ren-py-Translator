[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

function Get-ValidRenpyExe {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RootDir
    )

    if (-not (Test-Path -LiteralPath $RootDir)) {
        return $null
    }

    return Get-ChildItem -LiteralPath $RootDir -Filter "renpy.exe" -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.FullName -match "\\renpy-[^\\]+-sdk\\renpy\.exe$" } |
        Select-Object -First 1
}

$latestPage = $env:RENTRY_RENPY_LATEST_PAGE
$fallbackUrl = $env:RENTRY_RENPY_SDK_FALLBACK_URL
$targetZip = $env:RENTRY_RENPY_SDK_ZIP
$targetDir = $env:RENTRY_RENPY_SDK_DIR
$downloadUrl = $env:RENTRY_RENPY_SDK_URL

if ([string]::IsNullOrWhiteSpace($targetZip) -or [string]::IsNullOrWhiteSpace($targetDir)) {
    throw "Ren'Py SDK paths are not configured."
}

$existingExe = Get-ValidRenpyExe -RootDir $targetDir
if ($existingExe) {
    exit 0
}

if (-not (Test-Path -LiteralPath $targetZip)) {
    if (-not $downloadUrl) {
        try {
            $page = Invoke-WebRequest -Uri $latestPage -UseBasicParsing -TimeoutSec 30
            $patterns = @(
                'https://www\.renpy\.org/dl/[0-9.]+/renpy-[0-9.]+-sdk\.zip',
                'href="(/dl/[0-9.]+/renpy-[0-9.]+-sdk\.zip)"'
            )

            foreach ($pattern in $patterns) {
                $match = [regex]::Match($page.Content, $pattern, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
                if ($match.Success) {
                    $downloadUrl = $match.Value
                    if ($match.Groups.Count -gt 1 -and $match.Groups[1].Value) {
                        $downloadUrl = 'https://www.renpy.org' + $match.Groups[1].Value
                    }
                    break
                }
            }
        }
        catch {
        }
    }

    if (-not $downloadUrl) {
        $downloadUrl = $fallbackUrl
    }

    if (-not $downloadUrl) {
        throw "Failed to resolve a Ren'Py SDK download URL."
    }

    $zipDir = Split-Path -Parent $targetZip
    if ($zipDir -and -not (Test-Path -LiteralPath $zipDir)) {
        New-Item -ItemType Directory -Path $zipDir -Force | Out-Null
    }

    Invoke-WebRequest -Uri $downloadUrl -OutFile $targetZip -UseBasicParsing -TimeoutSec 120
}

if (-not (Test-Path -LiteralPath $targetZip)) {
    throw "Ren'Py SDK archive could not be found or downloaded."
}

if (-not (Test-Path -LiteralPath $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
}

Expand-Archive -LiteralPath $targetZip -DestinationPath $targetDir -Force

$preparedExe = Get-ValidRenpyExe -RootDir $targetDir
if (-not $preparedExe) {
    throw "Ren'Py SDK directory was created but renpy.exe was not found."
}

exit 0
