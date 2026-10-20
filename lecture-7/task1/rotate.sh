#!/usr/bin/env bash
set -euo pipefail

log_file="${LOG_DIR:-/home/logs}/app.log"
max_size=1048576 # 1 MiB

if [ ! -f "$log_file" ]; then
    exit 0
fi

if [ "$(stat -c %s "$log_file")" -lt "$max_size" ]; then
    exit 0
fi

start=$(date +%s%N)

# Keep the current log and only two old copies.
rm -f "$log_file.2"
if [ -f "$log_file.1" ]; then
    mv "$log_file.1" "$log_file.2"
fi
cp "$log_file" "$log_file.1"

# Keep the same file open: the application can continue writing to it.
truncate -s 0 "$log_file"

duration_ms=$(( ($(date +%s%N) - start) / 1000000 ))
# systemd redirects this line to /home/log_rotates.log.
echo "$(date --iso-8601=seconds) rotated app.log in ${duration_ms} ms"
