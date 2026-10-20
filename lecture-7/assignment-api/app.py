import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from psycopg_pool import AsyncConnectionPool

DB_URL = os.getenv("DATABASE_URL", "postgresql://app:app@db:5432/app")
REQUEST_TIMEOUT = 4.5  # hard cap so DB requests fail within 5s during an outage

# one shared pool for the whole process, created once, never per request
pool = AsyncConnectionPool(
    DB_URL,
    min_size=1,
    max_size=5,
    open=False,
    timeout=3,  # max wait for a free connection
    reconnect_timeout=10,  # give up a failed reconnect quickly; next request retries
    check=AsyncConnectionPool.check_connection,  # drop broken connections on checkout
    kwargs={
        "connect_timeout": 3,
        "application_name": "api",
        "options": "-c statement_timeout=3000",
    },
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await pool.open(wait=False)  # don't block startup waiting for postgres
    yield
    await pool.close()  # graceful shutdown


app = FastAPI(lifespan=lifespan)


async def query(sql, params=None):
    async with asyncio.timeout(REQUEST_TIMEOUT):
        async with pool.connection() as conn:
            cur = await conn.execute(sql, params)
            return await cur.fetchone()


def unavailable(e):
    return JSONResponse({"status": "unavailable", "error": type(e).__name__}, status_code=503)


@app.get("/health/live")
async def live():
    return {"status": "alive"}


@app.get("/health/ready")
async def ready():
    try:
        await query("SELECT 1")
    except Exception as e:
        return unavailable(e)
    return {"status": "ready"}


@app.get("/db-time")
async def db_time(sleep: float = 0):
    # ponytail: ?sleep= only exists to hold connections for the concurrency demo
    try:
        row = await query("SELECT NOW(), pg_sleep(%s)", (sleep,))
    except Exception as e:
        return unavailable(e)
    return {"db_time": row[0].isoformat()}


@app.get("/pool-stats")
async def pool_stats():
    return pool.get_stats()
