from collections.abc import Callable 

from functools import wraps 
from time import perf_counter 
from typing import ParamSpec, TypeVar 


P = ParamSpec("P")
R = TypeVar("R")

def timed(function: Callable[P,R]) -> Callable[P,R]:
    @wraps(function)
    def wrapper(*args: P.args, **kwargs: P.kwargs) ->R:
        started = perf_counter()

        try:
            return function(*args,**kwargs)
        finally:
            elapsed = perf_counter() - started 
            print(f"{function.__name__} took {elapsed:.3f}s")

    return wrapper




if __name__ == "__main__":
    @timed
    def work() -> str:
        """Succeeds."""
        return "ok"

    @timed
    def boom() -> None:
        """Fails."""
        raise RuntimeError("deployment failed")

    print(work())
    assert work.__name__ == "work"        
    assert work.__doc__ == "Succeeds."

    try:
        boom()                             
    except RuntimeError as error:
        print("caught:", error)