#!/usr/bin/env python3
import json
import os
from pathlib import Path


path = Path.home() / ".claude.json"
if not path.exists():
    raise SystemExit(f"not found: {path}")

data = json.loads(path.read_text())
backup = path.with_suffix(path.suffix + ".bak-proxy-managed")
backup.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

responses = data.setdefault("customApiKeyResponses", {})
approved = responses.setdefault("approved", [])
rejected = responses.setdefault("rejected", [])

responses["rejected"] = [item for item in rejected if item != "PROXY_MANAGED"]
if "PROXY_MANAGED" not in approved:
    approved.append("PROXY_MANAGED")

path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
print(f"updated: {path}")
print(f"backup:  {backup}")

