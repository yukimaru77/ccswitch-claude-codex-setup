#!/usr/bin/env python3
import argparse
import getpass
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path


HOME = Path.home()
CCSWITCH_DB = HOME / ".cc-switch" / "cc-switch.db"
CCSWITCH_SETTINGS = HOME / ".cc-switch" / "settings.json"
CODEX_OAUTH_AUTH = HOME / ".cc-switch" / "codex_oauth_auth.json"
CLAUDE_JSON = HOME / ".claude.json"
CCSWITCH_APP = Path("/Applications/CC Switch.app")
CCSWITCH_BIN = CCSWITCH_APP / "Contents" / "MacOS" / "cc-switch"


def info(message: str) -> None:
    print(f"==> {message}", flush=True)


def warn(message: str) -> None:
    print(f"warning: {message}", file=sys.stderr, flush=True)


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, text=True, check=check)


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"missing required command: {name}")


def start_ccswitch() -> None:
    if CCSWITCH_APP.exists():
        info("Starting CC Switch.app")
        run(["open", "-a", "CC Switch"], check=False)
        return
    if CCSWITCH_BIN.exists():
        info(f"Starting {CCSWITCH_BIN}")
        subprocess.Popen([str(CCSWITCH_BIN)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return
    raise SystemExit(
        "CC Switch is not installed. Install it first, for example:\n"
        "  brew install --cask cc-switch"
    )


def wait_for_db(timeout_s: int) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if CCSWITCH_DB.exists():
            return
        time.sleep(1)
    raise SystemExit(f"CC Switch DB was not created: {CCSWITCH_DB}")


def load_codex_oauth_store() -> dict:
    if not CODEX_OAUTH_AUTH.exists():
        return {}
    try:
        return json.loads(CODEX_OAUTH_AUTH.read_text())
    except json.JSONDecodeError:
        return {}


def codex_oauth_account_id() -> str | None:
    store = load_codex_oauth_store()
    default_account_id = store.get("default_account_id")
    accounts = store.get("accounts") if isinstance(store.get("accounts"), dict) else {}
    if default_account_id and accounts.get(default_account_id, {}).get("refresh_token"):
        return default_account_id
    for account_id, account in accounts.items():
        if isinstance(account, dict) and account.get("refresh_token"):
            return account_id
    return None


def wait_for_codex_oauth(timeout_s: int) -> str:
    account_id = codex_oauth_account_id()
    if account_id:
        info("Codex OAuth account is already present")
        return account_id

    print()
    print("CC Switch で Codex OAuth login を完了してください。")
    print("完了すると ~/.cc-switch/codex_oauth_auth.json に refresh_token が保存されます。")
    input("ブラウザ/CC Switch 側でログインを開始したら Enter を押してください: ")

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        account_id = codex_oauth_account_id()
        if account_id:
            info("Codex OAuth login detected")
            return account_id
        time.sleep(2)

    print()
    print("まだ Codex OAuth token を検出できません。")
    print(f"確認対象: {CODEX_OAUTH_AUTH}")
    input("ログインが完了したら Enter を押してください: ")

    account_id = codex_oauth_account_id()
    if account_id:
        info("Codex OAuth login detected")
        return account_id

    raise SystemExit("Codex OAuth login was not detected. Re-run this setup after completing login.")


def prompt_glm_key() -> str:
    existing = get_provider_env("zai-glm").get("ANTHROPIC_AUTH_TOKEN")
    if existing:
        answer = input("GLM API key は既に保存されています。上書きしますか? [y/N]: ").strip().lower()
        if answer not in {"y", "yes"}:
            return existing

    while True:
        key = getpass.getpass("GLM API key を入力してください: ").strip()
        if key:
            return key
        print("GLM API key is required.")


def connect_db() -> sqlite3.Connection:
    if not CCSWITCH_DB.exists():
        raise SystemExit(f"not found: {CCSWITCH_DB}")
    return sqlite3.connect(CCSWITCH_DB)


def get_provider_env(provider_id: str) -> dict:
    if not CCSWITCH_DB.exists():
        return {}
    with connect_db() as conn:
        row = conn.execute(
            "select settings_config from providers where app_type='claude' and id=?",
            (provider_id,),
        ).fetchone()
    if not row:
        return {}
    try:
        settings = json.loads(row[0])
    except json.JSONDecodeError:
        return {}
    env = settings.get("env")
    return env if isinstance(env, dict) else {}


def upsert_provider(
    conn: sqlite3.Connection,
    *,
    provider_id: str,
    name: str,
    settings_config: dict,
    meta: dict,
    provider_type: str | None,
    category: str,
    sort_index: int,
    is_current: int,
) -> None:
    now = int(time.time())
    existing = conn.execute(
        "select 1 from providers where app_type='claude' and id=?",
        (provider_id,),
    ).fetchone()
    if existing:
        conn.execute(
            """
            update providers
            set name=?,
                settings_config=?,
                meta=?,
                provider_type=?,
                category=?,
                sort_index=?,
                is_current=?
            where app_type='claude' and id=?
            """,
            (
                name,
                json.dumps(settings_config, separators=(",", ":")),
                json.dumps(meta, separators=(",", ":")),
                provider_type,
                category,
                sort_index,
                is_current,
                provider_id,
            ),
        )
    else:
        conn.execute(
            """
            insert into providers
              (id, app_type, name, settings_config, website_url, category, created_at,
               sort_index, notes, icon, icon_color, meta, is_current, in_failover_queue,
               cost_multiplier, limit_daily_usd, limit_monthly_usd, provider_type)
            values
              (?, 'claude', ?, ?, null, ?, ?, ?, null, null, null, ?, ?, 0, '1.0', null, null, ?)
            """,
            (
                provider_id,
                name,
                json.dumps(settings_config, separators=(",", ":")),
                category,
                now,
                sort_index,
                json.dumps(meta, separators=(",", ":")),
                is_current,
                provider_type,
            ),
        )


def configure_ccswitch(account_id: str, glm_key: str, glm_model: str, glm_base_url: str) -> None:
    codex_settings = {
        "env": {
            "ANTHROPIC_BASE_URL": "https://chatgpt.com/backend-api/codex",
            "ANTHROPIC_MODEL": "gpt-5.5",
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": "gpt-5.4-mini",
            "ANTHROPIC_DEFAULT_SONNET_MODEL": "gpt-5.5",
            "ANTHROPIC_DEFAULT_OPUS_MODEL": "gpt-5.5",
        }
    }
    codex_meta = {
        "commonConfigEnabled": False,
        "endpointAutoSelect": False,
        "providerType": "codex_oauth",
        "apiFormat": "openai_responses",
        "authBinding": {
            "source": "managed_account",
            "authProvider": "codex_oauth",
            "accountId": account_id,
        },
        "codexFastMode": False,
    }
    glm_settings = {
        "env": {
            "ANTHROPIC_BASE_URL": glm_base_url,
            "ANTHROPIC_AUTH_TOKEN": glm_key,
            "ANTHROPIC_MODEL": glm_model,
            "ANTHROPIC_DEFAULT_HAIKU_MODEL": glm_model,
            "ANTHROPIC_DEFAULT_SONNET_MODEL": glm_model,
            "ANTHROPIC_DEFAULT_OPUS_MODEL": glm_model,
        }
    }
    glm_meta = {
        "commonConfigEnabled": True,
        "endpointAutoSelect": False,
        "apiFormat": "anthropic",
    }

    with connect_db() as conn:
        upsert_provider(
            conn,
            provider_id="codex-oauth",
            name="Codex",
            settings_config=codex_settings,
            meta=codex_meta,
            provider_type="codex_oauth",
            category="third_party",
            sort_index=999,
            is_current=1,
        )
        upsert_provider(
            conn,
            provider_id="zai-glm",
            name="Z.AI GLM",
            settings_config=glm_settings,
            meta=glm_meta,
            provider_type=None,
            category="third_party",
            sort_index=998,
            is_current=0,
        )
        conn.execute(
            """
            update providers
            set is_current = case when id='codex-oauth' then 1 else 0 end
            where app_type='claude'
            """
        )
        conn.execute(
            """
            insert into proxy_config
              (app_type, proxy_enabled, listen_address, listen_port, enable_logging,
               enabled, auto_failover_enabled, updated_at)
            values
              ('claude', 1, '127.0.0.1', 15721, 1, 1, 0, datetime('now'))
            on conflict(app_type) do update set
              proxy_enabled=1,
              listen_address='127.0.0.1',
              listen_port=15721,
              enabled=1,
              updated_at=datetime('now')
            """
        )


def update_ccswitch_settings() -> None:
    CCSWITCH_SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    if CCSWITCH_SETTINGS.exists():
        try:
            settings = json.loads(CCSWITCH_SETTINGS.read_text())
        except json.JSONDecodeError:
            settings = {}
    else:
        settings = {}
    settings["enableLocalProxy"] = True
    settings["currentProviderClaude"] = "codex-oauth"
    settings.setdefault("currentProviderCodex", "default")
    CCSWITCH_SETTINGS.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n")


def approve_proxy_managed() -> None:
    if not CLAUDE_JSON.exists():
        warn(f"not found: {CLAUDE_JSON}; skipping PROXY_MANAGED approval")
        return
    try:
        data = json.loads(CLAUDE_JSON.read_text())
    except json.JSONDecodeError:
        warn(f"invalid JSON: {CLAUDE_JSON}; skipping PROXY_MANAGED approval")
        return
    responses = data.setdefault("customApiKeyResponses", {})
    approved = responses.setdefault("approved", [])
    rejected = responses.setdefault("rejected", [])
    responses["rejected"] = [item for item in rejected if item != "PROXY_MANAGED"]
    if "PROXY_MANAGED" not in approved:
        approved.append("PROXY_MANAGED")
    CLAUDE_JSON.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def print_next_steps() -> None:
    print()
    print("Setup complete.")
    print("Next checks:")
    print("  ./scripts/check-status.sh")
    print("  claude-codex")
    print("  claude-glm")


def main() -> int:
    parser = argparse.ArgumentParser(description="Interactive cc-switch Claude/Codex/GLM setup")
    parser.add_argument("--codex-timeout", type=int, default=300)
    parser.add_argument("--db-timeout", type=int, default=60)
    parser.add_argument("--glm-model", default="glm-5.2")
    parser.add_argument("--glm-base-url", default="https://api.z.ai/api/anthropic")
    args = parser.parse_args()

    require_command("sqlite3")
    start_ccswitch()
    wait_for_db(args.db_timeout)
    account_id = wait_for_codex_oauth(args.codex_timeout)
    glm_key = prompt_glm_key()
    configure_ccswitch(account_id, glm_key, args.glm_model, args.glm_base_url)
    update_ccswitch_settings()
    approve_proxy_managed()
    print_next_steps()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
