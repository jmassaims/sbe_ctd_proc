# sbe_ctd_proc
 Seabird CTD Processor

Batch processing for Seabird CTD Data Processing.
Automated calibration file and CTD selection to process all files in a directory easily.

This script will process .hex files in a directory and ask for latitude for each file's
derive step as well as parse/lookup the cast date and other information.
The app is created with [NiceGUI](https://nicegui.io)

* [Technical Overview](./docs/overview.md) - highlights and explanations of important concepts in code.
* [Process Flow](./docs/process_flow.md) - description of the flow files go through.

# Setup

This project uses [uv](https://docs.astral.sh/uv/)
to manage the Python environment and dependencies.

Current uv install command for Windows:
```bash
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

`uv` should install Python for you if needed. Alternatively,
 [install Python](https://www.python.org/downloads/) yourself.
For Windows users, it's easiest to install [Python 3 from Windows Store](https://apps.microsoft.com/detail/9ncvdn91xzqp).

## Python Virtual Environment

`uv` creates a _.venv_ directory, which most Python IDEs should discover automatically.
This will be created automatically by commands like `uv run`, or you can explicitly run
`uv sync`.

## Seabird Dependencies

Install [SBE Data Processing](https://software.seabird.com/) (in the All Software section).
This app will execute some of the programs installed by Seabird.

## Configuration

### config.toml

Copy `config.example.toml` to `config.toml` and edit for your setup.
Any path with `<USER>` is an example value and should be fixed unless you're not using
that feature.

**Tip:** you can create/select directories with File Explorer, copy them, then paste in
your editor to paste the path, which just needs quotes around it in _config.toml_.

* Under `[paths]`, update `raw`, `processing`, `destination`

**Optional:**
* Update `SBEDataProcessing` if you installed SBE Data Processing to another location
* Under `[ctd]`, set `config_path` to the directory of psa config files if you want to
use a different location than the `config` directory in this project.

### psa files config directory

By default, the `config` directory in this project will be used. To use another directory,
specify `[ctd]` `config_path` in the _config.toml_ file.

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

# Running

`uv run sbe_proc.py`

This should open a browser tab to http://127.0.0.1:8080/ or http://localhost:8080/

## Development

To develop the nicegui app, run `gui_dev.py`, which will launch in reload mode.
This will reload the page whenever you modify python code. You can run this various ways:

* `uv run gui_dev.py`
* `python gui_dev.py` (if venv is active)
* open file in your IDE and click play/run button. (IDE should have the venv active)

Tip: If reload stops updating, stop the server. Check if it's still running in the background
by refreshing the page; if it is, kill the python process before starting again.
_This seems to be less of an issue with later versions of NiceGUI._

See [ui.run docs](https://nicegui.io/documentation/run) to change configuration.

## Tests

Tests are located in the `tests` directory. Run all tests with: `python -m unittest`

Alternatively, if using VSCode, the Testing tab should work.

# Notes

This project was originally created with hatch. For now, hatch configuration has been
left in the pyproject.toml file.

The old TKinter UI can be run with `sbe-ctd-proc-OLD`. This project is maintaining both UIs for now.
Also, the original `sbe_proc.py` script runs the old UI.

## Dependencies

Dependencies in pyproject.toml are using `~=`
([compatible release](https://hatch.pypa.io/latest/config/dependency/#compatible-release))
up to the patch version, which is fairly conservative.

If we want some dependencies to update minor versions, patch should be removed. For example
changing `"pandas~=2.2.3"` to `"pandas~=2.2"` would allow it to update to `2.3`.

**Known issues**

Various technical issues and their workarounds.
For more information, see [these notes](./docs/tech_issues.md).

* Python 3.13 (system or managed) may have various build errors.
  The version is pinned by the `.python-version` file to avoid these issues.
* Starlette versions 0.42 to 0.45.2 caused a 404 for static files. see [NiceGUI issue #4255](https://github.com/zauberzeug/nicegui/issues/4255) \
Workaround: Starlette version set to >=0.45.3 in pyproject.toml
