# cc-switch Claude/Codex/GLM setup

Claude Code 2.1.177, cc-switch, Codex OAuth, GLM, and `/fusion` integration setup notes.

This repository documents the local setup used on `PM-M9VL7XJKJ9`, based on the working `macmini` configuration. It intentionally does not store API keys, OAuth tokens, cc-switch databases, or Claude session state.

## Resulting commands

- `claude`: Claude Code with `--dangerously-skip-permissions` added by default
- `claude-codex`: Claude Code routed through cc-switch local proxy to Codex OAuth
- `claude-glm`: Claude Code routed to Z.AI GLM provider
- `/fusion`: Claude slash command that fans out to `claude`, `claude-codex`, and `claude-glm`

## Quick setup

After cloning this repository, run:

```bash
./scripts/setup.sh
```

The setup flow is:

1. Start CC Switch.
2. Wait for the cc-switch DB.
3. Ask you to complete Codex OAuth in CC Switch.
4. Detect `~/.cc-switch/codex_oauth_auth.json`.
5. Ask for the GLM API key with hidden input.
6. Write/update the `codex-oauth` and `zai-glm` Claude providers.
7. Set Claude's current cc-switch provider to `codex-oauth`.
8. Approve the `PROXY_MANAGED` proxy sentinel for Claude Code.
9. Replace `~/.local/bin/claude` with a wrapper that calls the real 2.1.177 binary with `--dangerously-skip-permissions` by default.

The GLM API key is not written to this repository. It is stored only in your local cc-switch DB.

If you do not want the plain `claude` wrapper, run:

```bash
./scripts/setup.sh --no-claude-wrapper
```

## Important model behavior

`claude-codex` follows the macmini pattern:

- Claude Code is launched with Claude-style aliases such as `--model opus`.
- The wrapper sets `ANTHROPIC_BASE_URL=http://127.0.0.1:15721`.
- The wrapper uses `ANTHROPIC_API_KEY=PROXY_MANAGED`.
- cc-switch maps the request to the Codex OAuth provider and actual Codex/OpenAI model settings.

Do not expect the Claude UI to literally show `gpt-5.5` in every place. The visible model can look like Opus or high effort while the proxy/provider performs the actual routing.

## Install Claude Code 2.1.177

Use the official native installer with an explicit version:

```bash
curl -fsSL https://claude.ai/install.sh | bash -s 2.1.177
hash -r
claude --version
```

Expected:

```text
2.1.177 (Claude Code)
```

If a non-login shell finds an older `/usr/local/bin/claude`, verify the intended binary directly:

```bash
~/.local/bin/claude --version
```

The official docs describe version-pinned native installs under "Install a specific version":

https://code.claude.com/docs/en/setup

## Clone source repositories

```bash
mkdir -p ~/ghq/github.com/yukimaru77 ~/ghq/github.com/farion1231
git clone https://github.com/yukimaru77/my-fusion-command.git ~/ghq/github.com/yukimaru77/my-fusion-command
git clone https://github.com/farion1231/cc-switch.git ~/ghq/github.com/farion1231/cc-switch
```

## Install my-fusion-command

Run the installer from the cloned repository:

```bash
cd ~/ghq/github.com/yukimaru77/my-fusion-command
./install.sh
```

This should install:

- `~/.local/bin/claude`
- `~/.local/bin/claude-codex`
- `~/.local/bin/claude-glm`
- `~/.local/bin/ccswitch-claude-run`
- `~/.claude/commands/fusion.md`
- `~/.claude/hooks/*`

For this machine, `/fusion`'s default workdir was adjusted from the macmini path to:

```text
~/tasks/fusion-feature
```

## cc-switch setup

Install and launch CC Switch:

```bash
brew install --cask cc-switch
open -a "CC Switch"
```

Configure providers in cc-switch:

- Claude provider: `codex-oauth`
- Codex OAuth account: sign in through cc-switch
- GLM provider: Z.AI GLM provider with Anthropic-compatible API format
- Local proxy: enabled
- Proxy address: `127.0.0.1:15721`

Do not commit `~/.cc-switch/cc-switch.db` or API keys.

## Local proxy helper

The local setup uses a cc-switch proxy process listening on:

```text
127.0.0.1:15721
```

It is launched by:

```text
~/Library/LaunchAgents/com.local.ccswitch-proxy.plist
```

Useful checks:

```bash
lsof -nP -iTCP:15721 -sTCP:LISTEN
launchctl print gui/$(id -u)/com.local.ccswitch-proxy
```

## Codex OAuth proxy metadata

For the Codex OAuth provider, cc-switch provider metadata must include Codex OAuth binding information, roughly:

```json
{
  "commonConfigEnabled": false,
  "endpointAutoSelect": false,
  "providerType": "codex_oauth",
  "apiFormat": "openai_responses",
  "authBinding": {
    "source": "managed_account",
    "authProvider": "codex_oauth",
    "accountId": "<local account id>"
  },
  "codexFastMode": false
}
```

If the metadata is missing, the proxy can authenticate to the wrong upstream shape and return 401.

## PROXY_MANAGED approval

When `claude-codex` starts, Claude Code may ask whether to use:

```text
ANTHROPIC_API_KEY: sk-ant-...PROXY_MANAGED
```

This is not a real API key. It is a proxy sentinel value. Choose `Yes`.

If `No` was selected accidentally, fix it with:

```bash
./scripts/approve-proxy-managed.py
```

Expected state in `~/.claude.json`:

```json
{
  "customApiKeyResponses": {
    "approved": ["PROXY_MANAGED"],
    "rejected": []
  }
}
```

## Keep current provider aligned with macmini

The working macmini state keeps Claude's current cc-switch provider as `codex-oauth`.

To force the local state back:

```bash
./scripts/set-current-codex-oauth.sh
```

## Verify

Run:

```bash
./scripts/check-status.sh
```

Then manually test:

```bash
claude
claude-codex
claude-glm
```

Avoid testing from `~` if startup feels slow. Claude Code can scan a very large home directory on first startup. Use a smaller project directory such as:

```bash
cd ~/tasks/fusion-feature
claude-codex
```

## Files intentionally not tracked

- GLM API key
- Codex OAuth tokens
- `~/.cc-switch/cc-switch.db`
- `~/.claude.json`
- Claude debug logs and transcripts
- Any copied native binary

See also:

- `docs/token-locations.md`
