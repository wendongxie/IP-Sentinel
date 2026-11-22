param(
    [string]$Python = "python",
    [string]$Iscc = "ISCC.exe",
    [string]$Gitleaks = "gitleaks.exe",
    [string]$Sources,
    [string]$OutputRoot
)
$ErrorActionPreference = "Stop"
$repository = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
if (!$OutputRoot) { $OutputRoot = Join-Path $repository ".build-tools/release-runs" }
$OutputRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($OutputRoot)
$run = Join-Path $OutputRoot ([Guid]::NewGuid().ToString("N"))
$reports = Join-Path $run "reports"
New-Item -ItemType Directory -Path $reports -Force | Out-Null
Write-Host "Release run: $run"
$pythonExe = (Get-Command $Python -CommandType Application).Source
$source = Join-Path $run "source"

function Invoke-Checked {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Failed ($LASTEXITCODE): $Program $($Arguments[0]); reports: $reports" }
}

$archive = Join-Path $run "source.zip"
Invoke-Checked git @("-C", $repository, "archive", "--format=zip", "--output=$archive", "HEAD")
Expand-Archive -LiteralPath $archive -DestinationPath $source
Invoke-Checked $pythonExe @("-I", "$source/packaging/release_check.py", "runtime", "--report", "$reports/runtime")

if (!$Sources) { throw "Provide -Sources with the verified corresponding-source archives." }
$Sources = (Resolve-Path -LiteralPath $Sources).Path
$compiler = (Get-Command $Iscc -CommandType Application).Source
$scanner = (Get-Command $Gitleaks -CommandType Application).Source
# Qt wheels contain nested QML build files. Keep the install root short on hosts
# that enforce MAX_PATH, independently of where reports and outputs are stored.
$environment = Join-Path $repository (".build-tools/w-" + (Split-Path $run -Leaf).Substring(0, 8))
if (Test-Path -LiteralPath $environment) { throw "Build environment already exists: $environment" }
Invoke-Checked $pythonExe @("-I", "-m", "venv", $environment)
$buildPython = Join-Path $environment "Scripts/python.exe"

Push-Location $source
try {
    Invoke-Checked $buildPython @("-I", "-m", "pip", "--isolated", "install", "--index-url", "https://pypi.org/simple", "--only-binary=:all:", "--require-hashes", "-r", "packaging/release-lock-cp312-win_amd64.txt")
    Invoke-Checked $buildPython @("-I", "packaging/release_check.py", "pre", "--report", "$reports/pre", "--sources", $Sources, "--gitleaks", $scanner)
    $originalPath, $originalTemp, $originalTmp = $env:PATH, $env:TEMP, $env:TMP
    try {
        $env:PATH = "$(Split-Path $buildPython);$env:SystemRoot\System32;$env:SystemRoot"
        $env:TEMP = (New-Item -ItemType Directory -Path (Join-Path $run "freeze-temp")).FullName
        $env:TMP = $env:TEMP
        Invoke-Checked $buildPython @("-I", "-m", "PyInstaller", "--noconfirm", "--clean", "packaging/IP Sentinel.spec")
    } finally {
        $env:PATH, $env:TEMP, $env:TMP = $originalPath, $originalTemp, $originalTmp
    }

    $policy = Get-Content packaging/release-policy.json -Raw | ConvertFrom-Json
    $version = $policy.version
    $payload = "dist/IP Sentinel"
    Copy-Item -LiteralPath "release-compliance" -Destination "$payload/release-compliance" -Recurse
    Copy-Item -LiteralPath @("docs/THIRD_PARTY_NOTICES.md", "docs/QT_LGPL_COMPLIANCE.md") -Destination "$payload/release-compliance"
    Invoke-Checked $buildPython @("-I", "packaging/release_check.py", "payload", "--input", $payload, "--report", "$reports/payload", "--gitleaks", $scanner)
    Invoke-Checked $compiler @("/Q", "packaging/setup.iss")

    $manual = "IP_Sentinel_V$($version)_用户使用手册.docx"
    Copy-Item -LiteralPath "docs/$manual" -Destination "release/$manual"
    $portable = "release/IPSentinel_Portable_v$version.zip"
    Compress-Archive -LiteralPath @($payload, "docs/$manual", "README.md", "docs/风险名单许可.txt", "docs/X4BNet-MIT.txt") -DestinationPath $portable
    $sourceIndex = Get-Content release-compliance/sources.json -Raw | ConvertFrom-Json
    $sourceFiles = @($sourceIndex | ForEach-Object { Join-Path $Sources $_.archive })
    $sourceBundle = "release/IPSentinel_Sources_v$version.zip"
    Compress-Archive -LiteralPath $sourceFiles -DestinationPath $sourceBundle
    $artifacts = @("release/IPSentinel_Setup_v$version.exe", $portable, "release/$manual", $sourceBundle)
    $artifacts | ForEach-Object {
        $file = Get-Item -LiteralPath $_
        "$((Get-FileHash -LiteralPath $file.FullName).Hash.ToLowerInvariant())  $($file.Name)"
    } | Set-Content -LiteralPath release/SHA256SUMS.txt -Encoding utf8NoBOM
    Invoke-Checked $buildPython @("-I", "packaging/release_check.py", "artifacts", "--input", "release", "--report", "$reports/artifacts", "--gitleaks", $scanner)
    Get-Item -LiteralPath $artifacts
} finally {
    Pop-Location
}






