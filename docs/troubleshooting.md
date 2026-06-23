# Troubleshooting

## `No` was selected for `PROXY_MANAGED`

Symptom:

```text
ANTHROPIC_API_KEY: sk-ant-...PROXY_MANAGED
Do you want to use this API key?
```

If `No` is selected, Claude Code stores `PROXY_MANAGED` in the rejected API key responses. `claude-codex` can then exit immediately or fail before reaching the proxy.

Fix:

```bash
./scripts/approve-proxy-managed.py
```

## `claude-codex` retries forever

Check:

```bash
lsof -nP -iTCP:15721 -sTCP:LISTEN
sqlite3 ~/.cc-switch/cc-switch.db "select app_type,id,is_current from providers where app_type='claude' order by id;"
jq '{currentProviderClaude,currentProviderCodex,enableLocalProxy}' ~/.cc-switch/settings.json
```

Expected:

- Proxy listening on `127.0.0.1:15721`
- Claude provider `codex-oauth` is current
- `enableLocalProxy` is `true`

## 401 from Codex OAuth through proxy

The Codex provider metadata may be missing the managed account auth binding.

Check provider meta:

```bash
sqlite3 ~/.cc-switch/cc-switch.db \
  "select id,provider_type,meta from providers where app_type='claude' and id='codex-oauth';"
```

Expected fields include:

- `providerType: codex_oauth`
- `apiFormat: openai_responses`
- `authBinding.source: managed_account`
- `authBinding.authProvider: codex_oauth`
- `authBinding.accountId`
- `codexFastMode: false`

## Claude startup feels frozen

When launched from `~`, Claude Code can scan a very large home directory. Start from a smaller project directory:

```bash
cd ~/tasks/fusion-feature
claude-codex
```

## Auth conflict

Symptom:

```text
Auth conflict: Both a token (claude.ai) and an API key (ANTHROPIC_API_KEY) are set.
```

For `claude-codex`, `ANTHROPIC_API_KEY=PROXY_MANAGED` is expected because it routes to the local proxy. For plain `claude`, avoid exporting `ANTHROPIC_API_KEY` globally in shell startup files.

