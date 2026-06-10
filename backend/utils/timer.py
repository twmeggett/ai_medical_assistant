import time
import inspect
import logging

logger = logging.getLogger(__name__)

def timer(_func):
    def report_time(start_time: float, end_time: float) -> str:
        return f"Execution time: {start_time - end_time:.2} seconds"
    
    def sync_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        _func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.info(report_time(start_time, end_time))

    def asyn_wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        _func(*args, **kwargs)
        end_time = time.perf_counter()
        logger.info(report_time(start_time, end_time))

    return asyn_wrapper if inspect.iscoroutinefunction(_func) else sync_wrapper