"""Print non-secret facts about the Supabase settings CI received, to debug an empty search.

Shows the key's role (from its JWT claims), the project ref in SUPABASE_URL, and how many shared chunks
the key can see. Never prints the key or the full URL.
"""

import base64
import json
import os
from urllib.parse import urlparse

key = os.environ.get("SUPABASE_SERVICE_KEY", "").strip()
url = os.environ.get("SUPABASE_URL", "").strip()

role = "missing"
if key.startswith("eyJ") and key.count(".") == 2:
    payload = key.split(".")[1] + "=" * (-len(key.split(".")[1]) % 4)
    role = json.loads(base64.urlsafe_b64decode(payload)).get("role", "unknown")
elif key.startswith("sb_secret_"):
    role = "secret key (sb_secret_)"
elif key.startswith("sb_publishable_"):
    role = "publishable key (like anon)"
elif key:
    role = f"unrecognised format ({len(key)} chars)"
print(f"SUPABASE_SERVICE_KEY role: {role}")
if os.environ.get("SUPABASE_SERVICE_KEY", "") != key:
    print("  note: the secret has leading/trailing whitespace")
host = urlparse(url).hostname or ""
print(f"SUPABASE_URL project ref: {host.split('.')[0] if host else 'missing'}")

try:
    from rag import store

    n = store.client().table("documents").select("id", count="exact").eq("namespace", "public").limit(1).execute().count
    print(f"shared chunks visible: {n}")
except Exception as e:  # noqa: BLE001
    print(f"query failed: {type(e).__name__}: {str(e)[:200]}")
