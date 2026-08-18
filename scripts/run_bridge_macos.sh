#!/bin/zsh
# ============================================================================
#  Claude SQL bridge — spousteni na macOS (ekvivalent NSSM sluzby z Windows)
#  Jirka (C28) + Claude, 10. 8. 2026.
#
#  Proc: claude_sql_runner.py je multiplatformni (jen stdlib, _git_exe() bere
#  "git" z PATH), ale jeho docstring popisuje jen instalaci pres NSSM. Na Macu
#  NSSM neni — ekvivalent je launchd. docs/team/Jirka28.md tenhle krok vedl
#  jako nedodelek („na Macu: ekvivalent — watcher pres python3 + launchd").
#
#  TOKEN: neni v tomhle skriptu ani v launchd plistu. Cte se z
#  ~/.strategie_deploy_token (chmod 600), takze secret zije na jednom miste,
#  neni v gitu a neni videt v `launchctl print`.
#
#  Kdyz token jeste neni, skript NESPADNE, ale ceka — jinak by ho launchd
#  s KeepAlive porad dokola restartoval. Jakmile soubor vznikne, most nabehne
#  sam (do 30 s).
#
#  Instalace jako sluzba (spousti se po prihlaseni):
#      cp scripts/cz.strategie.claude-sql.plist.template \
#         ~/Library/LaunchAgents/cz.strategie.claude-sql.plist
#      # v plistu nahradit __REPO__ absolutni cestou k repu
#      launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/cz.strategie.claude-sql.plist
#  Odinstalace:
#      launchctl bootout gui/$(id -u)/cz.strategie.claude-sql
#  Rucni spusteni (debug):  ./scripts/run_bridge_macos.sh
# ============================================================================

TOKEN_FILE="${STRATEGIE_TOKEN_FILE:-$HOME/.strategie_deploy_token}"

# Repo odvodime z umisteni skriptu — funguje at je klon kdekoliv.
SCRIPT_DIR="${0:A:h}"
REPO="${SCRIPT_DIR:h}"

if [[ ! -f "$REPO/scripts/claude_sql_runner.py" ]]; then
  echo "CHYBA: nenasel jsem $REPO/scripts/claude_sql_runner.py" >&2
  exit 1
fi

if [[ ! -f "$TOKEN_FILE" ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] cekam na $TOKEN_FILE — bez nej se most neautentizuje (hlavicka X-Deploy-Token)."
  echo "  Token vydava Marti (tyz, jaky ma cloud APP), nebo je na Windows stroji v konfiguraci sluzby STRATEGIE-CLAUDE-SQL."
  echo "  Pak:  printf '%s' '<token>' > $TOKEN_FILE && chmod 600 $TOKEN_FILE"
  while [[ ! -f "$TOKEN_FILE" ]]; do
    sleep 30
  done
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] token dorazil, startuji most."
fi

export STRATEGIE_DEPLOY_TOKEN="$(cat "$TOKEN_FILE")"
if [[ -z "$STRATEGIE_DEPLOY_TOKEN" ]]; then
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] CHYBA: $TOKEN_FILE je prazdny." >&2
  exit 1
fi

# ID instance: env, jinak scripts/claude_sql/INSTANCE_ID.txt (gitignored, per-stroj).
if [[ -z "$CLAUDE_INSTANCE_ID" && -f "$REPO/scripts/claude_sql/INSTANCE_ID.txt" ]]; then
  export CLAUDE_INSTANCE_ID="$(cat "$REPO/scripts/claude_sql/INSTANCE_ID.txt")"
fi

PY="${STRATEGIE_PYTHON:-/usr/bin/python3}"
cd "$REPO" || exit 1
exec "$PY" scripts/claude_sql_runner.py
