### 1. Parse 100 small local configuration files once — **sequential**

The total work is a few a milliseconds, of a local dis i/o 
the page cache makes and repeat reads 
creating the pool in this case cost more than parsing 
concureency also add failure modes 
so for this reason i think that we should to stop for sequential 


### 2. Checksums for thousands of large artifacts on a multi-core machine — **processes**







### 3. Call 50 services through a blocking HTTP client — **a bounded thread pool*

there is no any async due to that await has noting to do 
threads handle this natielty 
like the one thread waits on a socket it releases the gil and the other proceed. 



### 4. Monitor 5,000 connections through an async-compatible client — **asyncio**
this is pretty easy like the 5k threads means that of the gigabytes of a stack so it's really heavy 
The condition is that the stack is async all the way down (`httpx`, `aiohttp`). One blocking call
anywhere inside a coroutine freezes the entire loop  measured in Task 4: the same TaskGroup code
takes 1.00 s with `await asyncio.sleep()` and 5.00 s with `time.sleep()`, because a blocking call
never yields to the loop. If a blocking call is unavoidable, isolate it with
`await asyncio.to_thread(...)`.



# my plan 
iterating thrugh files lazily with a generator 
parse each line with small function 
represernt validation rules as the objects 
 report expected failure with exceptions 
 save the process for cpu heavy tasks