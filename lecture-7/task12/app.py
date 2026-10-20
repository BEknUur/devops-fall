import os
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, HTTPException, Request


@asynccontextmanager
async def lifespan(app: FastAPI):
    # min_size=0: запуск HTTP не ждёт подключения к PostgreSQL.
    app.state.pool = await asyncpg.create_pool(
        dsn=os.environ.get("DATABASE_URL"),
        min_size=0,
        max_size=5,
        timeout=1,
        command_timeout=1,
        server_settings={"application_name": "assignment-api"},
    )
    try:
        yield
    finally:
        await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


async def query_value(request: Request, sql: str):
    try:
        # До 1с на получение соединения; до 1с на SQL;
        # release использует тот же таймаут 1с для возврата соединения.
        async with request.app.state.pool.acquire(timeout=1) as connection:
            return await connection.fetchval(sql, timeout=1)
    except (asyncpg.PostgresError, asyncpg.InterfaceError, OSError, TimeoutError):
        raise HTTPException(status_code=503, detail="Database unavailable") from None


@app.get("/")
async def home():
    return {"message": "Hello from FastAPI", "version": "1.0"}


@app.get("/health/live")
async def live():
    return {"status": "alive"}


@app.get("/health/ready")
async def ready(request: Request):
    await query_value(request, "SELECT 1")
    return {"status": "ready"}


@app.get("/db-time")
async def db_time(request: Request):
    value = await query_value(request, "SELECT NOW()")
    return {"db_time": value.isoformat()}


@app.get("/pool-stats")
async def pool_stats(request: Request):
    pool = request.app.state.pool
    return {
        "size": pool.get_size(),
        "idle": pool.get_idle_size(),
        "max_size": pool.get_max_size(),
    }
