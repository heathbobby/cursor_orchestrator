param(
  [switch]$Clean = $true,
  [switch]$EnableCursor = $false
)

$ErrorActionPreference = "Stop"

function Assert-PathExists([string]$Path, [string]$Message) {
  if (!(Test-Path $Path)) {
    throw "$Message ($Path)"
  }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$src = Join-Path $PSScriptRoot "SaaSGen"
$dst = Join-Path $PSScriptRoot "SaaSGen.bootstrapped"

Write-Host "Repo root: $repoRoot"

if (!(Test-Path $src)) {
  Write-Host "SaaSGen not found at $src. Skipping."
  exit 0
}

Write-Host "Using SaaSGen source: $src"
Write-Host "Bootstrapping into: $dst"

if ($Clean -and (Test-Path $dst)) {
  Remove-Item $dst -Recurse -Force
}

if (!(Test-Path $dst)) {
  Copy-Item -Recurse -Force $src $dst
}

# Prevent nested git repo issues (we want this to be a pure workspace copy)
if (Test-Path (Join-Path $dst ".git")) {
  Remove-Item (Join-Path $dst ".git") -Recurse -Force
}

# Copy minimal framework payload into the scenario project
New-Item -ItemType Directory -Force (Join-Path $dst "orchestration-framework") | Out-Null
$itemsToCopy = @(
  "bootstrap.py",
  "cli.py",
  "requirements.txt",
  "config.yaml.example",
  "templates",
  "tools"
)
foreach ($item in $itemsToCopy) {
  $srcItem = Join-Path $repoRoot $item
  if (Test-Path $srcItem) {
    Copy-Item -Recurse -Force $srcItem (Join-Path $dst "orchestration-framework")
  }
}

# Run bootstrap + a minimal orchestration loop
Push-Location $dst
try {
  if ($EnableCursor) {
    python .\orchestration-framework\bootstrap.py --init --project-name "SaaSGen" --trunk-branch main
  } else {
    python .\orchestration-framework\bootstrap.py --init --project-name "SaaSGen" --trunk-branch main --no-cursor
  }
  if ($LASTEXITCODE -ne 0) { throw "bootstrap.py failed" }

  # Ensure config gets patched for dry-run agent launching in environments without Cursor installed.
  $cfgPath = Join-Path $dst ".orchestration\\config\\framework.yaml"
  Assert-PathExists $cfgPath "Missing framework.yaml"
  $cfg = Get-Content $cfgPath -Raw
  if ($cfg -notmatch "(?m)^cursor:\\s*$") {
    Add-Content -Path $cfgPath -Value "`ncursor:`n  enabled: true`n  agent_command: agent`n  agent_runner_prefix: []`n  agent_output_format: text`n  agent_max_parallel: 3`n"
  } elseif ($cfg -notmatch "(?m)^\\s+agent_command:") {
    Add-Content -Path $cfgPath -Value "`n  agent_command: agent`n  agent_runner_prefix: []`n  agent_output_format: text`n  agent_max_parallel: 3`n"
  }

  python .\orchestration-framework\cli.py execute "/orchestrator::ingest_project" | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "ingest_project failed" }
  python .\orchestration-framework\cli.py execute "/orchestrator::derive_roles" | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "derive_roles failed" }

  # Status + knowledge artifacts (should help us assess compatibility with existing AI-agent guidance)
  python .\orchestration-framework\cli.py execute "/orchestrator::update_knowledge" | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "update_knowledge failed" }
  python .\orchestration-framework\cli.py execute "/orchestrator::render_status" | Out-Null
  if ($LASTEXITCODE -ne 0) { throw "render_status failed" }

  Write-Host "OK SaaSGen scenario completed. Review:"
  Write-Host "  - .orchestration\\config\\project_profile.yaml"
  Write-Host "  - .orchestration\\config\\derived_roles.yaml"
  Write-Host "  - .orchestration\\knowledge\\"
  Write-Host "  - .orchestration\\runtime\\status\\STATUS.md"
} finally {
  Pop-Location
}

