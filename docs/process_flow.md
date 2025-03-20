# Process Flow

_Work in progress._

## Status

The main status a file goes through is `raw` -> `processing` -> `approved`

TODOC all status, CTDFile holds status

* raw
* processing
* approved
* error

## Scan Raw

The app scans the raw, processing, and approved directories to determine file status
and lists them in the app.

## Selection

By default, all raw hex files that are not in the processing or approved directories
will be processed. The user may also make a selection of files to process/reprocess.

## CTD file Processing

Prepare the CTD file for processing and execute all Seabird steps using the local psa files.
See `process_hex_file` function.

### 1. Setup processing directory

Create processing directory for the file.

This is created even if there are errors such as not parsing cast date or finding psa file.
This is so the user may fix issues within the directory to allow processing to continue.
For example, if cast date failed to parse, the user may still determine the correct psa
file and copy it to the processing directory; then re-process the file.

The app should display the errors that need to be fixed to allow a file to process.

### 2. Extract and lookup information

Parse cast date and other information in hex file. Lookup latitude using the configured
method. (This is stored in `CTDFile.latitude`).

### 3. Copy psa/xmlcon files

Lookup psa & xmlcon files in ctd _config_ directory and copy them to the processing
 directory (if they don't already exist).

_Note: this requires cast date, so will fail if cast date not found._

### 4. Modify psa files

Modify the local psa files in the processing directory, see `rewrite_psa_file`.
* set `<Latitude>` `value` attribute to file's latitude.
* clear `<NameAppend>` `value` attribute.

### 5. Convert hex to cnv

Convert the hex file to `*C.cnv` using `DatCnvW.exe`

### 6. Execute Seabird processing steps

Execute all of the Seabird programs in order. The output cnv of previous program
is input into the next.
### 7. Audit log

Write a row to the audit log.

## Processing State & Analysis

The file is now waiting in a `processing` state for approval by the user. If errors
were encountered, the file may show `error`

The user may view data checks and charts in the app.

## Reprocess

The user may reprocess the file after fixing issues. This runs the file through
all Seabird steps again. Examples of typical fixes are:
* edit the local psa file
* fix information in the database/spreadsheet
* fix issues in this code


## Approve

When approved in the app, the directory is moved to the approved directory.
