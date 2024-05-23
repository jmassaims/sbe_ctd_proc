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
        self.manager = Manager()

        self.build(parent)

    def build(self, parent):
        button_style = dict(fg_color="transparent")
        row = customtkinter.CTkFrame(self.parent)
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

        # process stage 1 button
        process_button = customtkinter.CTkButton(
            parent, text="Process Data", font=("Arial", 30, 'bold'), fg_color="#5D892B", hover_color="#334B18",
            command=lambda: self.app.start_process()
        ).pack(pady=(10,10))
        stage1_path_label = customtkinter.CTkLabel(parent, text="Process data from .hex to BinDown stage", font=CONFIG["LABEL_FONTS"])
        stage1_path_label.pack(pady=(5, 25))

        # Stop process button
        stop_button = customtkinter.CTkButton(
            parent, text="Stop", font=("Arial", 20, 'bold'), fg_color="#AC3535", hover_color="#621E1E",
            command=lambda: self.stop_process()
        ).pack(pady=(0,20))

        self.progressbar = customtkinter.CTkProgressBar(parent)
        self.progressbar.pack()
        self.progressbar.set(0)

    def prepare(self):
        """re-scan directories and update button labels"""
        mgr = self.manager
        print("preparing, scanning directories.")
        mgr.scan_dirs()
        self.pending_button.configure(text=f"{len(mgr.pending)}/{mgr.hex_count} Pending")

        if mgr.processing:
            # indicate to user that stuff in processing
            self.processing_button.configure(text=f"{len(mgr.processing)} Processing?", fg_color="orange")
        else:
            self.processing_button.configure(text="Processing", fg_color="transparent")

        self.processed_button.configure(text=f"{len(mgr.processed)} Processed")


    def reset_progress(self, num_to_process: int):
        self.num_to_process = num_to_process
        self.progressbar.set(0)

    def finished_file(self, name, num):
        self.progressbar.set(num / self.num_to_process)