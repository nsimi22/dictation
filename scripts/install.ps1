# One-command installer for free-dictation (Windows, PowerShell).
#
# From a checkout:
#   .\scripts\install.ps1
#
# Or straight from GitHub:
#   irm https://raw.githubusercontent.com/nsimi22/dictation/main/scripts/install.ps1 | iex
#
# Installs the app into an isolated environment with pipx and puts the
# `dictate` and `dictate-gui` commands on your PATH. Re-running upgrades it.
#
# Override the source repo (e.g. SSH for a private repo) with:
#   $env:DICTATION_REPO = "git@github.com:nsimi22/dictation.git"

$ErrorActionPreference = "Stop"

$Repo = if ($env:DICTATION_REPO) { $env:DICTATION_REPO } else { "https://github.com/nsimi22/dictation.git" }

# Find a Python launcher.
$py = $null
foreach ($candidate in @("python", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) { $py = $candidate; break }
}
if (-not $py) {
    Write-Error "Python not found. Install Python 3.9+ from https://www.python.org/downloads/ and tick 'Add python.exe to PATH'."
}

# Ensure pipx (driven via `python -m pipx` so we don't rely on PATH updates).
& $py -m pipx --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing pipx..."
    & $py -m pip install --user pipx
    & $py -m pipx ensurepath
}

Write-Host "Installing free-dictation from $Repo ..."
& $py -m pipx install --force "git+$Repo"

Write-Host ""
Write-Host "Done! Open a new terminal (pipx just updated your PATH), then run:"
Write-Host "    dictate-gui      # desktop window for settings + start/stop"
Write-Host "    dictate          # command-line version"
