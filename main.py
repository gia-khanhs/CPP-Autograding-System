from pathlib import Path

from src.misc.debug import clear_logs

from src.gui.main import start_gui

backend, app = start_gui()
course = backend.loaded_course