import asyncio 
from concurrent.futures import ThreadPoolExecutor 
from time import perf_counter, sleep 


SERVICES = ["api","auth"]

DELAY = 1.0 


# 1 threads 

def check_service(service:str)->tuple[str,str]:
    sleep(DELAY)
    return service, "healthy"


def run_threads()->None:
    started = perf_counter()
    with ThreadPoolExecutor(max_workers=len(SERVICES))  as pool:
        results = list(pool.map(check_service,SERVICES))
        print(f"threads: {perf_counter() - started:.2f}s -> {results}")



# 2 asyncio 
async def check_async(service:str)->tuple[str,str]:
    await asyncio.sleep(DELAY)
    return service, "healthy"

async def run_async() -> None:
    started = perf_counter()
    async with asyncio.TaskGroup() as group:               
        tasks = [group.create_task(check_async(s)) for s in SERVICES]
    results = [task.result() for task in tasks]             
    print(f"asyncio: {perf_counter() - started:.2f}s -> {results}")



async def check_blocking(service: str) -> tuple[str, str]:
    sleep(DELAY)                 
    return service, "healthy"


async def run_async_blocking() -> None:
    started = perf_counter()
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(check_blocking(s)) for s in SERVICES]
    results = [task.result() for task in tasks]
    print(f"asyncio + time.sleep: {perf_counter() - started:.2f}s -> {results}")


if __name__ == "__main__":
    run_threads()                       
    asyncio.run(run_async())              
    asyncio.run(run_async_blocking())     