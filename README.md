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
For Windows users, this is easiest to install from the [Windows Store](https://apps.microsoft.com/detail/9ncvdn91xzqp).

1. Create a virtual environment.
You can use your IDE (e.g. VSCode) to do this, or run:  
`python3 -m venv .venv`  
`.venv\Scripts\activate`

2. Install requirements  
`pip install -r requirements.txt`
