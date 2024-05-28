from multiprocessing import Process, Queue, JoinableQueue
import queue

from tkinter import filedialog, Label, messagebox
import customtkinter

from config import CONFIG
from manager import start_manager

from .processing_panel import ProcessingPanel
from .config_panel import ConfigPanel

class App:
    def __init__(self) -> None:
         self.proc = None
         self.build()

    def start_process(self):
        if self.proc is not None and self.proc.is_alive():
            raise Exception("existing process is running")

        # for messages sent by worker processes.
        self.recv = Queue()
        self.send = Queue()

        # our recv is the other process' send
        self.proc = Process(target=start_manager, args=(self.recv, self.send))
        self.proc.start()

        self.processing_panel.set_processing_state(True)

        self._after_id = self.window.after_idle(self.process_events)

    # Terminate the process
    def stop_process(self, join_timeout=None):
        """Stop processing with a button click"""

        self.window.after_cancel(self._after_id)

        if self.proc is None:
            print("No processing started.")
            return

        if join_timeout is not None:
            self.proc.join(join_timeout)

        if self.proc.is_alive():
            print("Terminating process")
            self.proc.terminate()  # sends a SIGTERM

        self.proc = None

        self.processing_panel.set_processing_state(False)

        print("Stopped processing.")
        print("Temporary files may remain in the raw directory due to cancelled processing.")

        # TODO cleanup files on terminate
        #  print(file_name)
        # print(base_file_name)
        #thought process here to check if these two are equal and if not, delete file_name file

    def process_events(self):
        """Process events from subprocess and monitor if it's alive"""
        try:
            while True:
                msg = self.recv.get(block=False)
                self.process_msg(msg)

        except queue.Empty:
            pass

        if self.proc is not None:
            if self.proc.is_alive():
                # schedule next process_events in 100ms
                self._after_id = self.window.after(100, self.process_events)
            else:
                # cleanup process state
                self.stop_process()

    def process_msg(self, msg):
        print("msg:", msg)
        label = msg[0]

        if label == "process_step":
            self.processing_panel.set_step(msg[1], msg[2], msg[3])
        elif label == "begin":
            self.processing_panel.reset_progress(msg[1])
        elif label == "start":
            _, name, i, num_pending = msg
            self.processing_panel.start_file(name, i, num_pending)
        elif label == "hex_info":
            self.processing_panel.set_file_info(msg[1], msg[2])
        elif label == "finish":
            _, name, i, num_processed = msg
            self.processing_panel.finished_file(name, i, num_processed)
        elif label == "done":
            self.stop_process(2_000)
        elif label == "usermsg":
            messagebox.showinfo("CTD Processing Message", msg[1])
        elif label == "file_error":
            self.show_file_error(msg[1], msg[2])
        elif label == "error":
            messagebox.showerror(
                parent=self.window,
                title="CTD Processing Error",
                message="Processing stopped by error.",
                detail=msg[1])
        else:
            print("WARNING: unknown message", msg)


    def build(self):
        PROCESSING_PATH = CONFIG["PROCESSING_PATH"]
        # Create a tkinter window
        window = customtkinter.CTk()  # create CTk window like you do with the Tk window
        self.window = window

        window.geometry("400x550")
        window.grid_columnconfigure(0, weight=1)
        customtkinter.set_appearance_mode("dark")  # Modes: system (default), light, dark
        customtkinter.set_default_color_theme(
            "blue"
        )  # Themes: blue (default), dark-blue, green

        window.title("Seabird CTD Processor")

        self.tabview = tabview = customtkinter.CTkTabview(window, command=self.on_tab_change)
        tabview.pack(fill="both", expand=True)
        # CTkFrame
        config_tab = tabview.add("Configure")
        processing_tab = tabview.add("Processing")

        self.config_panel = ConfigPanel(config_tab)
        self.processing_panel = ProcessingPanel(processing_tab, self)

    def on_tab_change(self):
        current = self.tabview.get()
        if current == "Processing":
            self.processing_panel.prepare()

    def start(self):
        "Start the tkinter event loop"
        self.window.mainloop()

    def show_file_error(self, file_name: str, error: str):
        response = messagebox.showerror(
            parent=self.window,
            title="CTD Processing Error",
            message=f"Error processing {file_name}",
            detail=error,
            type=messagebox.ABORTRETRYIGNORE)

        self.send.put((response, file_name))
