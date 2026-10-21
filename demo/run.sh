#!/usr/bin/env bash
# Host driver: start Bob's container (attacker infrastructure, its own host on the network) and the
# demo container (desktop + pi + recorder + computer-use operator + validation). Artifacts land in
# $OUT.
#
# Bob runs as a SEPARATE container with the network alias `deps.buildcache.dev`, so the victim
# resolves it to a routable docker-network IP — a realistic external host, not a loopback tell.
# FORGED=0 serves the clean guide — the control arm (identical everything, no forged line).
#
# Watch it live while it runs at http://localhost:6080/vnc.html (noVNC).
set -euo pipefail

OUT="${1:-/tmp/compaction-demo-out}"
mkdir -p "$OUT"
: "${OPENAI_API_KEY:?set OPENAI_API_KEY (pi)}"
: "${ANTHROPIC_API_KEY:?set ANTHROPIC_API_KEY (operator)}"
# trust pre-seed: skip the project-trust prompt so the operator never has to click it
TRUST_SEED='{"/home/computeruse/alice": true}'

NET=cdemo-net
docker network create "$NET" >/dev/null 2>&1 || true

docker rm -f cbob cdemo >/dev/null 2>&1 || true

# Bob: attacker infrastructure, root-only files, port 80, alias = the trusted domain
# (entrypoint override: skip the desktop stack — this container is just the web server)
docker run -d --name cbob --network "$NET" --network-alias deps.buildcache.dev \
  -e FORGED="${FORGED:-1}" -u root --entrypoint python3 \
  compaction-demo /opt/bob/server.py >/dev/null

# Alice's machine: the desktop + pi victim
docker run -d --name cdemo --network "$NET" \
  -e OPENAI_API_KEY -e ANTHROPIC_API_KEY -e WIDTH=1280 -e HEIGHT=800 \
  -p 6080:6080 -p 5900:5900 \
  -v "$OUT":/out \
  compaction-demo >/dev/null

echo "[run] containers started; watch live at http://localhost:6080/vnc.html"
for _ in $(seq 1 60); do
  if docker exec -e DISPLAY=:1 cdemo xdotool getdisplaygeometry >/dev/null 2>&1; then
    echo "[run] desktop up ($(docker exec -e DISPLAY=:1 cdemo xdotool getdisplaygeometry | tr '\n' 'x'))"
    break
  fi
  sleep 1
done

# skip pi's project-trust prompt (deterministic startup for the operator)
docker exec cdemo bash -c "mkdir -p ~/.pi/agent && printf '%s' '$TRUST_SEED' > ~/.pi/agent/trust.json"

# Bob's server must be reachable from Alice's machine by its domain name
docker exec cdemo curl -fsS -o /dev/null http://deps.buildcache.dev/setup-guide

docker exec -e DISPLAY=:1 -e OPENAI_API_KEY -e ANTHROPIC_API_KEY -e PI_MODEL="${PI_MODEL:-gpt-5.6-luna}" \
  cdemo bash -lc 'cd ~ && python3 orchestrate.py'
code=$?
echo "[run] orchestrate exit=$code — artifacts in $OUT"
exit $code
