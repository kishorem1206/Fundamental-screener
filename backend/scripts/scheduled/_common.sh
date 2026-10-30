# Shared by the launchd jobs: move to the backend and make sure the database is up.
export PATH=/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin
cd "$(dirname "$0")/../.." || exit 1
PY=.venv/bin/python
echo "=== $(date '+%Y-%m-%d %H:%M:%S') $JOB start"
if ! nc -z localhost 5434 2>/dev/null; then
  open -a Docker
  for _ in $(seq 1 40); do docker info >/dev/null 2>&1 && break; sleep 3; done
  docker compose -p containers -f ../containers/docker-compose.yml up -d
  for _ in $(seq 1 30); do nc -z localhost 5434 2>/dev/null && break; sleep 2; done
fi
if ! nc -z localhost 5434 2>/dev/null; then
  echo "=== $(date '+%Y-%m-%d %H:%M:%S') $JOB stopped: database not reachable"
  exit 1
fi
