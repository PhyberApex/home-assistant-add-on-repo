#!/usr/bin/env sh
set -e

OPTIONS_FILE=/data/options.json

log() { echo "[kuroshiro] $*"; }

option() {
  [ -f "$OPTIONS_FILE" ] || return 0
  jq -r "$1 // empty" "$OPTIONS_FILE"
}

persist_in_data() {
  data_dir="$1"
  app_path="$2"
  mkdir -p "$data_dir" "$(dirname "$app_path")"
  rm -rf "$app_path"
  ln -s "$data_dir" "$app_path"
}

start_postgres() {
  mkdir -p "$PGDATA" "$PGSOCKET"
  touch "$PGLOG"
  chown -R postgres:postgres "$PGDATA" "$PGSOCKET" "$PGLOG"
  chmod 700 "$PGDATA"

  if [ ! -s "$PGDATA/PG_VERSION" ]; then
    log "initialising the bundled postgres cluster in $PGDATA"
    su-exec postgres initdb -D "$PGDATA" -U "$KUROSHIRO_DB_USER" \
      --auth-local=trust --auth-host=trust --encoding=UTF8 >/dev/null
  fi

  su-exec postgres pg_ctl -D "$PGDATA" -w -t 60 -l "$PGLOG" \
    -o "-c listen_addresses=$KUROSHIRO_DB_HOST -p $KUROSHIRO_DB_PORT -k $PGSOCKET" start

  if ! su-exec postgres psql -h "$PGSOCKET" -U "$KUROSHIRO_DB_USER" -d postgres \
      -tAc "SELECT 1 FROM pg_database WHERE datname = '$KUROSHIRO_DB_DB'" | grep -q 1; then
    log "creating database $KUROSHIRO_DB_DB"
    su-exec postgres createdb -h "$PGSOCKET" -U "$KUROSHIRO_DB_USER" "$KUROSHIRO_DB_DB"
  fi
}

stop_postgres() {
  su-exec postgres pg_ctl -D "$PGDATA" -m fast -w stop >/dev/null 2>&1 || true
}

# Devices are handed absolute image and firmware URLs built from this, so it has to be an
# address the devices themselves can reach - never localhost.
resolve_api_url() {
  url=$(option '.api_url')
  if [ -n "$url" ]; then
    echo "${url%/}"
    return 0
  fi

  [ -n "$SUPERVISOR_TOKEN" ] || return 0
  host_ip=$(curl -fsS -H "Authorization: Bearer $SUPERVISOR_TOKEN" http://supervisor/network/info \
    | jq -r '[.data.interfaces[]? | select(.enabled) | .ipv4.address[]?]
             | map(split("/")[0]) | first // empty' 2>/dev/null) || return 0
  if [ -n "$host_ip" ]; then
    echo "http://${host_ip}:${KUROSHIRO_PORT}"
  fi
  return 0
}

persist_in_data /data/screens/devices /app/public/screens/devices
persist_in_data /data/firmware /app/public/firmware
persist_in_data /data/uploads /app/uploads

KUROSHIRO_API_URL=$(resolve_api_url)
if [ -z "$KUROSHIRO_API_URL" ]; then
  log "ERROR: could not work out the address your TRMNL devices should talk to."
  log "Set the 'api_url' option (for example http://192.168.1.10:${KUROSHIRO_PORT}) and restart."
  exit 1
fi
export KUROSHIRO_API_URL
log "devices will be pointed at $KUROSHIRO_API_URL"

start_postgres

terminate() {
  kill -TERM "$app_pid" 2>/dev/null || true
  wait "$app_pid" 2>/dev/null || true
  stop_postgres
  exit 0
}
trap terminate INT TERM

/app/entrypoint.sh &
app_pid=$!

exit_code=0
wait "$app_pid" || exit_code=$?
stop_postgres
exit "$exit_code"
