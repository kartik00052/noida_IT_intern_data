param(
  [switch]$SkipCollector,
  [int]$Port = 8000,
  [string]$AsOf = '2026-11-21'
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

if (-not $SkipCollector) {
  python scripts\noida_it_collector.py --enrich --limit 200 --out-dir data
} else {
  Write-Host 'Skipping collector (using repo-local raw leads).'
}

python scripts\build_datasets.py --as-of $AsOf
python -m pytest tests\test_data.py -q

if (-not (Test-Path (Join-Path $PSScriptRoot 'tests\node_modules'))) {
  npm install --prefix tests --no-audit --no-fund
}
node tests\check_dashboard.js

Write-Host "Dashboard: http://localhost:$Port/dashboard/index.html"
python -m http.server $Port
