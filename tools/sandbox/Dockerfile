# Sandbox for regenerations and hidden-test runs.
# Contains: python3, the OpenCode harness, curl (so the harness can sign the ledger),
# iptables (outbound allowlist). No secrets, fresh /work per run.
FROM node:22-bookworm-slim

# Pinned deliberately. The harness version is part of what makes a grade reproducible:
# a release that starts sending its own sampling parameters would silently flatten the
# best-of-K temperature schedule, with no error and no visible symptom.
# Measured working: 1.18.29 (2026-09-08, docs/review/evidence/f65-temperature-path.md).
ARG OPENCODE_VERSION=1.18.29
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv ca-certificates curl iptables iproute2 dnsutils git \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g opencode-ai@${OPENCODE_VERSION} \
    && useradd -m -u 1001 -s /bin/bash runner
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY init-firewall.sh /usr/local/bin/init-firewall.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/init-firewall.sh
WORKDIR /work
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["regenerate"]
