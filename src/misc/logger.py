from datetime import datetime

from config.paths import LOG_FILE


def logged(function):
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
    with open(LOG_FILE, "a") as log_file:
        log_file.write(text)
        log_file.close()