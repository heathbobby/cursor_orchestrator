param(
  [switch]$Clean = $true
)

$ErrorActionPreference = "Stop"

function Assert-PathExists([string]$Path, [string]$Message) {
  if (!(Test-Path $Path)) {
    throw "$Message ($Path)"
  }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$projects = @("python-sample", "node-sample", "mixed-sample")
$itemsToCopy = @(
  "bootstrap.py",
  "cli.py",
  "requirements.txt",
  "config.yaml.example",
  # Keep only minimal docs needed for operation (templates include command shorthand + conventions).
  "templates",
  "tools"
)

Write-Host "Repo root: $repoRoot"

foreach ($p in $projects) {
  $projRoot = Join-Path $PSScriptRoot $p
  Assert-PathExists $projRoot "Missing test project"

  Write-Host "`n=== $p ==="

  if ($Clean) {
    if (Test-Path (Join-Path $projRoot ".orchestration")) {
      Remove-Item (Join-Path $projRoot ".orchestration") -Recurse -Force
    }
    if (Test-Path (Join-Path $projRoot "orchestration-framework")) {
      Remove-Item (Join-Path $projRoot "orchestration-framework") -Recurse -Force
    }
    if (Test-Path (Join-Path $projRoot ".cursor")) {
      Remove-Item (Join-Path $projRoot ".cursor") -Recurse -Force
    }
    if (Test-Path (Join-Path $projRoot ".gitignore")) {
      Remove-Item (Join-Path $projRoot ".gitignore") -Force
    }
    if (Test-Path (Join-Path $projRoot "CONTRIBUTING.md")) {
      Remove-Item (Join-Path $projRoot "CONTRIBUTING.md") -Force
    }
  }

  # NOTE: We intentionally do NOT initialize nested git repos inside testing-workspace.
  # Nested `.git/` folders cause the framework repo to treat these as submodules and break `git add`.

  # Copy framework into project
  New-Item -ItemType Directory -Force (Join-Path $projRoot "orchestration-framework") | Out-Null
  foreach ($item in $itemsToCopy) {
    $src = Join-Path $repoRoot $item
    if (Test-Path $src) {
      Copy-Item -Recurse -Force $src (Join-Path $projRoot "orchestration-framework")
    }
  }

  # Run bootstrap
  Push-Location $projRoot
  try {
    $noCursor = $true
    if ($p -eq "python-sample") { $noCursor = $false }  # exercise cursor rules generation in one project
    if ($noCursor) {
      python .\orchestration-framework\bootstrap.py --init --project-name $p --trunk-branch main --no-cursor
    } else {
      python .\orchestration-framework\bootstrap.py --init --project-name $p --trunk-branch main
    }
    if ($LASTEXITCODE -ne 0) { throw "bootstrap.py exited non-zero for $p" }
  } finally {
    Pop-Location
  }

  # Patch in minimal Cursor CLI config so launch_agents(dry-run) can run even when Cursor isn't installed here.
  # (launch_agents requires cursor.enabled + cursor.agent_command to be present, but dry-run won't execute agent.)
  $cfgPath = Join-Path $projRoot ".orchestration\\config\\framework.yaml"
  Assert-PathExists $cfgPath "Missing config.yaml to patch for tests"
  $cfg = Get-Content $cfgPath -Raw
  if ($cfg -notmatch "(?m)^cursor:\\s*$") {
    Add-Content -Path $cfgPath -Value "`ncursor:`n  enabled: true`n  agent_command: agent`n  agent_runner_prefix: []`n  agent_output_format: text`n  agent_max_parallel: 3`n"
  } elseif ($cfg -notmatch "(?m)^\\s+agent_command:") {
    Add-Content -Path $cfgPath -Value "`n  agent_command: agent`n  agent_runner_prefix: []`n  agent_output_format: text`n  agent_max_parallel: 3`n"
  }

  # Verify expected outputs
  Assert-PathExists (Join-Path $projRoot ".orchestration\\runtime\\agent-sync\\COMMAND_SHORTHAND.md") "Missing COMMAND_SHORTHAND.md"
  Assert-PathExists (Join-Path $projRoot ".orchestration\\runtime\\agent-sync\\COMMUNICATION_CONVENTIONS.md") "Missing COMMUNICATION_CONVENTIONS.md"
  Assert-PathExists (Join-Path $projRoot ".orchestration\\runtime\\iterations") "Missing iterations runtime dir"
  Assert-PathExists (Join-Path $projRoot ".orchestration\\config\\workflows\\example-workflow.yaml") "Missing example workflow"
  Assert-PathExists (Join-Path $projRoot ".orchestration\\config\\framework.yaml") "Missing framework.yaml"
  Assert-PathExists (Join-Path $projRoot ".gitignore") "Missing .gitignore"
  Assert-PathExists (Join-Path $projRoot "CONTRIBUTING.md") "Missing CONTRIBUTING.md"

  if ($p -eq "python-sample") {
    Assert-PathExists (Join-Path $projRoot ".cursor\\agent.md") "Missing .cursor/agent.md"
    Assert-PathExists (Join-Path $projRoot ".cursor\\rules\\00-orchestration.mdc") "Missing cursor rule 00-orchestration.mdc"
  }

  # Smoke orchestration flow (non-destructive)
  Push-Location $projRoot
  try {
    python .\orchestration-framework\cli.py list | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "cli.py list failed for $p" }

    # New: ingestion + role derivation (safe generators)
    if ($p -eq "python-sample") {
      python .\orchestration-framework\cli.py execute "/orchestrator::ingest_project" | Out-Null
      if ($LASTEXITCODE -ne 0) { throw "ingest_project failed for $p" }
      python .\orchestration-framework\cli.py execute "/orchestrator::derive_roles" | Out-Null
      if ($LASTEXITCODE -ne 0) { throw "derive_roles failed for $p" }
      Assert-PathExists (Join-Path $projRoot ".orchestration\\config\\project_profile.yaml") "Missing project_profile.yaml"
      Assert-PathExists (Join-Path $projRoot ".orchestration\\config\\PROJECT_CONTEXT.md") "Missing PROJECT_CONTEXT.md"
      Assert-PathExists (Join-Path $projRoot ".orchestration\\config\\derived_roles.yaml") "Missing derived_roles.yaml"
      Assert-PathExists (Join-Path $projRoot ".cursor\\rules\\30-derived-roles.mdc") "Missing derived roles cursor rule"
    }

    python .\orchestration-framework\cli.py execute "/orchestrator::start_workflow(example-workflow, phase-1, iteration-1)" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "start_workflow failed for $p" }

    python .\orchestration-framework\cli.py execute "/orchestrator::launch_agents(iteration-1, parallel, 3, dry-run)" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "launch_agents dry-run failed for $p" }

    python .\orchestration-framework\cli.py execute "/integrator::apply_ready(dry-run)" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "apply_ready dry-run failed for $p" }
  } finally {
    Pop-Location
  }

  Write-Host "OK bootstrap outputs verified for $p"
}

Write-Host "`nAll bootstrap tests passed."

