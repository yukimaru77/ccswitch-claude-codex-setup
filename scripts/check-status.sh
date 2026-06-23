#!/usr/bin/env bash
set -euo pipefail

echo "== claude =="
echo "PATH claude: $(command -v claude || true)"
echo "local claude: ${HOME}/.local/bin/claude"
"${HOME}/.local/bin/claude" --version || true
ls -l "${HOME}/.local/bin/claude" || true

echo
echo "== wrapper commands =="
for cmd in claude-codex claude-glm ccswitch-claude-run; do
  command -v "$cmd" || true
  ls -l "${HOME}/.local/bin/${cmd}" 2>/dev/null || true
done

echo
echo "== cc-switch proxy =="
lsof -nP -iTCP:15721 -sTCP:LISTEN || true
launchctl print "gui/$(id -u)/com.local.ccswitch-proxy" 2>/dev/null | sed -n '1,80p' || true

echo
echo "== cc-switch providers =="
if [ -f "${HOME}/.cc-switch/cc-switch.db" ]; then
  sqlite3 "${HOME}/.cc-switch/cc-switch.db" \
    "select app_type,id,name,provider_type,category,is_current,sort_index from providers order by app_type,sort_index,id;"
else
  echo "not found: ${HOME}/.cc-switch/cc-switch.db"
fi

echo
echo "== cc-switch settings =="
if [ -f "${HOME}/.cc-switch/settings.json" ]; then
  jq '{enableLocalProxy,currentProviderClaude,currentProviderCodex}' "${HOME}/.cc-switch/settings.json"
else
  echo "not found: ${HOME}/.cc-switch/settings.json"
fi

echo
echo "== PROXY_MANAGED approval =="
if [ -f "${HOME}/.claude.json" ]; then
  jq '{customApiKeyResponses}' "${HOME}/.claude.json"
else
  echo "not found: ${HOME}/.claude.json"
fi
