from datetime import datetime
import os
import tkinter as tk
import customtkinter

from config import CONFIG
from manager import Manager

def open_dir(path):
    os.startfile(path)


class ProcessingPanel():

    manager: Manager
    """Manager instance for previewing what processing will do.
    Note the launched Process has its own instance."""

    def __init__(self, parent, app) -> None:
        self.parent = parent
        self.app = app
        self.build(parent)

    def build(self, parent):
        window = self.app.window

        button_style = dict(fg_color="transparent")
        row = customtkinter.CTkFrame(parent)
        row.pack(pady=16)

        pending_button = customtkinter.CTkButton(row, text="Pending", **button_style,
                                                 command=lambda: open_dir(self.manager.raw_path))
        pending_button.pack(side=tk.LEFT)
        self.pending_button = pending_button

        processing_button = customtkinter.CTkButton(row, text="Processing", **button_style,
                                                    command=lambda: open_dir(self.manager.processing_dir))
        processing_button.pack(side=tk.LEFT)
        self.processing_button = processing_button

        processed_button = customtkinter.CTkButton(row, text="Processed", **button_style,
                                                   command=lambda: open_dir(self.manager.destination_dir))
        processed_button.pack(side=tk.LEFT)
        self.processed_button = processed_button

        progress_row = customtkinter.CTkFrame(parent)
        progress_row.pack()

        self.progressbar = customtkinter.CTkProgressBar(progress_row)
        self.progressbar.pack(side=tk.LEFT)
        self.progressbar.set(0)

        # Stop process button
        self.stop_button = stop_button = customtkinter.CTkButton(
            progress_row, text="🟥", font=("Arial", 20, 'bold'), fg_color="transparent", text_color="#AC3535", hover_color="#621E1E", border_spacing=8,
            width=20, state=tk.DISABLED,
            command=self.app.stop_process
        )
        stop_button.pack(side=tk.LEFT, pady=(0, 0))

        self.start_frame = start_frame = customtkinter.CTkFrame(parent)
        start_frame.pack()

        self.start_button = start_button = customtkinter.CTkButton(
            start_frame, text="Process Data", font=("Arial", 30, 'bold'), fg_color="#5D892B", hover_color="#334B18",
            command=self.app.start_process
        )
        start_button.pack(pady=(10,10))

        stage1_path_label = customtkinter.CTkLabel(start_frame, text="Process data from .hex to BinDown stage", font=CONFIG["LABEL_FONTS"])
        stage1_path_label.pack(pady=(5, 25))

        self.info_frame = info_frame = customtkinter.CTkFrame(parent)
        info_frame.pack()

        self.file_label = file_label = customtkinter.CTkLabel(info_frame, text="")
        file_label.pack()

        self.info_label = customtkinter.CTkLabel(info_frame, text="")
        self.info_label.pack()

        self.step_label = customtkinter.CTkLabel(info_frame, text="")
        self.step_label.pack()

    def set_processing_state(self, processing: bool):
        """Change to or from the processing UI mode"""
        print("set_processing_state", processing)
        if processing:
            self.stop_button.configure(state=tk.NORMAL)
            # hide start UI
            self.start_frame.pack_forget()
            self.info_frame.pack()
        else:
            self.stop_button.configure(state=tk.DISABLED)
            self.prepare()
            self.info_frame.pack_forget()
            self.start_frame.pack()

    def prepare(self):
        """re-scan directories and update button labels.
        Note: called when switching to Processing tab"""
        # new Manager in case CONFIG changed.
        self.manager = mgr = Manager()
        print("preparing, scanning directories.")
        mgr.scan_dirs()
        self.pending_button.configure(text=f"{len(mgr.pending)}/{mgr.hex_count} Pending")
        self.reset_progress(len(mgr.pending))

        if mgr.processing:
            # indicate to user that stuff in processing
            self.processing_button.configure(text=f"{len(mgr.processing)} Processing?", fg_color="orange")
        else:
            self.processing_button.configure(text="Processing", fg_color="transparent")

        self.processed_button.configure(text=f"{len(mgr.processed)} Processed")

        # Clear file name and step
        self.file_label.configure(text="")

    def reset_progress(self, num_to_process: int):
        """reset the progress bar"""
        self.num_to_process = num_to_process
        self.progressbar.set(0)
        self.file_label.configure(text="")
        self.info_label.configure(text="")
        self.step_label.configure(text="")

    def start_file(self, name: str, num: int, num_pending: int):
        self.file_label.configure(text=name)
        self.pending_button.configure(text=f"{num_pending} Pending")
        # minus 1 since num is 1-based index
        self.file_progress_init = (num - 1) / self.num_to_process
        self.progressbar.set(self.file_progress_init)

    def finished_file(self, name: str, num: int, num_processed: int):
        self.progressbar.set(num / self.num_to_process)
        self.processed_button.configure(text=f"{num_processed} Processed")
        self.step_label.configure(text="")

    def set_step(self, name: str, step_num: int, num_steps: int):
        self.step_label.configure(text=name)

        # width of progressbar allocated to a file
        file_width = 1 / self.num_to_process

        progress = self.file_progress_init + (step_num / num_steps) * file_width
        self.progressbar.set(progress)

    def set_file_info(self, serial_number: str, cast_date: datetime):
        self.info_label.configure(text=f"Serial Number: {serial_number}  Cast Date: {cast_date}")
