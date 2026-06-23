#!/usr/bin/env bash
set -euo pipefail

db_path="${HOME}/.cc-switch/cc-switch.db"
settings_path="${HOME}/.cc-switch/settings.json"

if [ ! -f "$db_path" ]; then
  echo "not found: $db_path" >&2
  exit 1
fi

sqlite3 "$db_path" <<'SQL'
UPDATE providers
SET is_current = CASE
  WHEN app_type='claude' AND id='codex-oauth' THEN 1
  WHEN app_type='claude' THEN 0
  ELSE is_current
END
WHERE app_type='claude';
SQL

if [ -f "$settings_path" ]; then
  tmp="$(mktemp)"
  jq '.currentProviderClaude="codex-oauth"' "$settings_path" > "$tmp"
  mv "$tmp" "$settings_path"
fi

sqlite3 "$db_path" "select app_type,id,is_current from providers where app_type='claude' order by id;"

