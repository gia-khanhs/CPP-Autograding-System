from typing import Optional

from .frontend import App
from ..data.structures import Course

app = App()
load_page = app.content._pages["load_data"]

def get_course() -> Optional[Course]:
    if hasattr(load_page, "loaded_course"):
        return load_page.loaded_course
    
    return None

def get_load_page_logs() -> str:
    return load_page.log_box.get("1.0", "end-1c")