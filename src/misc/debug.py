from datetime import datetime
import time
from functools import wraps

from config.paths import LOG_FILE

#region logger
def logged(function):
    @wraps(function)
    def wrapper(*args, **kargs):
        returned_value = function(*args, **kargs)

        now = datetime.now()
        formatted_time = now.strftime("%H:%M:%S")

        log_data = f"[{formatted_time}]: {function.__name__} has returned {returned_value}"

        with open(LOG_FILE, "a", encoding="utf-8") as log_file:
            log_file.write(log_data + "\n")
            log_file.close()

        return returned_value
    
    return wrapper
        

def clear_logs() -> None:
    with open(LOG_FILE, "w") as log_file:
        log_file.write("")
        log_file.close()


def write_log(text: str) -> None:
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write(text)
        log_file.close()
#endregion

#region timer
def timed(function):
    @wraps(function)
    def wrapper(*args, **kargs):
        initial_time = time.perf_counter()
        returned_val = function(*args, **kargs)
        final_time = time.perf_counter()

        elapsed_time = final_time - initial_time

        now = datetime.now()
        formatted_time = now.strftime("%H:%M:%S")

        return returned_val

    return wrapper
#endregion

def delayed(delay_seconds=2.5):
    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwargs):
            initial_time = time.perf_counter()
            returned_val = function(*args, **kwargs)
            
            elapsed = time.perf_counter() - initial_time
            time.sleep(max(0, delay_seconds - elapsed))
            
            return returned_val
        return wrapper
    return decorator

def exp_delayed(initial_delay=1, multiplier=2, max_delay=None):
    def decorator(function):
        current_delay = initial_delay

        @wraps(function)
        def wrapper(*args, **kwargs):
            nonlocal current_delay

            initial_time = time.perf_counter()
            returned_val = function(*args, **kwargs)

            elapsed = time.perf_counter() - initial_time
            time.sleep(max(0, current_delay - elapsed))

            next_delay = current_delay * multiplier
            if max_delay is not None:
                next_delay = min(next_delay, max_delay)
            current_delay = next_delay

            return returned_val

        return wrapper
    return decorator