param(
    [string]$TexFile = "report_lecture.tex",
    [string]$OutputDir = "."
)

$ErrorActionPreference = "Stop"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$logPath = Join-Path $scriptDir "build_report_lecture.log"

Push-Location $scriptDir
try {
    if (Test-Path $logPath) {
        Remove-Item $logPath -Force
    }

    xelatex -interaction=nonstopmode -halt-on-error -output-directory $OutputDir $TexFile 2>&1 |
        Tee-Object -FilePath $logPath
    xelatex -interaction=nonstopmode -halt-on-error -output-directory $OutputDir $TexFile 2>&1 |
        Tee-Object -FilePath $logPath -Append

    Write-Host ""
    Write-Host "Build complete."
    Write-Host "PDF: $(Join-Path $scriptDir 'report_lecture.pdf')"
    Write-Host "Log: $logPath"
}
finally {
    Pop-Location
}
