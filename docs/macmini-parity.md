# macmini parity checklist

Use this checklist when rebuilding another machine from the working macmini setup.

## Claude Code

- Version is `2.1.177`.
- Installed by official native installer, not by copying the binary.
- `~/.local/bin/claude` points to `~/.local/share/claude/versions/2.1.177`.

## `~/.claude.json`

`PROXY_MANAGED` must be approved:

```json
{
  "customApiKeyResponses": {
    "approved": ["PROXY_MANAGED"],
    "rejected": []
  }
}
```

## `~/.claude/settings.json`

Important shape:

```json
{
  "model": "claude-opus-4-6[1m]",
  "effortLevel": "xhigh",
  "autoUpdatesChannel": "stable",
  "env": {
    "HCOM": "hcom",
    "ANTHROPIC_MODEL": "claude-opus-4-6[1m]",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "claude-opus-4-6[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-opus-4-6[1m]",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "claude-opus-4-6[1m]"
  }
}
```

Do not copy macmini absolute paths directly. Replace:

```text
/Users/nonaka
```

with the local home directory.

## cc-switch

`~/.cc-switch/settings.json` important values:

```json
{
  "enableLocalProxy": true,
  "currentProviderClaude": "codex-oauth",
  "currentProviderCodex": "default"
}
```

Claude providers in `~/.cc-switch/cc-switch.db`:

```text
claude|claude-official|0
claude|codex-oauth|1
claude|default|0
claude|zai-glm|0
```

## Wrappers

Expected commands:

```text
~/.local/bin/claude-codex
~/.local/bin/claude-glm
~/.local/bin/ccswitch-claude-run
```

`claude-codex` and `claude-glm` are thin wrappers around `ccswitch-claude-run`.

## `/fusion`

Expected files:

```text
~/.claude/commands/fusion.md
~/.claude/hooks/fusion-run.py
~/.claude/hooks/capture-query.py
~/.claude/hooks/collect-transcript.py
```

Default agents:

```text
claude
claude-codex
claude-glm
```

