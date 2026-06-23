# cc-switch local proxy notes

This setup depends on cc-switch serving an Anthropic-compatible local proxy on:

```text
http://127.0.0.1:15721
```

## Local files used in this machine

The working local setup used:

```text
~/ghq/github.com/farion1231/cc-switch
~/Library/LaunchAgents/com.local.ccswitch-proxy.plist
~/.cc-switch/cc-switch.db
~/.cc-switch/settings.json
```

The LaunchAgent runs a local `cc-switch-proxy` helper built from the cc-switch repository:

```text
~/ghq/github.com/farion1231/cc-switch/src-tauri/target/debug/cc-switch-proxy
```

## Forwarder fallback fix

The local cc-switch repository has a small working-tree patch in:

```text
src-tauri/src/proxy/forwarder.rs
```

Purpose:

- When the forwarder is running without a Tauri `app_handle`, Codex OAuth token lookup can otherwise be unavailable.
- The fallback creates a `CodexOAuthManager` from cc-switch's app config directory.
- It retrieves the valid default Codex OAuth account/token.
- It injects the `chatgpt-account-id` header for the managed account.

Without this fallback, direct OAuth token checks can work while proxy-routed requests still return 401.

## Provider metadata that mattered

The `codex-oauth` Claude provider must have metadata equivalent to:

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

`accountId` is local account state and must not be committed.

## Runtime checks

```bash
lsof -nP -iTCP:15721 -sTCP:LISTEN
launchctl print gui/$(id -u)/com.local.ccswitch-proxy
tail -n 80 ~/.cc-switch/logs/cc-switch-proxy.launchd.err
tail -n 80 ~/.cc-switch/logs/cc-switch-proxy.launchd.log
```

Expected log line:

```text
CC Switch proxy listening on 127.0.0.1:15721
```

