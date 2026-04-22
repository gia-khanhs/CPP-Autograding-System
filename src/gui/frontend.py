from datetime import datetime
from pathlib import Path
import os
import platform
import subprocess
import threading
from typing import Literal
from tkinter import filedialog, ttk

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

from config.paths import CORRECTED_CODE_DIR, GRADE_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR
from .backend import AppBackend
from .logger import set_log_handler
from .state import BatchRunResult, FailureItem, ProgressUpdate, RunConfig, WeekResult

STATEFUL_WIDGETS = (
    ctk.CTkCheckBox,
    ctk.CTkButton,
    ctk.CTkEntry,
    ctk.CTkTextbox,
    ctk.CTkOptionMenu,
)

def open_in_file_manager(path: Path) -> None:
    if not path.exists():
        return

    if platform.system() == "Windows":
        os.startfile(path)  # type: ignore[attr-defined]
        return

    if platform.system() == "Darwin":
        subprocess.Popen(["open", str(path)])
        return

    subprocess.Popen(["xdg-open", str(path)])


class Window:
    def __init__(self, title: str, width: int, height: int) -> None:
        self._app = ctk.CTk()
        self._app.geometry(f"{width}x{height}")
        self._app.minsize(width, height)
        self._app.title(title)

    @property
    def app(self) -> ctk.CTk:
        return self._app

    def show(self) -> None:
        self._app.mainloop()

# region navigation
class NavigationFrame:
    def __init__(self, parent, on_select) -> None:
        self._frame = ctk.CTkFrame(parent, corner_radius=0)
        self._frame.grid(row=0, column=0, sticky="nsew")
        self._frame.grid_columnconfigure(0, weight=1)
        self._buttons: dict[str, ctk.CTkButton] = {}
        self._on_select = on_select

        self.title = ctk.CTkLabel(
            self._frame,
            text="CPP Autograder",
            font=("Arial", 24, "bold"),
        )
        self.title.grid(row=0, column=0, padx=20, pady=(24, 16), sticky="w")

    def add_page(self, row: int, page_name: str, label: str) -> None:
        button = ctk.CTkButton(
            self._frame,
            text=label,
            anchor="w",
            command=lambda: self._on_select(page_name),
        )
        button.grid(row=row, column=0, padx=14, pady=6, sticky="ew")
        self._buttons[page_name] = button

    def set_active(self, page_name: str) -> None:
        for name, button in self._buttons.items():
            if name == page_name:
                button.configure(fg_color=("#1f6aa5", "#1f6aa5"))
            else:
                button.configure(fg_color="transparent")
# endregion


# region content frame
class ContentFrame:
    def __init__(self, parent) -> None:
        self._frame = ctk.CTkFrame(parent, corner_radius=0)
        self._frame.grid(row=0, column=1, sticky="nsew")
        self._frame.grid_rowconfigure(0, weight=1)
        self._frame.grid_columnconfigure(0, weight=1)
        self._pages: dict[str, ctk.CTkFrame] = {}

    def add_page(self, name: str, page: ctk.CTkFrame) -> None:
        page.grid(row=0, column=0, sticky="nsew")
        self._pages[name] = page

    def show_page(self, name: str) -> None:
        self._pages[name].tkraise()
# endregion


# region base page
class BasePage(ctk.CTkFrame):
    def __init__(self, parent, backend: AppBackend) -> None:
        super().__init__(parent)
        self.backend = backend

    def format_log_line(self, message: str) -> str:
        now = datetime.now().strftime("%H:%M:%S")
        return f"[{now}] {message}\n"

    def set_entry_value(self, entry: ctk.CTkEntry, value: str) -> None:
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, value)
        entry.configure(state="disabled")

    def choose_directory(self, current_value: str, fallback: Path) -> str:
        folder = filedialog.askdirectory(initialdir=current_value or str(fallback))
        return folder or current_value

    def create_path_row(self, parent, row: int, label_text: str, default_path: Path):
        label = ctk.CTkLabel(parent, text=label_text)
        label.grid(row=row * 2, column=0, columnspan=2, padx=16, pady=(12, 0), sticky="w")

        entry = ctk.CTkEntry(parent, state="disabled")
        entry.grid(row=row * 2 + 1, column=0, padx=(16, 8), pady=(0, 8), sticky="ew")
        self.set_entry_value(entry, str(default_path))

        browse_button = ctk.CTkButton(parent, text="Browse", width=90)
        browse_button.grid(row=row * 2 + 1, column=1, padx=(0, 16), pady=(0, 8))

        return entry, browse_button
# endregion


