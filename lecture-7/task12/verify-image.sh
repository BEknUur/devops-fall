#!/usr/bin/env bash
set -euo pipefail

image=${1:?Usage: bash verify-image.sh IMAGE EXPECTED_VERSION}
expected_version=${2:?Pass the expected API version, for example 1.0}

# The application is downloaded from Docker Hub. No local build or source mount.
docker pull "$image"
container_id=$(docker run --rm -d -p 127.0.0.1:8080:8000 "$image")
trap 'docker rm -f "$container_id" >/dev/null' EXIT

curl --fail --silent --show-error --retry 30 --retry-delay 1 \
  --retry-all-errors --max-time 5 http://127.0.0.1:8080/health/live
printf '\n'

curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8080/ |
  python3 -c '
import json
import sys

response = json.load(sys.stdin)
print(response)
if response["version"] != sys.argv[1]:
    raise SystemExit("Unexpected API version")
' "$expected_version"

printf 'Verified published image: %s\n' "$image"
