param(
    [string]$Python = "python",
    [string]$Iscc = "ISCC.exe"
)
$ErrorActionPreference = "Stop"
Push-Location $PSScriptRoot\..
try {
    & $Python -m PyInstaller --noconfirm --clean "packaging/IP Sentinel.spec"
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed." }
    & $Iscc /Q packaging/setup.iss
    if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed." }
    $artifact = Get-Item -LiteralPath release/IPSentinel_Setup_v1.2.0.exe
    $hash = (Get-FileHash -LiteralPath $artifact.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $($artifact.Name)" | Set-Content -LiteralPath "$($artifact.FullName).sha256" -Encoding ascii
    $manual = "IP_Sentinel_V1.2.0_用户使用手册.docx"
    Copy-Item -LiteralPath "docs/$manual" -Destination "release/$manual" -Force
    $portable = "release/IPSentinel_Portable_v1.2.0.zip"
    Compress-Archive -LiteralPath @("dist/IP Sentinel", "docs/$manual", "README.md", "docs/风险名单许可.txt", "docs/X4BNet-MIT.txt") -DestinationPath $portable -Force
    $portableHash = (Get-FileHash -LiteralPath $portable -Algorithm SHA256).Hash.ToLowerInvariant()
    "$portableHash  IPSentinel_Portable_v1.2.0.zip" | Set-Content -LiteralPath "$portable.sha256" -Encoding ascii
    Get-Item -LiteralPath $artifact.FullName, $portable, "release/$manual"
} finally {
    Pop-Location
}






