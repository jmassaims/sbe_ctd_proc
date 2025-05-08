# Technical Overview

High level overview of technical concepts.

## Manager

The `Manager` class scans for files and tracks their state; it also processes files
and communicates the state of processing to the NiceGUI app via messages sent over the
send/recv Queues.

Multiple instances of `Manager` are created during the life of the app. One instance
is used to display the file list in the app. Another instance is created when files
start processing (see ProcessingState section).

## ProcessingState

The `PROC_STATE` singleton is a service used by the app to get the current processing
state and start processing files. NiceGUI widgets directly reference `ProcessingState`
attributes and bind their values.

When the user chooses to process files, a new instance of `Manager` is created within a
separate thread (using NiceGUI's `run.io_bound`), see `ProcessingState.start_processing`.
This manager instance is initialized with full configuration and inter-process communication
is established using send/recv Queues (see `start_manager`).

Messages received from processing are handled by the `handle_msg_*` methods of
`ProcessingState`, which may update attributes the UI is bound to.

## Status

The status of a CTDfile goes from `raw` to `processing` to `approved`. (see `FileStatus`)
This is determined by scanning the corresponding directories. The "base name" of the hex
file (file name without extension) is used for processing/approved directory names and is the
primary way CTD files are identified in code. Files that are both in processing and approved
directories is ambiguous and must be manually fixed; the app warns about this situation.
For more information, see [Process Flow](./process_flow.md).

## Config Service

`CONFIG` is a singleton instance of the `Config` service, which processes and validates
the app configuration. It manages and provides access to other configured services like
 the database and latitude spreadsheet.

State may be cached in these services, e.g. the latitude spreadsheet Pandas dataframe.
When file processing is started, `Config.refresh_services` is called to reload such state.

### Future Config Work

When Config UI is developed, will need to support refreshing `CONFIG` completely.
Also, note that `CONFIG` is shared between threads and may not be thread-safe.
For example `DataFrame` in `LatitudeSpreadsheet` is not thread-safe; though probably not a
issue since we don't mutate it and it's only used by the processing thread.
Still, it would be more robust to have separate `Config` instances per thread.
