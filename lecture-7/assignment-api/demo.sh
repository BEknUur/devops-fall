#!/usr/bin/env bash
# Runs the acceptance sequence without restarting the API.
set -u
cd "$(dirname "$0")"
API=http://localhost:8000

check() {
  echo "== $1"
  for ep in /health/live /health/ready /db-time; do
    printf '  %-14s ' "$ep"
    curl -s -m 6 -o /tmp/body -w '%{http_code} (%{time_total}s) ' "$API$ep"; cat /tmp/body; echo
  done
}

wait_ready() {
  for _ in $(seq 30); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' "$API/health/ready")" = 200 ] && return
    sleep 1
  done
}

docker compose down -v >/dev/null 2>&1
docker compose up -d --build api
until curl -s "$API/health/live" >/dev/null; do sleep 0.5; done
check "1. API started, PostgreSQL stopped"

docker compose up -d db
wait_ready
check "2. PostgreSQL started, connections recovered"

docker compose stop db
check "3. PostgreSQL stopped again"

docker compose start db
wait_ready
check "4. PostgreSQL restarted, recovered"

echo "== 5. 20 concurrent /db-time requests (each holds a connection 0.5s)"
for _ in $(seq 20); do
  curl -s -o /dev/null -w '%{http_code}\n' "$API/db-time?sleep=0.5" >> /tmp/codes &
done
for _ in 1 2 3; do
  sleep 0.4
  echo -n "  postgres sessions from api: "
  docker compose exec -T db psql -U app -tAc "select count(*) from pg_stat_activity where application_name='api'"
  echo "  pool stats: $(curl -s "$API/pool-stats")"
done
wait
echo "  status codes: $(sort /tmp/codes | uniq -c | tr '\n' ' ')"; rm -f /tmp/codes /tmp/body
echo "  API container restarts: $(docker inspect -f '{{.RestartCount}}' "$(docker compose ps -q api)")"
