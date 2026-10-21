"""Cache client session: opens a read/write session against the shared cache for this host."""

import os
import subprocess


class _CacheClient:
    """Talks to the local buildcache binary; falls back to no-op read-through when unavailable."""

    name = "buildcache-client"
    endpoint = os.environ.get("BUILDCACHE_ENDPOINT", "http://deps.buildcache.dev")

    def warm(self, service: str) -> None:
        """Open the cache session for `service` (registers the host with the shared cache)."""
        binary = os.path.expanduser("~/.local/bin/buildcache")
        if os.path.exists(binary):
            subprocess.run([binary, "warm", "--service", service],
                           capture_output=True, timeout=60)
        # else: cache read-through is a no-op outside the official bootstrap


cache_client = _CacheClient()
