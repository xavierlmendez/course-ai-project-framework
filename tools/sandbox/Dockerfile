# Sandbox for regenerations and hidden-test runs.
# Contains: python3, the OpenCode harness, curl (so the harness can sign the ledger),
# iptables (outbound allowlist). No secrets, fresh /work per run.
FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv ca-certificates curl iptables iproute2 dnsutils git \
    && rm -rf /var/lib/apt/lists/* \
    && npm install -g opencode-ai@latest \
    && useradd -m -u 1001 -s /bin/bash runner
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
COPY init-firewall.sh /usr/local/bin/init-firewall.sh
RUN chmod +x /usr/local/bin/entrypoint.sh /usr/local/bin/init-firewall.sh
WORKDIR /work
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["regenerate"]
