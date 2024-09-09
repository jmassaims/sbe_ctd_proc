
def start_gui():
    # avoid circular import error with some launches by importing inside function.
    from .app import App

    app = App()
    app.start()

if __name__ == "__main__":
    start_gui()