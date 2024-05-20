import customtkinter

def request_latitude(name):
    "Request latitute from the user in a new dialog"
    derive_latitude = customtkinter.CTkInputDialog(
        text="What is the latitude for: " + name + "?",
        title="Derive Latitude Input",
    ).get_input()

    return derive_latitude
