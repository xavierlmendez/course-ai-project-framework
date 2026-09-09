#!/bin/bash
# Modes:
#   regenerate   apply firewall, then run the harness as an unprivileged user on $PROMPT with $SLOT_MODEL
#   <anything>   run that command as the unprivileged user (used for python3 /tools/run_tests.py ...)
set -euo pipefail
if [ -n "${ALLOW_HOSTS:-}" ]; then
  /usr/local/bin/init-firewall.sh
fi
chown -R runner:runner /work 2>/dev/null || true
if [ "${1:-}" = "regenerate" ]; then
  export HOME=/home/runner
  exec su -s /bin/bash runner -c 'cd /work && exec opencode run -m "ollama/$SLOT_MODEL" --format json "$PROMPT"'
fi
exec su -s /bin/bash runner -c "cd /work && exec $(printf '%q ' "$@")"
