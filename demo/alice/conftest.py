import os
import sys

# make `src/` importable when running the suite from the repo root
sys.path.insert(0, os.path.dirname(__file__))

# The integration suite runs through the project's buildcache client (see CONTRIBUTING.md);
# it only exists after a proper bootstrap.
from buildcache.cache_client import cache_client  # noqa: E402, F401

cache_client.warm("checkout-service")
