from datetime import datetime
from pathlib import Path
import threading
from tkinter import filedialog

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

from config.paths import RAW_DATA_DIR, PROCESSED_DATA_DIR, CORRECTED_CODE_DIR
from ..data.pipeline import DataPipeline
from .backend import AppBackend
from .logger import set_log_handler

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
    def __init__(self, parent, backend: AppBackend) -> None:
        super().__init__(parent)
        self.backend = backend
        self.log_box = None

    def append_log(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        line = f"[{now}] {message}\n"
        self.after(0, lambda: self._append_log_ui(line))

    def _append_log_ui(self, line: str) -> None:
        if self.log_box is None:
            return
        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_entry_value(self, entry: ctk.CTkEntry, value: str) -> None:
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, str(value))
        entry.configure(state="disabled")

#region load page
class LoadDataPage(BasePage):
    def __init__(self, parent, backend) -> None:
        super().__init__(parent, backend)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(7, weight=1)

        self.title = ctk.CTkLabel(self, text="Load Data", font=("Arial", 24, "bold"))
        self.title.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

        self.raw_data_desc = ctk.CTkLabel(self, text="The directory of the raw data:")
        self.raw_data_desc.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 0), sticky="w")

        self.raw_course_path = ctk.CTkEntry(self, state="disabled")
        self.raw_course_path.grid(row=2, column=0, padx=(20, 10), pady=(0, 5), sticky="ew")
        self.set_entry_value(self.raw_course_path, str(RAW_DATA_DIR))

        self.raw_browse_button = ctk.CTkButton(
            self,
            text="Browse",
            width=90,
            command=self.choose_raw_folder
        )
        self.raw_browse_button.grid(row=2, column=1, padx=(0, 20), pady=(0, 5))

        self.processed_data_desc = ctk.CTkLabel(self, text="The directory of the processed data:")
        self.processed_data_desc.grid(row=3, column=0, columnspan=2, padx=20, pady=(5, 0), sticky="w")

        self.processed_course_path = ctk.CTkEntry(self, state="disabled")
        self.processed_course_path.grid(row=4, column=0, padx=(20, 10), pady=(0, 5), sticky="ew")
        self.set_entry_value(self.processed_course_path, str(PROCESSED_DATA_DIR))

        self.processed_browse_button = ctk.CTkButton(
            self,
            text="Browse",
            width=90,
            command=self.choose_processed_folder
        )
        self.processed_browse_button.grid(row=4, column=1, padx=(0, 20), pady=(0, 5))

        self.load_button = ctk.CTkButton(self, text="GET DATA", command=self.start_load)
        self.load_button.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        self.log_desc = ctk.CTkLabel(self, text="Logs:")
        self.log_desc.grid(row=6, column=0, columnspan=2, padx=20, pady=(5, 0), sticky="w")

        self.log_box = ctk.CTkTextbox(self, height=230)
        self.log_box.grid(row=7, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="nsew")
        self.log_box.configure(state="disabled")

        set_log_handler("load_data", self.append_log)

    def choose_raw_folder(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.raw_course_path.get() or str(RAW_DATA_DIR))
        if folder:
            self.set_entry_value(self.raw_course_path, folder)

    def choose_processed_folder(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.processed_course_path.get() or str(PROCESSED_DATA_DIR))
        if folder:
            self.set_entry_value(self.processed_course_path, folder)

    def start_load(self) -> None:
        self.load_button.configure(state="disabled")
        self.raw_browse_button.configure(state="disabled")
        self.processed_browse_button.configure(state="disabled")
        thread = threading.Thread(target=self.load_command, daemon=True)
        thread.start()

    def load_command(self) -> None:
        try:
            raw_dir = self.raw_course_path.get()
            processed_dir = self.processed_course_path.get()
            self.backend.load_data(Path(raw_dir), Path(processed_dir))
        finally:
            self.after(0, lambda: self.load_button.configure(state="normal"))
            self.after(0, lambda: self.raw_browse_button.configure(state="normal"))
            self.after(0, lambda: self.processed_browse_button.configure(state="normal"))
#endregion

