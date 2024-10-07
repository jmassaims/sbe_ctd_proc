from tkinter import filedialog
import customtkinter

from ..config import CONFIG


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


class ConfigPanel:
    """UI to change configuration.
    Note that it's not safe to mutate CONFIG while process is running.
    """
    def __init__(self, parent) -> None:
        self.build(parent)

    def build(self, parent):
        # raw directory button
        raw_directory_button = customtkinter.CTkButton(
            parent, text="Select Raw Directory", font=CONFIG["LABEL_FONTS"],
            command=lambda: select_raw_directory(raw_path_label)
        ).pack()
        raw_path_label = customtkinter.CTkLabel(parent, text=CONFIG["RAW_PATH"], font=CONFIG["LABEL_FONTS"])
        raw_path_label.pack(pady=(5, 25))

        # processing directory button
        processing_directory_button = customtkinter.CTkButton(
            parent, text="Select processing Directory", font=CONFIG["LABEL_FONTS"],
            command=lambda: select_processing_directory(PROCESSING_PATH_label)
        ).pack()
        PROCESSING_PATH_label = customtkinter.CTkLabel(parent, text=CONFIG["PROCESSING_PATH"], font=CONFIG["LABEL_FONTS"])
        PROCESSING_PATH_label.pack(pady=(5, 25))

        # configuration directory button
        config_directory_button = customtkinter.CTkButton(
            parent, text="Select Configuration Directory", font=CONFIG["LABEL_FONTS"],
            command=lambda: select_config_directory(config_path_label)
        ).pack()
        config_path_label = customtkinter.CTkLabel(parent, text=CONFIG["CTD_CONFIG_PATH"], font=CONFIG["LABEL_FONTS"])
        config_path_label.pack(pady=(5, 25))

        # database directory button
        database_directory_button = customtkinter.CTkButton(
            parent, text="Select Database Directory", font=CONFIG["LABEL_FONTS"],
            command=lambda: select_database_directory(database_path_label)
        ).pack()
        database_path_label = customtkinter.CTkLabel(parent, text=CONFIG["DATABASE_MDB_FILE"], font=CONFIG["LABEL_FONTS"])
        database_path_label.pack(pady=(5, 25))
