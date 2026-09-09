#!/bin/bash
# Outbound allowlist for the grading sandbox. Requires --cap-add NET_ADMIN.
#
# ALLOW_ENDPOINTS is a comma-separated list of host:port pairs, not bare hosts. A bare
# host would open every service on the grading machine to the student's specification,
# including the model server's management API, which can read the secret seeds and
# overwrite the pinned slot models.
#
# DNS is allowed only to the resolvers this container was configured with. Allowing
# udp/53 to any destination is a tunnel straight through the allowlist.
#
# IPv6 is dropped entirely: the allowlist is expressed in IPv4 and an unfiltered v6
# path would bypass all of it.
set -euo pipefail

flush_v4() { iptables -F OUTPUT; iptables -P OUTPUT DROP; }

flush_v4
iptables -A OUTPUT -o lo -j ACCEPT
iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# DNS, only to this container's own resolvers.
resolvers=$(awk '/^nameserver/{print $2}' /etc/resolv.conf | sort -u)
for r in $resolvers; do
  case "$r" in
    *:*) continue ;;                       # v6 resolver: v6 is dropped below anyway
  esac
  iptables -A OUTPUT -d "$r" -p udp --dport 53 -j ACCEPT
  iptables -A OUTPUT -d "$r" -p tcp --dport 53 -j ACCEPT
  echo "allow dns -> $r"
done

# The task's endpoints, host and port together.
IFS=',' read -ra ENDPOINTS <<< "${ALLOW_ENDPOINTS:-}"
for e in "${ENDPOINTS[@]}"; do
  [ -z "$e" ] && continue
  host="${e%:*}"; port="${e##*:}"
  if [ "$host" = "$e" ] || [ -z "$port" ]; then
    echo "refusing to open every port on '$e': ALLOW_ENDPOINTS entries must be host:port" >&2
    exit 1
  fi
  found=0
  for ip in $(getent ahostsv4 "$host" | awk '{print $1}' | sort -u); do
    iptables -A OUTPUT -d "$ip" -p tcp --dport "$port" -j ACCEPT
    echo "allow $host:$port -> $ip"
    found=1
  done
  [ "$found" = 1 ] || echo "warning: $host did not resolve to an IPv4 address" >&2
done

# No IPv6 at all.
if command -v ip6tables >/dev/null 2>&1; then
  ip6tables -F OUTPUT 2>/dev/null || true
  ip6tables -P OUTPUT DROP 2>/dev/null || true
  ip6tables -A OUTPUT -o lo -j ACCEPT 2>/dev/null || true
  echo "ipv6: dropped"
fi

echo "firewall: outbound restricted to ${ALLOW_ENDPOINTS:-nothing}"
