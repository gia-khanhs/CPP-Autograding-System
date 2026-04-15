from datetime import datetime
from pathlib import Path
import threading

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

from config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR
from ..data.pipeline import DataPipeline
from .logger_backend import set_load_page_logger

class Window:
    def __init__(self, title: str, width: int, height: int) -> None:
        self._app = ctk.CTk()
        self._app.geometry(f"{width}x{height}")
        self._app.title(title)

    @property
    def app(self) -> ctk.CTk:
        return self._app

    def show(self) -> None:
        self._app.mainloop()


class OptionFrame:
    def __init__(self, parent, on_option_selected) -> None:
        self._frame = ctk.CTkFrame(parent)
        self._frame.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")
        self._frame.grid_columnconfigure(0, weight=1)

        self._option_count = 0
        self._on_option_selected = on_option_selected

    def add_option(self, text: str, page_name: str) -> None:
        button = ctk.CTkButton(
            self._frame,
            text=text,
            command=lambda: self._on_option_selected(page_name)
        )
        button.grid(row=self._option_count, column=0, padx=10, pady=(10, 5), sticky="ew")
        self._option_count += 1

    def finalize_layout(self) -> None:
        self._frame.grid_rowconfigure(self._option_count, weight=1)


class BasePage(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent)

#region load page
class LoadDataPage(BasePage):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)

        self.title = ctk.CTkLabel(self, text="Load Data", font=("Arial", 24, "bold"))
        self.title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.raw_data_desc = ctk.CTkLabel(self, text="The directory of the raw data:")
        self.raw_data_desc.grid(row=1, column=0, padx=20, pady=(5, 0), sticky="w")

        self.raw_course_path = ctk.CTkEntry(self, placeholder_text=str(RAW_DATA_DIR))
        self.raw_course_path.grid(row=2, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.raw_course_path.insert("end", str(RAW_DATA_DIR))

        self.processed_data_desc = ctk.CTkLabel(self, text="The directory of the processed data:")
        self.processed_data_desc.grid(row=3, column=0, padx=20, pady=(5, 0), sticky="w")

        self.processed_course_path = ctk.CTkEntry(self, placeholder_text=str(PROCESSED_DATA_DIR))
        self.processed_course_path.grid(row=4, column=0, padx=20, pady=(0, 5), sticky="ew")
        self.processed_course_path.insert("end", str(PROCESSED_DATA_DIR))

        self.load_button = ctk.CTkButton(self, text="GET DATA", command=self.start_load)
        self.load_button.grid(row=5, column=0, padx=20, pady=5, sticky="ew")

        self.log_desc = ctk.CTkLabel(self, text="Logs:")
        self.log_desc.grid(row=6, column=0, padx=20, pady=(5, 0), sticky="w")

        self.log_box = ctk.CTkTextbox(self, height=230)
        self.log_box.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="nsew")
        self.log_box.configure(state="disabled")

        set_load_page_logger(self.append_log)

    def start_load(self) -> None:
        self.load_button.configure(state="disabled")

        thread = threading.Thread(target=self.load_command, daemon=True)
        thread.start()

        self.load_button.configure(state="normal")

    def load_command(self) -> None:
        raw_dir = self.raw_course_path.get()
        processed_dir = self.processed_course_path.get()
        self.loaded_course = DataPipeline(Path(raw_dir), Path(processed_dir)).get()

    def append_log(self, message: str) -> None:
        try:
            now = datetime.now().strftime("%H:%M:%S")
            line = f"[{now}] {message}\n"

            self.log_box.configure(state="normal")
            self.log_box.insert("end", line)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        except:
            return
#endregion


class TrainPage(BasePage):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Train Model", font=("Arial", 24, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        info = ctk.CTkLabel(self, text="Configure training settings here.")
        info.grid(row=1, column=0, padx=20, pady=10, sticky="w")


class EvaluatePage(BasePage):
    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Evaluate", font=("Arial", 24, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        info = ctk.CTkLabel(self, text="View evaluation results here.")
        info.grid(row=1, column=0, padx=20, pady=10, sticky="w")


class ContentFrame:
    def __init__(self, parent) -> None:
        self._frame = ctk.CTkFrame(parent)
        self._frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self._frame.grid_rowconfigure(0, weight=1)
        self._frame.grid_columnconfigure(0, weight=1)

        self._pages = {}
        self._current_page = None

    def add_page(self, name: str, page_cls) -> None:
        page = page_cls(self._frame)
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_remove()
        self._pages[name] = page

    def show_page(self, name: str) -> None:
        if self._current_page is not None:
            self._current_page.grid_remove()

        self._current_page = self._pages[name]
        self._current_page.grid()

    @property
    def frame(self):
        return self._frame


class App:
    def __init__(self) -> None:
        self.window = Window("LLM-AC", 760, 540)

        self.window.app.grid_columnconfigure(0, weight=1, minsize=160)
        self.window.app.grid_columnconfigure(1, weight=5)
        self.window.app.grid_rowconfigure(0, weight=1)

        self.content = ContentFrame(self.window.app)

        self.content.add_page("load_data", LoadDataPage)
        self.content.add_page("train", TrainPage)
        self.content.add_page("evaluate", EvaluatePage)

        self.sidebar = OptionFrame(
            self.window.app,
            on_option_selected=self.content.show_page
        )

        self.sidebar.add_option("Load Data", "load_data")
        self.sidebar.add_option("Train Model", "train")
        self.sidebar.add_option("Evaluate", "evaluate")
        self.sidebar.finalize_layout()

        self.content.show_page("load_data")

    def run(self) -> None:
        self.window.show()