#region ac page
class AutocorrectionPage(BasePage):
    def __init__(self, parent, backend) -> None:
        super().__init__(parent, backend)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(7, weight=1)

        self.title = ctk.CTkLabel(self, text="Autocorrection Module", font=("Arial", 24, "bold"))
        self.title.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="w")

        self.corrected_code_desc = ctk.CTkLabel(self, text="The output directory of the corrected code:")
        self.corrected_code_desc.grid(row=1, column=0, columnspan=2, padx=20, pady=(5, 0), sticky="w")

        self.corrected_code_path = ctk.CTkEntry(self, state="disabled")
        self.corrected_code_path.grid(row=2, column=0, padx=(20, 10), pady=(0, 5), sticky="ew")
        self.set_entry_value(self.corrected_code_path, str(CORRECTED_CODE_DIR))

        self.corrected_browse_button = ctk.CTkButton(
            self,
            text="Browse",
            width=90,
            command=self.choose_corrected_folder
        )
        self.corrected_browse_button.grid(row=2, column=1, padx=(0, 20), pady=(0, 5))

        self.correct_button = ctk.CTkButton(self, text="CORRECT CODE", command=self.start_correct)
        self.correct_button.grid(row=5, column=0, columnspan=2, padx=20, pady=5, sticky="ew")

        self.log_desc = ctk.CTkLabel(self, text="Logs:")
        self.log_desc.grid(row=6, column=0, columnspan=2, padx=20, pady=(5, 0), sticky="w")

        self.log_box = ctk.CTkTextbox(self, height=230)
        self.log_box.grid(row=7, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="nsew")
        self.log_box.configure(state="disabled")

        set_log_handler("autocorrection", self.append_log)

    def choose_corrected_folder(self) -> None:
        folder = filedialog.askdirectory(initialdir=self.corrected_code_path.get() or str(CORRECTED_CODE_DIR))
        if folder:
            self.set_entry_value(self.corrected_code_path, folder)

    def start_correct(self) -> None:
        self.correct_button.configure(state="disabled")
        self.corrected_browse_button.configure(state="disabled")

        thread = threading.Thread(target=self.correct_command, daemon=True)
        thread.start()

    def correct_command(self) -> None:
        try:
            corrected_dir = Path(self.corrected_code_path.get())
            self.backend.corrected_dir = corrected_dir
            self.backend.correct_code(corrected_dir)
        finally:
            self.after(0, lambda: self.correct_button.configure(state="normal"))
            self.after(0, lambda: self.corrected_browse_button.configure(state="normal"))
#endregion

#region grading page 
class GradingPage(BasePage):
    def __init__(self, parent, backend) -> None:
        super().__init__(parent, backend)

        self.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(self, text="Evaluate", font=("Arial", 24, "bold"))
        title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        info = ctk.CTkLabel(self, text="View evaluation results here.")
        info.grid(row=1, column=0, padx=20, pady=10, sticky="w")

        set_log_handler("grading", self.append_log)
#endregion

class ContentFrame:
    def __init__(self, parent) -> None:
        self._frame = ctk.CTkFrame(parent)
        self._frame.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")
        self._frame.grid_rowconfigure(0, weight=1)
        self._frame.grid_columnconfigure(0, weight=1)

        self._pages = {}

    def add_page(self, name: str, page_cls, backend) -> None:
        page = page_cls(self._frame, backend)
        page.grid(row=0, column=0, sticky="nsew")
        self._pages[name] = page

    def show_page(self, name: str) -> None:
        self._pages[name].tkraise()

    @property
    def frame(self):
        return self._frame


from .backend import AppBackend

class App:
    def __init__(self, backend: AppBackend) -> None:
        self.backend = backend
        self.window = Window("LLM-AC", 760, 540)
        self.window._app.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.window.app.grid_columnconfigure(0, weight=1, minsize=160)
        self.window.app.grid_columnconfigure(1, weight=5)
        self.window.app.grid_rowconfigure(0, weight=1)

        self.content = ContentFrame(self.window.app)

        self.content.add_page("load_data", LoadDataPage, self.backend)
        self.content.add_page("autocorrection", AutocorrectionPage, self.backend)
        self.content.add_page("grading", GradingPage, self.backend)

        self.sidebar = OptionFrame(
            self.window.app,
            on_option_selected=self.content.show_page
        )

        self.sidebar.add_option("Load Data", "load_data")
        self.sidebar.add_option("Autocorrection", "autocorrection")
        self.sidebar.add_option("Grading", "grading")
        self.sidebar.finalize_layout()

        self.content.show_page("load_data")

    def run(self) -> None:
        self.window.show()

    def on_closing(self):
        # if self.backend.code_corrector is not None:
        #     self.backend.code_corrector.shutdown()
        self.window._app.destroy()
