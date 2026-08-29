import atexit
from concurrent.futures import ThreadPoolExecutor

# Central shared executor for background tasks to prevent thread explosion
executor = ThreadPoolExecutor(max_workers=4)

def shutdown_executor():
    executor.shutdown(wait=False)

atexit.register(shutdown_executor)