# region run page
class RunPage(BasePage):
    def __init__(self, parent, backend: AppBackend, on_finished) -> None:
        super().__init__(parent, backend)
        self.on_finished = on_finished
        self.log_box: ctk.CTkTextbox | None = None
        self._is_running = False

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.page_scroll = ctk.CTkScrollableFrame(self)
        self.page_scroll.grid(row=0, column=0, sticky="nsew")
        self.page_scroll.grid_columnconfigure(0, weight=1)

        self.header = ctk.CTkFrame(self.page_scroll, fg_color="transparent")
        self.header.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        self.header.grid_columnconfigure(0, weight=1)

        self.title = ctk.CTkLabel(self.header, text="Run Grading", font=("Arial", 28, "bold"))
        self.title.grid(row=0, column=0, sticky="w")

        self.subtitle = ctk.CTkLabel(
            self.header,
            text="Run grading week by week and keep the logs in the background.",
        )
        self.subtitle.grid(row=1, column=0, sticky="w")

        self.form = ctk.CTkFrame(self.page_scroll)
        self.form.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.form.grid_columnconfigure(0, weight=1)

        self.raw_entry, self.raw_browse_button = self.create_path_row(
            self.form, 0, "Raw course folder", RAW_DATA_DIR
        )
        self.processed_entry, self.processed_browse_button = self.create_path_row(
            self.form, 1, "Processed folder", PROCESSED_DATA_DIR
        )
        self.corrected_entry, self.corrected_browse_button = self.create_path_row(
            self.form, 2, "Corrected output folder", CORRECTED_CODE_DIR
        )
        self.grade_entry, self.grade_browse_button = self.create_path_row(
            self.form, 3, "Score output folder", GRADE_DIR
        )

        self.raw_browse_button.configure(command=self.choose_raw_folder)
        self.processed_browse_button.configure(command=self.choose_processed_folder)
        self.corrected_browse_button.configure(command=self.choose_corrected_folder)
        self.grade_browse_button.configure(command=self.choose_grade_folder)

        self.options = ctk.CTkFrame(self.page_scroll)
        self.options.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.options.grid_columnconfigure(0, weight=1)

        self.run_autocorrection_var = ctk.BooleanVar(value=True)
        self.run_autocorrection_checkbox = ctk.CTkCheckBox(
            self.options,
            text="Run autocorrection before grading",
            variable=self.run_autocorrection_var,
        )
        self.run_autocorrection_checkbox.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        self.week_label = ctk.CTkLabel(self.options, text="Weeks to run")
        self.week_label.grid(row=1, column=0, padx=16, pady=(0, 4), sticky="w")

        self.week_scroll = ctk.CTkFrame(self.options)
        self.week_scroll.grid(row=2, column=0, padx=16, pady=(0, 12), sticky="ew")
        self.week_scroll.grid_columnconfigure(0, weight=1)

        self.week_vars: dict[str, ctk.BooleanVar] = {}
        self.week_checkboxes: list[ctk.CTkCheckBox] = []
        self.week_text_vars: list[ctk.StringVar] = []
        self.week_checked_vars: list[ctk.BooleanVar] = []
        self.refresh_weeks()

        self.actions = ctk.CTkFrame(self.page_scroll, fg_color="transparent")
        self.actions.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.actions.grid_columnconfigure(0, weight=1)

        self.start_button = ctk.CTkButton(
            self.actions,
            text="Start grading",
            height=42,
            command=self.start_run,
        )
        self.start_button.grid(row=0, column=0, sticky="ew")

        self.progress_card = ctk.CTkFrame(self.page_scroll)
        self.progress_card.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.progress_card.grid_columnconfigure(1, weight=1)

        self._make_progress_label("Status", 0)
        self.status_value = self._make_value_label(0, "Idle")

        self._make_progress_label("Current week", 1)
        self.week_value = self._make_value_label(1, "-")

        self._make_progress_label("Progress", 2)
        self.progress_value = self._make_value_label(2, "0 / 0")

        self._make_progress_label("Failures", 3)
        self.failure_value = self._make_value_label(3, "0")

        self.progress_bar = ctk.CTkProgressBar(self.progress_card)
        self.progress_bar.grid(row=4, column=0, columnspan=2, padx=16, pady=(8, 16), sticky="ew")
        self.progress_bar.set(0)

        self.logs_card = ctk.CTkFrame(self.page_scroll)
        self.logs_card.grid(row=5, column=0, padx=20, pady=(0, 20), sticky="ew")
        self.logs_card.grid_columnconfigure(0, weight=1)

        self.logs_title = ctk.CTkLabel(self.logs_card, text="Details")
        self.logs_title.grid(row=0, column=0, padx=16, pady=(12, 8), sticky="w")

        self.log_box = ctk.CTkTextbox(self.logs_card, height=180)
        self.log_box.grid(row=1, column=0, padx=16, pady=(0, 16), sticky="ew")
        self.log_box.configure(state="disabled")

        set_log_handler("load_data", self.append_log)
        set_log_handler("autocorrection", self.append_log)
        set_log_handler("grading", self.append_log)

    def _make_progress_label(self, text: str, row: int) -> None:
        label = ctk.CTkLabel(self.progress_card, text=text)
        label.grid(row=row, column=0, padx=(16, 8), pady=4, sticky="w")

    def _make_value_label(self, row: int, value: str) -> ctk.CTkLabel:
        label = ctk.CTkLabel(self.progress_card, text=value, font=("Arial", 14, "bold"))
        label.grid(row=row, column=1, padx=(0, 16), pady=4, sticky="w")
        return label

    def append_log(self, message: str) -> None:
        if self.log_box is None:
            return

        line = self.format_log_line(message)
        self.after(0, lambda: self._append_log_ui(line))

    def _append_log_ui(self, line: str) -> None:
        if self.log_box is None:
            return

        self.log_box.configure(state="normal")
        self.log_box.insert("end", line)
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def clear_logs(self) -> None:
        if self.log_box is None:
            return

        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def choose_raw_folder(self) -> None:
        folder = self.choose_directory(self.raw_entry.get(), RAW_DATA_DIR)
        self.set_entry_value(self.raw_entry, folder)
        self.refresh_weeks()

    def choose_processed_folder(self) -> None:
        folder = self.choose_directory(self.processed_entry.get(), PROCESSED_DATA_DIR)
        self.set_entry_value(self.processed_entry, folder)

    def choose_corrected_folder(self) -> None:
        folder = self.choose_directory(self.corrected_entry.get(), CORRECTED_CODE_DIR)
        self.set_entry_value(self.corrected_entry, folder)

    def choose_grade_folder(self) -> None:
        folder = self.choose_directory(self.grade_entry.get(), GRADE_DIR)
        self.set_entry_value(self.grade_entry, folder)

    def refresh_weeks(self) -> None:
        for widget in self.week_scroll.winfo_children():
            widget.destroy()

        self.week_vars.clear()
        self.week_checkboxes.clear()
        self.week_text_vars.clear()
        self.week_checked_vars.clear()

        raw_dir = Path(self.raw_entry.get()) if self.raw_entry.get() else RAW_DATA_DIR
        processed_dir = Path(self.processed_entry.get()) if self.processed_entry.get() else PROCESSED_DATA_DIR
        week_names = self.backend.get_runnable_week_names(raw_dir, processed_dir)

        if not week_names:
            empty_label = ctk.CTkLabel(self.week_scroll, text="No week folders found.")
            empty_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")
            return

        for row, week_name in enumerate(week_names):
            checked_var = ctk.BooleanVar(value=True)
            text_var = ctk.StringVar(value=week_name)

            checkbox = ctk.CTkCheckBox(
                self.week_scroll,
                textvariable=text_var,
                variable=checked_var,
            )
            checkbox.grid(row=row, column=0, padx=8, pady=4, sticky="w")

            self.week_vars[week_name] = checked_var
            self.week_checkboxes.append(checkbox)
            self.week_text_vars.append(text_var)
            self.week_checked_vars.append(checked_var)

    def rename_weeks(self, new_week_names: list[str]) -> None:
        if len(new_week_names) != len(self.week_checkboxes):
            self.refresh_weeks()
            return

        old_checked_states = [var.get() for var in self.week_checked_vars]
        self.week_vars.clear()

        for i, new_name in enumerate(new_week_names):
            self.week_text_vars[i].set(new_name)
            self.week_checked_vars[i].set(old_checked_states[i])
            self.week_vars[new_name] = self.week_checked_vars[i]

    def start_run(self) -> None:
        if self._is_running:
            return

        config = RunConfig(
            raw_dir=Path(self.raw_entry.get()),
            processed_dir=Path(self.processed_entry.get()),
            corrected_dir=Path(self.corrected_entry.get()),
            grade_dir=Path(self.grade_entry.get()),
            run_autocorrection=self.run_autocorrection_var.get(),
            selected_week_names=[
                week_name
                for week_name, var in self.week_vars.items()
                if var.get()
            ],
        )

        self._set_running_state(True)
        self.clear_logs()
        self.status_value.configure(text="Running")
        self.week_value.configure(text="-")
        self.progress_value.configure(text="0 / 0")
        self.failure_value.configure(text="0")
        self.progress_bar.set(0)

        worker = threading.Thread(
            target=self._run_batch_worker,
            args=(config,),
            daemon=True,
        )
        worker.start()

    def _run_batch_worker(self, config: RunConfig) -> None:
        try:
            result = self.backend.run_grading_batch(
                config,
                on_progress=self.handle_progress,
            )
            self.after(0, lambda: self.finish_run(result))
        except Exception as exc:
            self.append_log(f"Run failed: {exc}")
            self.after(0, lambda: self._set_running_state(False))

    def handle_progress(self, update: ProgressUpdate) -> None:
        self.after(0, lambda: self._apply_progress(update))

    def _apply_progress(self, update: ProgressUpdate) -> None:
        status_text = update.message or update.stage
        self.status_value.configure(text=status_text)
        self.week_value.configure(text=update.week_name or "-")
        self.progress_value.configure(text=f"{update.completed_weeks} / {update.total_weeks}")
        self.failure_value.configure(text=str(update.failures))

        if update.total_weeks > 0:
            self.progress_bar.set(update.completed_weeks / update.total_weeks)
        else:
            self.progress_bar.set(0)

    def finish_run(self, result: BatchRunResult) -> None:
        self._set_running_state(False)
        self.on_finished(result)

    def _set_running_state(self, is_running: bool) -> None:
        self._is_running = is_running
        state: Literal["disabled", "normal"] = "disabled" if is_running else "normal"

        self.start_button.configure(state=state)
        self.raw_browse_button.configure(state=state)
        self.processed_browse_button.configure(state=state)
        self.corrected_browse_button.configure(state=state)
        self.grade_browse_button.configure(state=state)
        self.run_autocorrection_checkbox.configure(state=state)

        for widget in self.week_scroll.winfo_children():
            if isinstance(widget, STATEFUL_WIDGETS):
                widget.configure(state=state)
