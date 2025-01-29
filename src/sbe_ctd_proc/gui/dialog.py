import customtkinter

# TODO ideally this should specify parent=window (of the App) to prevent the extra
#  window from opening. But this requires reworking code to communicate to the App
#  through the send/recv Queues.
def request_latitude(name) -> float:
    "Request latitute from the user in a new dialog"
    derive_latitude = customtkinter.CTkInputDialog(
        text="What is the latitude for: " + name + "?",
        title="Derive Latitude Input",
    ).get_input()

    if derive_latitude is None:
        raise ValueError("No latitude provided")

    return float(derive_latitude)
