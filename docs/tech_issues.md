# Technical Issues

More information on technical issues mentioned in the README.

## Python 3.13 build problems

Building with Python 3.13 is unreliable. On a system where Python 3.12 works,
when switching to 3.13 we see this error:

> error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/

Python 3.13 seems to require a newer version of C++ build tools?
After installing C++ build tools, the app did work on one system.
However, on another system, we saw other build errors:

> error: command 'C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools\\VC\\Tools\\MSVC\\14.43.34808\\bin\\HostX86\\x86\\link.exe' failed with exit code 1120

> LIBCMT.lib(dll_dllmain.obj) : error LNK2001: unresolved external symbol __except_handler4

These errors were resolved by using Python 3.12, so we've decided to pin that version
in this project using `uv python pin 3.12` (updates _.python-version_).

## Old Status Names

Status values were renamed. Some of these old names may be left and should be changed
to the new status names for consistency, see [Process Flow](./process_flow.md).
* pending -> raw
* processed -> processing
* done/destination -> approved

## Config Reload

`config.toml` reload on change is implemented, but this needs more testing and work. There
may still be state loaded from config in some objects that is not being reloaded correctly.

# Concurrency

Since this is a single user app that generally only has one worker thread, there
 shouldn't be too many concurrency concerns. However, it can be an issue.

`AuditLog` should be threadsafe with its internal lock.
One `CONFIG.audit_log` instance is shared by throughout the app and in multiple threads.
You could have files processing and user approving at same time, this lock should
prevent concurrency problems in this situation.
