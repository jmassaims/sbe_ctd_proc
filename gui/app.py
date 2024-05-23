from multiprocessing import Process, Queue, JoinableQueue
import queue

from tkinter import filedialog, Label, messagebox
import customtkinter

from config import CONFIG
from manager import start_manager

# FIXME not safe to change config while process is running.
#   not sure how Python synchronizes changes to module objects like CONFIG betweens processes.

def select_raw_directory(raw_path_label):
    """Get the raw directory with button click (default assigned to local directory)"""
    print("Raw Directory Button clicked!")
    raw_directory_selected = filedialog.askdirectory()
    CONFIG["RAW_PATH"] = raw_directory_selected
    raw_path_label.configure(text=CONFIG["RAW_PATH"])


def select_processing_directory(PROCESSING_PATH_label):
    """Get the processing directory with button click (default assigned to local directory)"""
    print("Processing Directory Button clicked!")
    processing_directory_selected = filedialog.askdirectory()
    print(processing_directory_selected)
    CONFIG["PROCESSING_PATH"] = (processing_directory_selected)
    PROCESSING_PATH_label.configure(text=CONFIG["PROCESSING_PATH"])


def select_config_directory(config_path_label):
    """Get the config directory with button click (default assigned to local directory)"""
    print("Configuration Directory Button clicked!")
    config_directory_selected = filedialog.askdirectory()
    CONFIG["CTD_CONFIG_PATH"] = config_directory_selected
    config_path_label.configure(text=CONFIG["CTD_CONFIG_PATH"])


def select_database_directory(database_path_label):
    """Get the database directory with button click (default assigned to local directory)"""
    print("Database Directory Button clicked!")
    database_directory_selected = filedialog.askdirectory()
    database_path = database_directory_selected
    CONFIG["CTD_DATABASE_PATH"] = database_directory_selected
    database_path_label.configure(text=CONFIG["CTD_DATABASE_PATH"])

class App:
    def __init__(self) -> None:
         self.proc = None
         self.build()

    def start_process(self):
        if self.proc is not None and self.proc.is_alive():
            raise Exception("existing process is running")

        # for messages sent by worker processes.
        self.recv = recv = Queue()

        # our recv is the other process' send
        self.proc = Process(target=start_manager, args=(recv,))
        self.proc.start()

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
        print("Stopped processing.")
        print("Temporary files may remain in the raw directory due to cancelled processing.")

        # TODO cleanup files on terminate
        #  print(file_name)
        # print(base_file_name)
        #thought process here to check if these two are equal and if not, delete file_name file

    def process_events(self):
        try:
            while True:
                msg = self.recv.get(block=False)
                self.process_msg(msg)

        except queue.Empty:
            pass

        self._after_id = self.window.after_idle(self.process_events)

    def process_msg(self, msg):
        print("got msg", msg)
        label = msg[0]

        if label == "begin":
            self.progressbar.set(0)
            self.num_to_process = msg[1]
        elif label == "start":
            # TODO display name
            name = msg[1]
        elif label == "finish":
            name = msg[1]
            i = msg[2]
            self.progressbar.set(i / self.num_to_process)
        elif label == "done":
            self.stop_process(2_000)
        elif label == "usermsg":
            messagebox.showinfo("CTD Processing Message", msg[1])
        elif label == "error":
            messagebox.showerror("CTD Processing Error", msg[1])


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

        self.build_config(window)

        # process stage 1 button
        process_button = customtkinter.CTkButton(
            window, text="Process Data", font=("Arial", 30, 'bold'), fg_color="#5D892B", hover_color="#334B18",
            command=lambda: self.start_process()
        ).pack(pady=(10,10))
        stage1_path_label = customtkinter.CTkLabel(window, text="Process data from .hex to BinDown stage", font=CONFIG["LABEL_FONTS"])
        stage1_path_label.pack(pady=(5, 25))

        # Stop process button
        stop_button = customtkinter.CTkButton(
            window, text="Stop", font=("Arial", 20, 'bold'), fg_color="#AC3535", hover_color="#621E1E",
            command=lambda: self.stop_process()
        ).pack(pady=(0,20))

        self.progressbar = customtkinter.CTkProgressBar(window)
        self.progressbar.pack()
        self.progressbar.set(0)

    def build_config(self, window):
        # raw directory button
        raw_directory_button = customtkinter.CTkButton(
            window, text="Select Raw Directory", font=CONFIG["LABEL_FONTS"],
            command=lambda: select_raw_directory(raw_path_label)
        ).pack()
        raw_path_label = customtkinter.CTkLabel(window, text=CONFIG["RAW_PATH"], font=CONFIG["LABEL_FONTS"])
        raw_path_label.pack(pady=(5, 25))

        # processing directory button
        processing_directory_button = customtkinter.CTkButton(
            window, text="Select processing Directory", font=CONFIG["LABEL_FONTS"],
            command=lambda: select_processing_directory(PROCESSING_PATH_label)
        ).pack()
        PROCESSING_PATH_label = customtkinter.CTkLabel(window, text=CONFIG["PROCESSING_PATH"], font=CONFIG["LABEL_FONTS"])
        PROCESSING_PATH_label.pack(pady=(5, 25))

        # configuration directory button
        config_directory_button = customtkinter.CTkButton(
            window, text="Select Configuration Directory", font=CONFIG["LABEL_FONTS"],
            command=lambda: select_config_directory(config_path_label)
        ).pack()
        config_path_label = customtkinter.CTkLabel(window, text=CONFIG["CTD_CONFIG_PATH"], font=CONFIG["LABEL_FONTS"])
        config_path_label.pack(pady=(5, 25))

        # database directory button
        database_directory_button = customtkinter.CTkButton(
            window, text="Select Database Directory", font=CONFIG["LABEL_FONTS"],
            command=lambda: select_database_directory(database_path_label)
        ).pack()
        database_path_label = customtkinter.CTkLabel(window, text=CONFIG["DATABASE_MDB_FILE"], font=CONFIG["LABEL_FONTS"])
        database_path_label.pack(pady=(5, 25))

    def start(self):
        "Start the tkinter event loop"
        self.window.mainloop()
