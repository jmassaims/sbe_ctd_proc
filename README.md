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


# Setup

If needed, [install Python](https://www.python.org/downloads/).
For Windows users, it's easiest to install [Python 3 from Windows Store](https://apps.microsoft.com/detail/9ncvdn91xzqp).

This project uses [Hatch](https://hatch.pypa.io/1.13/), which manages the Python environment,
 dependencies, runs tests, etc.

[Install hatch](https://hatch.pypa.io/1.13/install/#gui-installer_1).
In Windows, this requires admin privileges. If the GUI Installer doesn't work, try the
[hatch command line installer](https://hatch.pypa.io/1.13/install/#command-line-installer_1).

Unfortunately, VSCode does not discover hatch installed other ways (e.g. using pip).
(see [Issue #23819](https://github.com/microsoft/vscode-python/issues/23819))

## Python Virtual Environment

`hatch` manages the virtual environment for you and creates it automatically with certain
commands like `hatch run`. You can explicitly manage the environment with `hatch env`.
To update all dependencies, delete the environment with `hatch env prune`; when the
environment is recreated, it will download the latest dependencies versions.

VSCode [should find the Hatch environment](https://hatch.pypa.io/1.12/how-to/integrate/vscode/)

For other IDEs, you may need to configure the Python interpreter with the hatch environment.
1. Get the path with: `hatch env find`
2. Add that interpreter path to your IDE
For example, in PyCharm add a new Python **System Interpreter** with that path
plus _/Scripts/python.exe_

## Seabird Dependencies

Install [SBE Data Processing](https://software.seabird.com/)

## Configuration

Copy `config.example.toml` to `config.toml` and edit for your setup.

# Running

`sbe-ctd-proc` if you are within the environment (`hatch shell`).
Alternatively, when outside the hatch shell: `hatch run sbe-ctd-proc`

This should open a browser tab to http://127.0.0.1:8080/ or http://localhost:8080/

## Development

To develop the nicegui app, run `gui_dev.py`, which will launch in reload mode.
This will reload the page whenever you modify python code.

If reload stops updating, stop the server. Check if it's still running in the background
by refreshing the page; if it is, kill the python process before starting again.

See [ui.run docs](https://nicegui.io/documentation/run) to change configuration.

## Tests

Tests are located in the `tests` directory. Run all tests with:
`hatch test`

Explicitly run a test env script like: `hatch run test:run`

Files can be executed individually.
Alternatively, run all tests with: `python -m unittest`
(*not ideal because this doesn't use the hatch test env*)

# Notes

If you change hatch `project.scripts`, you need to re-create the hatch environment for it
to have an effect.

This project uses the [uv installer](https://hatch.pypa.io/dev/how-to/environment/select-installer/),
which is much faster and works with current dependencies.

The old TKinter UI can be run with `sbe-ctd-proc-OLD`. This project is maintaining both UIs for now.
Also, the original `sbe_proc.py` script runs the old UI.

## Dependencies

Dependencies in pyproject.toml are using `~=`
([compatible release](https://hatch.pypa.io/latest/config/dependency/#compatible-release))
up to the patch version, which is fairly conservative.

If we want some dependencies to update minor versions, patch should be removed. For example
changing `"pandas~=2.2.3"` to `"pandas~=2.2"` would allow it to update to `2.3`.

**Known issues**

* Starlette versions 0.42 to 0.45.2 caused a 404 for static files. see [NiceGUI issue #4255](https://github.com/zauberzeug/nicegui/issues/4255) \
Workaround: Starlette version set to >=0.45.3 in pyproject.toml

## Miscalaneous Issues

Issues to investigate or fix. Some of these may be resolved by dependency update in the
future.

* gui-scripts not working, console seems to be required.
* NiceGui reload fails often.
