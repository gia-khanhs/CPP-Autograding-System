from .backend import AppBackend
from .frontend import App

def start_gui() -> tuple[AppBackend, App]:
    backend = AppBackend()
    app = App(backend)
    app.run()

    return backend, app