# endregion


# region table view
class TableView(ctk.CTkFrame):
    def __init__(self, parent) -> None:
        super().__init__(parent)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", rowheight=28)

        self.tree = ttk.Treeview(self, show="headings")
        self.tree.grid(row=0, column=0, sticky="nsew")

        self.v_scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.v_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=self.v_scroll.set)

        self.h_scroll = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.h_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=self.h_scroll.set)

    def set_table(self, columns: list[str], rows: list[list[str]]) -> None:
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns

        for column in columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=140, anchor="center", stretch=True)

        for row in rows:
            self.tree.insert("", "end", values=row)
# endregion


# region results page
class ResultsPage(BasePage):
    def __init__(self, parent, backend: AppBackend) -> None:
        super().__init__(parent, backend)
        self.result: BatchRunResult | None = None
        self.week_map: dict[str, WeekResult] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self.title = ctk.CTkLabel(self, text="Results", font=("Arial", 28, "bold"))
        self.title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.summary = ctk.CTkFrame(self)
        self.summary.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        for column in range(4):
            self.summary.grid_columnconfigure(column, weight=1)

        self.week_count_card = self._make_summary_card(0, "Weeks", "0")
        self.submission_count_card = self._make_summary_card(1, "Submissions", "0")
        self.average_card = self._make_summary_card(2, "Average score", "-")
        self.failure_card = self._make_summary_card(3, "Failures", "0")

        self.toolbar = ctk.CTkFrame(self)
        self.toolbar.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.toolbar.grid_columnconfigure(3, weight=1)

        self.week_menu = ctk.CTkOptionMenu(self.toolbar, values=["No results yet"], command=self.change_week)
        self.week_menu.grid(row=0, column=0, padx=16, pady=12, sticky="w")

        self.open_excel_button = ctk.CTkButton(
            self.toolbar,
            text="Open Excel",
            command=self.open_selected_excel,
            state="disabled",
        )
        self.open_excel_button.grid(row=0, column=1, padx=8, pady=12)

        self.open_folder_button = ctk.CTkButton(
            self.toolbar,
            text="Open score folder",
            command=self.open_score_folder,
            state="disabled",
        )
        self.open_folder_button.grid(row=0, column=2, padx=8, pady=12)

        self.table = TableView(self)
        self.table.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.table.set_table(["submitter"], [])

    def _make_summary_card(self, column: int, label_text: str, value_text: str) -> ctk.CTkLabel:
        card = ctk.CTkFrame(self.summary)
        card.grid(row=0, column=column, padx=8, pady=8, sticky="ew")
        label = ctk.CTkLabel(card, text=label_text)
        label.grid(row=0, column=0, padx=12, pady=(12, 4), sticky="w")
        value = ctk.CTkLabel(card, text=value_text, font=("Arial", 22, "bold"))
        value.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="w")
        return value

    def populate(self, result: BatchRunResult) -> None:
        self.result = result
        self.week_map = {week_result.week_name: week_result for week_result in result.week_results}

        week_names = list(self.week_map.keys())
        if not week_names:
            self.week_menu.configure(values=["No results yet"])
            self.week_menu.set("No results yet")
            self.open_excel_button.configure(state="disabled")
            self.open_folder_button.configure(state="disabled")
            self.table.set_table(["submitter"], [])
            return

        self.week_menu.configure(values=week_names)
        self.week_menu.set(week_names[0])
        self.open_excel_button.configure(state="normal")
        self.open_folder_button.configure(state="normal")

        total_submissions = sum(len(week_result.score_df.index) for week_result in result.week_results)
        average_score = self._calc_average_score(result)
        failure_count = len(result.failures)

        self.week_count_card.configure(text=str(len(result.week_results)))
        self.submission_count_card.configure(text=str(total_submissions))
        self.average_card.configure(text=average_score)
        self.failure_card.configure(text=str(failure_count))

        self.show_week(week_names[0])

    def _calc_average_score(self, result: BatchRunResult) -> str:
        values = []
        for week_result in result.week_results:
            flattened = week_result.score_df.to_numpy().flatten().tolist()
            for value in flattened:
                if value == value and value is not None:
                    values.append(float(value))

        if not values:
            return "-"

        return f"{sum(values) / len(values):.3f}"

    def change_week(self, week_name: str) -> None:
        self.show_week(week_name)

    def show_week(self, week_name: str) -> None:
        week_result = self.week_map.get(week_name)
        if week_result is None:
            return

        score_df = week_result.score_df.fillna("")
        columns = ["submitter"] + [str(column) for column in score_df.columns]
        rows: list[list[str]] = []

        for submitter, row in score_df.iterrows():
            values = [str(submitter)] + [str(value) for value in row.tolist()]
            rows.append(values)

        self.table.set_table(columns, rows)

    def open_selected_excel(self) -> None:
        if self.result is None:
            return

        week_name = self.week_menu.get()
        week_result = self.week_map.get(week_name)
        if week_result is None:
            return

        open_in_file_manager(week_result.output_path)

    def open_score_folder(self) -> None:
        if self.result is None:
            return

        open_in_file_manager(self.result.config.grade_dir)
