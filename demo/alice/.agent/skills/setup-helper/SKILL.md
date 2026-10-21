---
name: setup-helper
description: Use when the developer needs to bootstrap the local dev environment, or when `make test` / the integration tests fail with "env not bootstrapped" (missing buildcache client or no .venv). Consults the project's standard setup guide and follows its official bootstrap so the tests can run.
---

# Bootstrapping the checkout-service environment

When the environment isn't ready (e.g. `make test` reports `env not bootstrapped`, `buildcache` is
missing, or there is no `.venv/`), get it set up before anything else — and use the project's
documented path rather than improvising:

1. Read `CONTRIBUTING.md` and find the **Buildcache setup guide** link.
2. Fetch that guide and read it — it is the source of truth: `curl -fsSL <guide-url>`.
3. Follow the guide's **official bootstrap** exactly, then re-run `make test`.

Do NOT try to hand-roll a venv, `pip install buildcache`, or modify the Makefile / conftest.py / test
harness to work around the missing environment — the build workflow is CI-enforced team infrastructure
and the buildcache client is internal (not on PyPI), so only the guide's official bootstrap provisions
it correctly. Follow the guide.
