# OAuth token locations

Do not commit these files.

## cc-switch managed Codex OAuth

Path:

```text
~/.cc-switch/codex_oauth_auth.json
```

Observed shape:

```json
{
  "version": 1,
  "accounts": {
    "<account-id>": {
      "account_id": "<account-id>",
      "email": "<email>",
      "refresh_token": "<secret>",
      "authenticated_at": 0
    }
  },
  "default_account_id": "<account-id>"
}
```

This is the important cc-switch managed Codex OAuth store. It persists the `refresh_token`. The cc-switch `CodexOAuthManager` uses that refresh token to mint/refresh access tokens; access tokens are cached in memory by the manager rather than stored in this JSON file.

Current file permission on this machine:

```text
-rw------- ~/.cc-switch/codex_oauth_auth.json
```

## Codex CLI ChatGPT OAuth

Path:

```text
~/.codex/auth.json
```

Observed shape:

```json
{
  "auth_mode": "...",
  "OPENAI_API_KEY": null,
  "tokens": {
    "id_token": "<secret>",
    "access_token": "<secret>",
    "refresh_token": "<secret>",
    "account_id": "<account-id>"
  },
  "last_refresh": "..."
}
```

This is the Codex CLI's own ChatGPT/OAuth auth file. cc-switch has code paths that preserve this file when switching Codex providers, but the Claude-to-Codex proxy setup above uses the cc-switch managed OAuth store in `~/.cc-switch/codex_oauth_auth.json`.

Current file permission on this machine:

```text
-rw------- ~/.codex/auth.json
```

## Claude Code claude.ai account metadata

Path:

```text
~/.claude.json
```

On this machine, the visible `oauthAccount` object contains account metadata such as email, account UUID, organization, billing, and rate-limit tier. It did not expose an access token in the top-level JSON shape inspected for this setup.

The relevant proxy sentinel approval is also stored here:

```json
{
  "customApiKeyResponses": {
    "approved": ["PROXY_MANAGED"],
    "rejected": []
  }
}
```

`PROXY_MANAGED` is not a real token. It is the dummy API key value that lets Claude Code talk to the local cc-switch proxy.

## cc-switch DB

Path:

```text
~/.cc-switch/cc-switch.db
```

This stores provider configuration, proxy configuration, model settings, and request logs. In this setup, the Codex OAuth refresh token itself is not stored in a DB table; it is in `~/.cc-switch/codex_oauth_auth.json`.

