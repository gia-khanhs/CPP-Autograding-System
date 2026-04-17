from functools import wraps
from typing import Callable, Optional, TypeVar, Any

F = TypeVar("F", bound=Callable[..., Any])

_log_handlers: dict[str, Callable[[str], None]] = {}

def set_log_handler(page_name: str, log_func: Optional[Callable[[str], None]]) -> None:
    if log_func is None:
        _log_handlers.pop(page_name, None)
    else:
        _log_handlers[page_name] = log_func

def app_log(page_name: str, message: str) -> None:
    log_func = _log_handlers.get(page_name)
    if log_func is not None:
        log_func(message)

def page_logged(page_name: str):
    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args, **kwargs):
            message = f"Started: {function.__qualname__}"

            display_args = args[1:] if args else ()
            parts = []

            if display_args:
                args_str = repr(display_args)
                if len(args_str) < 200:
                    parts.append(f"args={args_str}")

            if kwargs:
                kwargs_str = repr(kwargs)
                if len(kwargs_str) < 200:
                    parts.append(f"kwargs={kwargs_str}")

            if parts:
                message += " with " + ", ".join(parts)

            app_log(page_name, message)

            try:
                result = function(*args, **kwargs)

                finished = f"Finished: {function.__qualname__}"
                result_str = repr(result)
                if len(result_str) < 200:
                    finished += f" => {result_str}"

                app_log(page_name, finished)
                return result
            except Exception as e:
                app_log(page_name, f"Error in {function.__qualname__}: {e}")
                raise

        return wrapper  # type: ignore

    return decorator

load_page_logged = page_logged("load_data")
autocorrection_page_logged = page_logged("autocorrection")
grading_page_logged = page_logged("grading")