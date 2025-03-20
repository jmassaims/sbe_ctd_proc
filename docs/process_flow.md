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

## Selection

By default, all raw hex files that are not in the processing or approved directories
will be processed. The user may also make a selection of files to process/reprocess.

## CTD file processing steps

### 1. Hex

### 2. Setup processing directory

Done early so that user may fix issues within the directory to allow processing to continue.
For example, if cast date failed to parse, the user may still determine the correct psa
file and copy it to the processing directory.

The app should display the errors that need to be fixed to allow a file to process.

### copy psa config file

### 3. Process

Process using the local psa

#### 3a. Lookup Information

latitude, cast date
TODOC where these are stored

#### 3b. Seabird steps/programs

## 4. Processing, Analysis

The file is now waiting in a `processing` state for approval by the user. If errors
were encountered, the file may show `error`

TODO review/doc: this error is currently not stored

## 4a. Reprocess

The user may reprocess the file after fixing issues. This runs the file through
all Seabird steps again. Examples of typical fixes are:
* edit the local psa file
* fix information in the database/spreadsheet
* fix issues in this code


## 5. Approval

When approved, the directory is moved to the approved directory.
