#!/usr/bin/env bash
#
# One-command installer for free-dictation (macOS / Linux).
#
# From a checkout:
#   ./scripts/install.sh
#
# Or straight from GitHub:
#   curl -fsSL https://raw.githubusercontent.com/nsimi22/dictation/main/scripts/install.sh | bash
#
# Installs the app into an isolated environment with pipx and puts the
# `dictate` and `dictate-gui` commands on your PATH. Re-running upgrades it.
#
# Overrides:
#   DICTATION_REPO=git@github.com:nsimi22/dictation.git ./scripts/install.sh   # SSH (private repos)
#   PYTHON=python3.11 ./scripts/install.sh                                     # pick a Python
set -euo pipefail

REPO_URL="${DICTATION_REPO:-https://github.com/nsimi22/dictation.git}"
PY="${PYTHON:-python3}"

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Error: '$PY' not found. Install Python 3.9+ first: https://www.python.org/downloads/" >&2
  exit 1
fi

# Ensure pipx is available. If we have to install it, drive it via `python -m`
# so we don't depend on PATH changes taking effect in this same shell.
if command -v pipx >/dev/null 2>&1; then
  PIPX=(pipx)
else
  echo "Installing pipx..."
  "$PY" -m pip install --user --quiet pipx
  "$PY" -m pipx ensurepath
  PIPX=("$PY" -m pipx)
fi

echo "Installing free-dictation from ${REPO_URL} ..."
"${PIPX[@]}" install --force "git+${REPO_URL}"

cat <<'EOF'

Done! If the commands aren't found, open a new terminal (pipx just updated
your PATH), then run:

    dictate-gui      # desktop window for settings + start/stop
    dictate          # command-line version

macOS: the first run will prompt for Microphone and Accessibility permission.
Grant both (System Settings -> Privacy & Security) and restart your terminal.
EOF
