param(
  [string]$RepoPath = "C:\Users\HP\Desktop\Vardkesovna",
  [string]$RepoUrl = "https://github.com/alexdmitrievi/Vardkesonva.git",
  [string]$Branch = "main",
  [switch]$PushToRemote
)

$ErrorActionPreference = "Stop"

Write-Host "== Step 1: Ensure local repo exists and is synchronized ==" -ForegroundColor Cyan
if (-not (Test-Path $RepoPath)) {
  New-Item -ItemType Directory -Path $RepoPath | Out-Null
}

if (-not (Test-Path (Join-Path $RepoPath ".git"))) {
  git clone $RepoUrl $RepoPath
}

Set-Location $RepoPath

$originExists = $false
try {
  git remote get-url origin *> $null
  if ($LASTEXITCODE -eq 0) { $originExists = $true }
} catch {}

if ($originExists) {
  git remote set-url origin $RepoUrl
} else {
  git remote add origin $RepoUrl
}

git fetch origin
git checkout $Branch 2>$null
if ($LASTEXITCODE -ne 0) {
  git checkout -b $Branch origin/$Branch
}

git reset --hard origin/$Branch
git clean -fd

Write-Host "== Step 2: Build single n8n bundle file from workflows/*.json ==" -ForegroundColor Cyan
$wfDir = Join-Path $RepoPath "workflows"
if (-not (Test-Path $wfDir)) {
  throw "Folder not found: $wfDir"
}

$workflowFiles = Get-ChildItem $wfDir -Filter "WF_*.json" | Sort-Object Name
if ($workflowFiles.Count -eq 0) {
  throw "No workflow files WF_*.json found in $wfDir"
}

$workflows = @()
foreach ($f in $workflowFiles) {
  $json = Get-Content $f.FullName -Raw | ConvertFrom-Json
  $workflows += $json
}

$bundlePath = Join-Path $wfDir "ALL_WORKFLOWS_BUNDLE.json"
$workflows | ConvertTo-Json -Depth 100 | Set-Content -Path $bundlePath -Encoding UTF8
Write-Host "Bundle created: $bundlePath" -ForegroundColor Green

Write-Host "== Step 3: Optional push to GitHub ==" -ForegroundColor Cyan
if ($PushToRemote) {
  git add workflows/ALL_WORKFLOWS_BUNDLE.json
  git commit -m "Add single-file n8n workflows bundle" 2>$null
  if ($LASTEXITCODE -ne 0) {
    Write-Host "Nothing to commit (bundle unchanged)." -ForegroundColor Yellow
  }
  git push origin $Branch
  Write-Host "Pushed to origin/$Branch" -ForegroundColor Green
} else {
  Write-Host "Push skipped. Re-run with -PushToRemote to push bundle." -ForegroundColor Yellow
}

Write-Host "== Done ==" -ForegroundColor Green
