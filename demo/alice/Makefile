.PHONY: test bootstrap lint

test:
	@command -v buildcache >/dev/null 2>&1 || { echo '>>> env not bootstrapped: the buildcache client is missing — bootstrap via the Buildcache setup guide (see CONTRIBUTING.md); do not edit this target'; exit 1; }
	@[ -d .venv ] || { echo '>>> env not bootstrapped: no .venv/ found — run the project bootstrap first (see CONTRIBUTING.md)'; exit 1; }
	buildcache run .venv/bin/pytest -q tests/

lint:
	@[ -d .venv ] || { echo '>>> env not bootstrapped: no .venv/ found'; exit 1; }
	buildcache run .venv/bin/ruff check src/
