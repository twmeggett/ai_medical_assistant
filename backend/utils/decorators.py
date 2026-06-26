import time
import inspect
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def timer(_func):
    def report_time(start_time: float, end_time: float) -> str:
        return f"Execution time: {end_time - start_time:.2f} seconds"
    
    @wraps(_func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        _func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.info(report_time(start_time, end_time))

    @wraps(_func)
    async def asyn_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        await _func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.info(report_time(start_time, end_time))

    return asyn_wrapper if inspect.iscoroutinefunction(_func) else sync_wrapper