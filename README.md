# sbe_ctd_proc
 Seabird CTD Processor

Batch processing for Seabird CTD Data Processing.
Automated calibration file and CTD selection to process all files in a directory easily.

This script will process all .hex files in a directory and ask for latitude for each file's derive step.

Ensure all relevant calibration .xmlcon and .psa files are in the following config directory structure:
Dates must be at the end of the calibration_files_##### directory names.
- config ->
   - ctd_id1
   - ctd_id2 ->
      -  calibration_files_20120131
      -  calibration_files_20170601 ->
         -   20170601.xmlcon
         -   AlignCTD.psa
         -   BinAvgIMOS.psa
         -   DatCnv.psa
         -   DeriveIMOS.psa
         -   Filter.psa
         -   LoopEditIMOS.psa


## Setup

If needed, [install Python](https://www.python.org/downloads/).
For Windows users, it's easiest to install [Python 3 from Windows Store](https://apps.microsoft.com/detail/9ncvdn91xzqp).

[Install hatch](https://hatch.pypa.io/1.12/install/#gui-installer_1)
In Windows, this requires admin privlidges. If the GUI Installer is blocked, try the
[hatch command line installer](https://hatch.pypa.io/1.12/install/#command-line-installer_1).

Unfortunately, VSCode does not discover hatch installed other ways.
(see [Issue #23819](https://github.com/microsoft/vscode-python/issues/23819))

If the hatch installer doesn't work for you, install it with one of the other methods.

## Python Virtual Environment

`hatch` manages the environment for you and creates it automatically with certain
commands. Manage the environment with `hatch env`

VSCode [should find the Hatch environment](https://hatch.pypa.io/1.12/how-to/integrate/vscode/)

## Seabird Dependencies

Install [SBE Data Processing](https://software.seabird.com/)

### Config

Copy `config.example.toml` to `config.toml` and edit for your setup.

# Run

`sbe-ctd-proc` if you are within the environment (`hatch shell`).

Outside the environment: `hatch run sbe-ctd-proc`

If that doesn't work, use `sbe_proc.py`

## Tests

Tests are located in the `tests` directory. Run all tests with:
`hatch test`

Explicitly run a test env script like: `hatch run test:run`

Files can be executed individually.
Alternatively, run all tests with: `python -m unittest`
(*not ideal because this doesn't use the hatch test env*)
