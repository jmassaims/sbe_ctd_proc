import multiprocessing

from tkinter import filedialog, Label
import customtkinter

from config import CONFIG
from process import process

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


# FIXME move to methods

# Start the process 1
def startStg1():
    global multiprocessing_process
    multiprocessing_process = multiprocessing.Process(target=process, args=())
    multiprocessing_process.start()


# Terminate the process
def stop():
    """Stop processing with a button click"""
    try:
        multiprocessing_process.terminate()  # sends a SIGTERM
        print("Stopped processing.")
        print("Temporary files may remain in the raw directory due to cancelled processing.")
      #  print(file_name)
      #  print(base_file_name)
        #thought process here to check if these two are equal and if not, delete file_name file
    except NameError:
        print("No processing started.")

class App:
    def __init__(self) -> None:
         self.build()

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
        # Set the window title
        window.title("Seabird CTD Processor")

        # raw directory button
        raw_directory_button = customtkinter.CTkButton(
            window, text="Select Raw Directory", font=CONFIG["LABEL_FONTS"], command=lambda: select_raw_directory(raw_path_label)
        ).pack()
        raw_path_label = customtkinter.CTkLabel(window, text=CONFIG["RAW_PATH"], font=CONFIG["LABEL_FONTS"])
        raw_path_label.pack(pady=(5, 25))

        # processing directory button
        processing_directory_button = customtkinter.CTkButton(
            window, text="Select processing Directory", font=CONFIG["LABEL_FONTS"], command=lambda: select_processing_directory(PROCESSING_PATH_label)
        ).pack()
        PROCESSING_PATH_label = customtkinter.CTkLabel(window, text=CONFIG["PROCESSING_PATH"], font=CONFIG["LABEL_FONTS"])
        PROCESSING_PATH_label.pack(pady=(5, 25))

        # configuration directory button
        config_directory_button = customtkinter.CTkButton(
            window, text="Select Configuration Directory", font=CONFIG["LABEL_FONTS"], command=lambda: select_config_directory(config_path_label)
        ).pack()
        config_path_label = customtkinter.CTkLabel(window, text=CONFIG["CTD_CONFIG_PATH"], font=CONFIG["LABEL_FONTS"])
        config_path_label.pack(pady=(5, 25))

        # database directory button
        database_directory_button = customtkinter.CTkButton(
            window, text="Select Database Directory", font=CONFIG["LABEL_FONTS"], command=lambda: select_database_directory(database_path_label)
        ).pack()
        database_path_label = customtkinter.CTkLabel(window, text=CONFIG["CTD_DATABASE_PATH"], font=CONFIG["LABEL_FONTS"])
        database_path_label.pack(pady=(5, 25))

        # process stage 1 button
        process_button = customtkinter.CTkButton(
            window, text="Process Data", font=("Arial", 30, 'bold'), fg_color="#5D892B", hover_color="#334B18",
            command=lambda: startStg1()
        ).pack(pady=(10,10))
        stage1_path_label = customtkinter.CTkLabel(window, text="Process data from .hex to BinDown stage", font=CONFIG["LABEL_FONTS"])
        stage1_path_label.pack(pady=(5, 25))


        # stop button
        stop_button = customtkinter.CTkButton(
            window, text="Stop", font=("Arial", 20, 'bold'), fg_color="#AC3535", hover_color="#621E1E", command=stop
        ).pack(pady=(0,20))

    def start(self):
        "Start the tkinter event loop"
        self.window.mainloop()
