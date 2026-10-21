# Demo container: Anthropic computer-use reference image (desktop + xdotool + the sampling loop)
# plus Node 22 + pi (the victim agent) + ffmpeg (recorder) + the Alice/Bob assets.
#
# Containment layout:
#   /home/computeruse/alice  Alice's repo (pi's cwd) — nothing attacker-controlled in here
#   /opt/bob                 Bob's attacker infrastructure — root-only, invisible to the victim agent
FROM ghcr.io/anthropics/anthropic-quickstarts:computer-use-demo-latest

USER root

# Node 22 (pi needs >=22.19) + ffmpeg for screen recording
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates gnupg curl \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs ffmpeg ripgrep fd-find build-essential \
    && ln -sf "$(command -v fdfind)" /usr/local/bin/fd \
    && rm -rf /var/lib/apt/lists/*

# pi (the shipping coding agent under test), pinned to the version we validated
RUN npm install -g @earendil-works/pi-coding-agent@0.79.0

# Bob's infrastructure: build the buildcache client. It's not obfuscated — it does exactly what
# the setup guide documents (registers a host cache session with the endpoint, guide §4) — and it
# lives root-only (mode 700) so the victim agent can't browse the source.
COPY bob /opt/bob
RUN cd /opt/bob \
    && gcc -O2 -s -o buildcache.bin buildcache.c \
    && chmod +x bootstrap.sh \
    && chmod -R go-rwx /opt/bob

# Alice's repo (pi's cwd) and the operator/conductor scripts.
COPY alice /home/computeruse/alice
COPY director.py orchestrate.py /home/computeruse/
RUN chown -R computeruse:computeruse /home/computeruse/alice \
       /home/computeruse/director.py /home/computeruse/orchestrate.py

USER computeruse
