from typing import Callable, Optional

_load_page_logger: Optional[Callable] = None

def set_load_page_logger(log_func: Optional[Callable]) -> None:
    global _load_page_logger
    _load_page_logger = log_func

def load_page_log(message: str) -> None:
    if _load_page_logger is not None:
        _load_page_logger(message)

def load_page_logged(function):
    def wrapper(*args, **kwargs):
        logged_data = f"Started: {function.__qualname__}"

        display_args = args[1:] if args else ()
        args_str = repr(display_args)
        kwargs_str = repr(kwargs)

        parts = []

        if display_args and len(args_str) < 200:
            parts.append(f"args={args_str}")

        if kwargs and len(kwargs_str) < 200:
            parts.append(f"kwargs={kwargs_str}")

        if parts:
            logged_data += " with " + ", ".join(parts)

        load_page_log(logged_data)

        try:
            returned_value = function(*args, **kwargs)
            returned_str = repr(returned_value)

            logged_data = f"Finished: {function.__qualname__}"
            if len(returned_str) < 200:
                logged_data += f" => {returned_str}"

            load_page_log(logged_data)

            return returned_value
        except Exception as exception:
            load_page_log(f"Error in {function.__qualname__}: {exception}")
            raise

    return wrapper