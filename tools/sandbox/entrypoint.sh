#!/bin/bash
# Modes:
#   regenerate   apply the firewall, then run the harness as the unprivileged user
#   runtests     stage the hidden tests root-only and run the test runner, which drops
#                to the unprivileged user for the solution itself
#   <anything>   run that command as the unprivileged user
#
# The working directory is a bind mount. It is deliberately not chowned: changing
# ownership of a bind mount rewrites the host's files to a uid that may not exist there,
# after which the runner cannot delete its own working directory on resume.
set -euo pipefail

if [ -n "${ALLOW_ENDPOINTS:-}" ]; then
  /usr/local/bin/init-firewall.sh
fi

stage_tests() {
  # The tests arrive at /root/tests-src. /root is 0700 and root-owned, so the graded
  # user cannot traverse into the mount whatever permissions the host gave it, and a
  # read-only mount cannot be chmod-ed. Stage a root-only copy for the test runner.
  if [ -d /root/tests-src ]; then
    rm -rf /tests
    cp -a /root/tests-src /tests
    chown -R root:root /tests
    chmod -R go-rwx /tests
    chmod 700 /tests
  fi
  chmod 700 /root 2>/dev/null || true
}

case "${1:-}" in
  regenerate)
    # On a Linux host the bind mount keeps the host owner's uid, and `runner` (1001) cannot
    # write into it (measured on an AWS g5.xlarge, 2026-09-09: "unable to write to the file
    # system due to permission restrictions"). Docker Desktop on macOS maps ownership and
    # hides this. So `runner` adopts the host user's uid/gid for this run; files it writes
    # then belong to the host user. The mount itself is still never chowned.
    if [ -n "${HOST_UID:-}" ] && [ "$HOST_UID" != "0" ] && [ "$HOST_UID" != "$(id -u runner)" ]; then
      taken=$(getent passwd "$HOST_UID" | cut -d: -f1 || true)
      if [ -n "$taken" ] && [ "$taken" != "runner" ]; then usermod -u 60001 "$taken"; fi
      usermod -u "$HOST_UID" runner
      if [ -n "${HOST_GID:-}" ] && [ "$HOST_GID" != "0" ]; then
        if getent group "$HOST_GID" >/dev/null; then usermod -g "$HOST_GID" runner
        else groupmod -g "$HOST_GID" runner; fi
      fi
      chown -R runner /home/runner
    fi
    export HOME=/home/runner
    exec su -s /bin/bash runner -c 'cd /work && exec opencode run -m "ollama/$SLOT_MODEL" --format json "$PROMPT"'
    ;;
  runtests)
    shift
    stage_tests
    # Runs as root so it can read /tests; it executes each solution as `runner`.
    cd /work
    exec "$@"
    ;;
  *)
    exec su -s /bin/bash runner -c "cd /work && exec $(printf '%q ' "$@")"
    ;;
esac
