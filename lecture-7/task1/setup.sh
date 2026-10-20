#!/usr/bin/env bash
# Run with sudo on a Linux machine using systemd.
set -euo pipefail
cd "$(dirname "$0")"

if [ "$EUID" -ne 0 ]; then
    echo "Run: sudo ./setup.sh" >&2
    exit 1
fi
if [ ! -d /run/systemd/system ]; then
    echo "This installation requires systemd running as the system manager." >&2
    exit 1
fi

install -d -m 755 /home/logs /opt/simple-api
install -m 644 app.py requirements.txt /opt/simple-api/
python3 -m venv /opt/simple-api/venv
/opt/simple-api/venv/bin/pip install -q -r /opt/simple-api/requirements.txt

# Remove the configuration used by the previous version of this task.
# Rotation is now performed only by our timer and Bash script.
rm -f /etc/logrotate.d/simple-api
install -m 755 rotate.sh /usr/local/bin/simple-api-rotate
install -m 644 simple-api.service logrotate-api.service logrotate-api.timer /etc/systemd/system/

systemctl daemon-reload
systemctl enable simple-api.service logrotate-api.timer
systemctl restart simple-api.service logrotate-api.timer
systemctl --no-pager status simple-api.service
