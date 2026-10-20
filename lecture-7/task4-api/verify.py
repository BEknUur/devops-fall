"""Проверка задания в отдельном Compose-проекте; нужны Python 3 и Docker."""

import json
import os
import secrets
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


project = "task4-check-" + secrets.token_hex(4)
directory = Path(__file__).resolve().parent
environment = os.environ.copy()
environment["POSTGRES_PASSWORD"] = secrets.token_hex(24)
with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
environment["API_PORT"] = str(port)
base_url = f"http://127.0.0.1:{port}"


def compose(*arguments):
    result = subprocess.run(
        ["docker", "compose", "-p", project, *arguments],
        cwd=directory,
        env=environment,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout.strip()


def request(path):
    start = time.monotonic()
    try:
        with urllib.request.urlopen(base_url + path, timeout=5) as response:
            status = response.status
            body = json.load(response)
    except urllib.error.HTTPError as error:
        status = error.code
        body = json.load(error)
    return status, time.monotonic() - start, body


def wait_for(path):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        try:
            if request(path)[0] == 200:
                return
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(0.5)
    raise AssertionError(f"{path} не восстановился за 60с")


def check_stage(label, database_status):
    print(label, flush=True)
    for path, expected in [
        ("/health/live", 200),
        ("/health/ready", database_status),
        ("/db-time", database_status),
    ]:
        status, elapsed, body = request(path)
        print(f"  {path}: {status}, {elapsed:.3f}s", flush=True)
        assert status == expected, (path, status, body)
        assert elapsed < 5, (path, elapsed)
        if path == "/db-time" and status == 200:
            assert "db_time" in body, body


def api_identity():
    container = compose("ps", "-q", "api")
    result = subprocess.run(
        ["docker", "inspect", "--format",
         "{{.Id}} {{.State.StartedAt}} {{.RestartCount}}", container],
        check=True, text=True, capture_output=True,
    )
    return result.stdout.strip()


def session_count():
    return int(compose(
        "exec", "-T", "postgres", "psql", "-U", "app", "-d", "app", "-Atc",
        "SELECT count(*) FROM pg_stat_activity "
        "WHERE application_name = 'assignment-api'",
    ))


print(f"Изолированный проект: {project}; API: {base_url}", flush=True)
try:
    compose("create", "postgres")
    compose("up", "-d", "--build", "--no-deps", "api")
    wait_for("/health/live")
    initial_identity = api_identity()
    check_stage("1. API запущен, PostgreSQL остановлен", 503)

    compose("start", "postgres")
    wait_for("/health/ready")
    check_stage("2. PostgreSQL запущен", 200)

    compose("stop", "postgres")
    check_stage("3. PostgreSQL снова остановлен", 503)

    compose("start", "postgres")
    wait_for("/health/ready")
    check_stage("4. PostgreSQL восстановлен", 200)

    # Pause оставляет TCP открытым, но БД перестаёт отвечать.
    compose("pause", "postgres")
    try:
        check_stage("5. PostgreSQL завис (docker pause)", 503)
    finally:
        compose("unpause", "postgres")
    wait_for("/health/ready")
    check_stage("6. PostgreSQL отвечает после unpause", 200)

    barrier = threading.Barrier(21)

    def concurrent_request():
        barrier.wait()
        return request("/db-time")

    samples = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(concurrent_request) for _ in range(20)]
        barrier.wait()
        while not all(future.done() for future in futures):
            samples.append(request("/pool-stats")[2])
            time.sleep(0.005)
        results = [future.result() for future in futures]
    samples.append(request("/pool-stats")[2])
    assert all(status == 200 and "db_time" in body
               for status, elapsed, body in results), results
    assert all(sample["size"] <= 5 and sample["max_size"] == 5
               for sample in samples), samples
    sessions = session_count()
    assert 0 < sessions <= 5, sessions
    print(f"20 одновременных запросов: 20/20 HTTP200; "
          f"max observed pool size={max(sample['size'] for sample in samples)}; "
          f"PostgreSQL sessions={sessions}", flush=True)

    assert api_identity() == initial_identity, "API перезапускался"
    print("Container ID, StartedAt, RestartCount API не изменились.", flush=True)

    compose("stop", "-t", "10", "api")
    assert "Application shutdown complete" in compose("logs", "api")
    assert session_count() == 0, "Соединения не закрылись при shutdown"
    print("Graceful shutdown: pool закрыт, DB sessions=0. Все проверки пройдены.",
          flush=True)
finally:
    compose("down", "--volumes")
