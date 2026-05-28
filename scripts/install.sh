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
#   DICTATION_REPO=ssh://git@github.com/nsimi22/dictation.git ./scripts/install.sh   # SSH (private repos)
#   PYTHON=python3.11 ./scripts/install.sh                                            # pick a Python
set -euo pipefail

REPO_URL="${DICTATION_REPO:-https://github.com/nsimi22/dictation.git}"
PY="${PYTHON:-python3}"

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Error: '$PY' not found. Install Python 3.9+ first: https://www.python.org/downloads/" >&2
  exit 1
fi

# Bootstrap pipx if it isn't already installed. Modern macOS (Homebrew) and
# Linux ship "externally managed" Pythons that reject `pip install --user`
# (PEP 668), so we prefer Homebrew and fall back to allowing the user install.
bootstrap_pipx() {
  if command -v brew >/dev/null 2>&1; then
    echo "Installing pipx via Homebrew..."
    brew install pipx && return 0
  fi
  echo "Installing pipx..."
  if "$PY" -m pip install --user --quiet pipx; then
    return 0
  fi
  # Retry for PEP 668 "externally-managed-environment" Pythons.
  "$PY" -m pip install --user --quiet --break-system-packages pipx
}

# Drive pipx via `python -m` after a fresh install so we don't depend on PATH
# changes (from `ensurepath`) taking effect in this same shell.
if command -v pipx >/dev/null 2>&1; then
  PIPX=(pipx)
else
  bootstrap_pipx
  "$PY" -m pipx ensurepath || true
  PIPX=("$PY" -m pipx)
fi

# Accept either a bare repo URL (we add the pip "git+" prefix) or a full
# pip VCS spec that already has it.
case "$REPO_URL" in
  git+*) SPEC="$REPO_URL" ;;
  *)     SPEC="git+${REPO_URL}" ;;
esac

echo "Installing free-dictation from ${REPO_URL} ..."
"${PIPX[@]}" install --force "$SPEC"

cat <<'EOF'

Done! If the commands aren't found, open a new terminal (pipx just updated
your PATH), then run:

    dictate-gui      # desktop window for settings + start/stop
    dictate          # command-line version

macOS: the first run will prompt for Microphone and Accessibility permission.
Grant both (System Settings -> Privacy & Security) and restart your terminal.
EOF