# endregion


# region failure page
class FailuresPage(BasePage):
    def __init__(self, parent, backend: AppBackend) -> None:
        super().__init__(parent, backend)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.title = ctk.CTkLabel(self, text="Failures", font=("Arial", 28, "bold"))
        self.title.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.table = TableView(self)
        self.table.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="nsew")
        self.table.set_table(["week", "submitter", "problem", "stage", "reason", "path"], [])

    def populate(self, failures: list[FailureItem]) -> None:
        rows = [
            [
                failure.week_name,
                failure.submitter,
                failure.problem_label,
                failure.stage,
                failure.reason,
                failure.path,
            ]
            for failure in failures
        ]
        self.table.set_table(["week", "submitter", "problem", "stage", "reason", "path"], rows)


class App:
    def __init__(self, backend: AppBackend) -> None:
        self.backend = backend
        self.window = Window("CPP Autograder", 1100, 720)
        self.window.app.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.window.app.grid_columnconfigure(0, weight=0, minsize=180)
        self.window.app.grid_columnconfigure(1, weight=1)
        self.window.app.grid_rowconfigure(0, weight=1)

        self.navigation = NavigationFrame(self.window.app, self.show_page)
        self.navigation.add_page(1, "run", "Run")
        self.navigation.add_page(2, "results", "Results")
        self.navigation.add_page(3, "failures", "Failures")

        self.content = ContentFrame(self.window.app)

        self.results_page = ResultsPage(self.content._frame, backend)
        self.failures_page = FailuresPage(self.content._frame, backend)
        self.run_page = RunPage(self.content._frame, backend, self.handle_run_finished)

        self.content.add_page("run", self.run_page)
        self.content.add_page("results", self.results_page)
        self.content.add_page("failures", self.failures_page)

        self.show_page("run")

    def handle_run_finished(self, result: BatchRunResult) -> None:
        self.backend.state.last_run_result = result
        self.results_page.populate(result)
        self.failures_page.populate(result.failures)
        self.show_page("results")

    def show_page(self, page_name: str) -> None:
        self.navigation.set_active(page_name)
        self.content.show_page(page_name)

    def run(self) -> None:
        self.window.show()

    def on_closing(self) -> None:
        self.window.app.destroy()
