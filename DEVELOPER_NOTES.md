# Developer Notes

## App and Processing

The app is written with [Tkinter](https://tkdocs.com/tutorial/index.html) and [Custom Tkinter](https://customtkinter.tomschimansky.com/documentation/widgets).
When the start processing button is clicked, a [Process](https://docs.python.org/3/library/multiprocessing.html#the-process-class)
launches, which creates a `Manager`
instance and begins processing files. Communication between the processes is done via tuple
messages sent through a `Queue`. Messages are processed via the Tkinter [eventloop](https://tkdocs.com/tutorial/eventloop.html)
using `after`, see `App.process_events`.

### Manager

The `Manager` is in charge of scanning directories and file tracking. A `Manager` instance
is created within the sub `Process`; it iterates through files, calling `process_hex_file`.

## Principals

* Different concerns should be organized in separate files.
* Error-prone code like parsing should have unit tests.
* App concerns should be separated as much as possible and not pollute files like `process.py`.
The code should not make it difficult to process in a headless mode if desired.
Though we need to send messages to the App, this should be thought of as abstract reporting.

## General Notes

[Path](https://docs.python.org/3/library/pathlib.html#basic-use) is used throughout the code.
There is a trivial performance cost versus `os.path` and string paths since it creates more
objects, but `Path` simplifies code and is more convenient to work with.

## Future Ideas

As mentioned in the `Process` documentation,
[ProcessPoolExecutor](https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ProcessPoolExecutor)
is a more modern way of managing worker processes. The `Manager` could use this instead of
everything executing within one `Process`. However, this would complicate things and may
only be worth the effort if we want to process multiple file simultaneously.
