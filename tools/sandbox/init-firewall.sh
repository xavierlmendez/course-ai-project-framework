#!/bin/bash
# Outbound allowlist: only the hosts in $ALLOW_HOSTS (comma-separated) plus loopback and DNS.
# Same pattern as the Claude Code devcontainer's init-firewall.sh. Requires --cap-add NET_ADMIN.
set -euo pipefail
iptables -F OUTPUT
iptables -P OUTPUT DROP
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT
IFS=',' read -ra HOSTS <<< "${ALLOW_HOSTS:-}"
for h in "${HOSTS[@]}"; do
  [ -z "$h" ] && continue
  for ip in $(getent ahostsv4 "$h" | awk '{print $1}' | sort -u); do
    iptables -A OUTPUT -d "$ip" -j ACCEPT
    echo "allow $h -> $ip"
  done
done
echo "firewall: outbound restricted to ${ALLOW_HOSTS:-nothing}"
