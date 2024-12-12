"""
SBE CTD Data Processor
Author: Thomas Armstrong
Australian Institute of Marine Science

Workflow adjusted by Jack Massuger

- adding in full MMP SBE dataproc steps
- proposing adding a plotting step for alignment - fathom an option for visual here
- changed folder structure, code to take raw into processing folder, bring in xmlcon + psa, run conversions, then move all files to "completed" folder, then
- remove files from processing folder
-proposed addition of a log


"""

# TODO: Skip option for each cast
# TODO: Pull temp file cleanup over to main function for lost files left from using 'stop button'
# Pass temp file names across with module functions, pull them into a list, then use the stop button function to search for them and delete if they exist.

# Imports
import os
from pathlib import Path
from queue import Queue
import shutil
from datetime import datetime
import sqlalchemy as sa

from .audit_log import AuditInfo, AuditLog
from .SBE import SBE
from .ctd_file import CTDFile
from .psa_file import rewrite_psa_file
from .db import get_db
from .gui.dialog import request_latitude
from .config_util import *
from .config import CONFIG


def convert_hex_to_cnv(ctdfile: CTDFile, sbe: SBE) -> None:
    """Import hex file and convert to first stage cnv file (dat_cnv step)

    :param file_name: _description_
    :type file_name: _type_
    :param sbe: _description_
    :type sbe: _type_
    """
    # run the data conversion processing
    with open(ctdfile.hex_path, "r", encoding="utf-8") as hex_file:
        print("Processing file: ", ctdfile.hex_path)
        cnvfile = sbe.dat_cnv(hex_file.read())
        try:
            dest_file = ctdfile.processing_dir / f"{ctdfile.base_file_name}C.cnv"
            with open(dest_file, "w") as cnv_write_file:
                cnv_write_file.write(cnvfile)
            print("HEX file converted: ", dest_file)
        except IOError as e:
            print("Error while converting the CNV file! ", ctdfile.hex_path)
            raise e


# All other processing steps
def process_step(
    ctdfile: CTDFile,
    processing_step,
    target_file_ext: str,
    result_file_ext: str,
    output_msg: str,
    error_msg: str,
) -> Path:
    """Run a particular SBE processing step saving the intermediate result

    :param file_name: _description_
    :type file_name: _type_
    :param processing_step: _description_
    :type processing_step: _type_
    :param target_file_ext: _description_
    :type target_file_ext: str
    :param result_file_ext: _description_
    :type result_file_ext: str
    :param output_msg: _description_
    :type output_msg: str
    :param error_msg: _description_
    :type error_msg: str
    :returns path to outpt cnv file
    """

    file_name = ctdfile.base_file_name

    with open(
        ctdfile.processing_dir / f"{file_name}{target_file_ext}.cnv",
        "r",
        encoding="utf-8",
    ) as read_file:
        cnvfile = processing_step(read_file.read())
        dest_file = ctdfile.processing_dir / f"{file_name}{result_file_ext}.cnv"
        try:
            with open(dest_file, "w") as write_file:
                write_file.write(cnvfile)
                print(output_msg, dest_file.name)
                return dest_file
        except IOError as e:
            print(error_msg)
            if dest_file.exists():
                print("WARNING: file could be corrupted ", dest_file)

            raise e


def process_cnv(ctdfile: CTDFile, sbe: SBE, send: Queue = None, log = None) -> None:
    """Run SBE data processing steps

    :param file_name: _description_
    :type file_name: _type_
    :param sbe: _description_
    :type sbe: SBE
    """

    # ensure log is always a function (avoids a bunch of if statements below)
    noop = lambda *args, **kwargs: None
    log = log or noop

    num_steps = 7
    def send_step(name, num):
        if send:
            send.put(("process_step", name, num, num_steps))


    send_step("Filter", 1)
    cnvpath = process_step(
        ctdfile,
        sbe.filter,
        "C",
        "CF",
        "CNV file filtered successfully!",
        "Error while filtering the CNV file!",
    )
    log(ctdfile, cnvpath, sbe.last_command)

    send_step("Align", 2)
    cnvpath = process_step(
        ctdfile,
        sbe.align_ctd,
        "CF",
        "CFA",
        "CNV file aligned successfully!",
        "Error while aligning the CNV file!",
    )
    log(ctdfile, cnvpath, sbe.last_command)

    send_step("Cell Thermal Mass", 3)
    cnvpath = process_step(
        ctdfile,
        sbe.cell_thermal_mass,
        "CFA",
        "CFAC",
        "CNV file loop edited successfully!",
        "Error while loop editing the CNV file!",
    )
    log(ctdfile, cnvpath, sbe.last_command)

    send_step("Loop Edit", 4)
    cnvpath = process_step(
        ctdfile,
        sbe.loop_edit,
        "CFAC",
        "CFACL",
        "CNV file loop edited successfully!",
        "Error while loop editing the CNV file!",
    )
    log(ctdfile, cnvpath, sbe.last_command)

    send_step("Wild Edit", 5)
    cnvpath = process_step(
        ctdfile,
        sbe.wild_edit,
        "CFACL",
        "CFACLW",
        "CNV file loop edited successfully!",
        "Error while loop editing the CNV file!",
       )
    log(ctdfile, cnvpath, sbe.last_command)

    send_step("Derive", 6)
    cnvpath = process_step(
        ctdfile,
        sbe.derive,
        "CFACLW",
        "CFACLWD",
        "CNV file derived successfully!",
        "Error while deriving the CNV file!",
    )
    log(ctdfile, cnvpath, sbe.last_command)

    send_step("Bin Average", 7)
    cnvpath = process_step(
        ctdfile,
        sbe.bin_avg,
        "CFACLWD",
        "CFACLWDB",
        "CNV file bin averaged successfully!",
        "Error while bin averaging the CNV file!",
    )
    log(ctdfile, cnvpath, sbe.last_command)


def setup_processing_dir(ctdfile: CTDFile, config_folder: Path, exist_ok=False)-> None:
    """Create the processing directory and copy files to it"""
    ctdfile.processing_dir.mkdir(exist_ok=exist_ok)

    #JM carry xmlcon file and psa files with data
    setupfiles=os.listdir(config_folder)
    print("Copying config files to", ctdfile.processing_dir)
    print(", ".join(setupfiles))

    for confname in setupfiles:
        shutil.copy2(os.path.join(config_folder, confname), ctdfile.processing_dir)

def move_to_destination_dir(ctdfile: CTDFile)-> None:
    """Create the destination directory and sub-directories"""
    #exception doesnt work. lay out correct file struct from here instead of raw and temp ect.
    destination_dir = ctdfile.destination_dir
    dest_raw = destination_dir / "raw"
    dest_done = destination_dir / "done"
    dest_psa = destination_dir / "psa"
    dest_config = destination_dir / "config"

    try:
        destination_dir.mkdir()
        print(f"Setup destination directory: {destination_dir}")
    except FileExistsError:
       print(f"Destination directory already exists: {destination_dir}")

    # Ensure all sub directories are created
    for subdir in (dest_raw, dest_done, dest_psa, dest_config):
        try:
            subdir.mkdir()
        except FileExistsError:
            pass

    file_name = ctdfile.base_file_name
    try:
         shutil.copy2(ctdfile.hex_path, dest_raw)

         for file in ctdfile.processing_dir.iterdir():
             if file.suffix == ".cnv":
                 shutil.move(file, dest_done)
             elif file.suffix == ".psa":
                 shutil.move(file, dest_psa)
             elif file.suffix == ".xmlcon":
                 shutil.move(file, dest_config)
             else:
                 print(f"unexpected file in processing dir: {file}")

         leftoverfiles = os.listdir(ctdfile.processing_dir)
         if len(leftoverfiles) == 0:
            ctdfile.processing_dir.rmdir()

    except FileNotFoundError:
       print("Files not copied")


# old Process entrypoint, using Manager now.
def process() -> None:
    """Main process loop"""

    raw_path = Path(CONFIG["RAW_PATH"])
    if not raw_path.is_dir():
        raise Exception(f"RAW_PATH is not a directory: {CONFIG["RAW_PATH"]}")

    # convert generator to list so we can get count.
    hex_files = list(raw_path.glob("*.hex"))
    print(f"Processing {len(hex_files)} in {raw_path}")

    for file in hex_files:
        underway_processing = os.listdir(CONFIG["PROCESSING_PATH"])
        completed_processing = os.listdir(CONFIG["DESTINATION_PATH"])

        file_path = raw_path / file

        ctdfile = CTDFile(file_path)
        base_file_name = ctdfile.base_file_name

        if base_file_name in underway_processing:
            print(base_file_name, " already processing")
            continue

        #check if already being processed, skip if so
        if base_file_name in completed_processing:
            print(base_file_name, " already processed")
            continue

        print("\n******************* Processing new file *******************")

        if ctdfile.latitude is None:
            # database disabled or latitude missing for this file, request latitude input
            print(f"WARNING: database missing latitude for file {base_file_name}. Manual latitude input required.")
            ctdfile.latitude = request_latitude(base_file_name)

        process_hex_file(ctdfile)


def process_hex_file(ctdfile: CTDFile, audit: AuditLog = None, send: Queue = None, exist_ok = False):
    """
    Process the CTDFile through all steps.
    exist_ok: no error if processing dir exists. remove files in existing processing directory.
    @throws Exception if latitude not set on CTDFile
    """

    base_file_name = ctdfile.base_file_name

    latitude = ctdfile.latitude
    if latitude is None or latitude == '':
        raise Exception('latitude is required')

    ctdfile.parse_hex()

    serial_number = ctdfile.serial_number
    if serial_number not in CONFIG["CTD_LIST"]:
        raise Exception("CTD serial number {ctd_id} not in config CTD_LIST")

    cast_date = ctdfile.cast_date

    print(f"CTD Serial Number: {serial_number}, Cast date: {cast_date}")
    if send:
        send.put(("hex_info", serial_number, cast_date))

    config_folder = get_config_dir(serial_number, cast_date)
    print("Configuration Folder Selected: ", config_folder)

    xmlcon_file = get_xmlcon(config_folder)
    print("Configuration File:", xmlcon_file)

    if exist_ok and ctdfile.status() == 'processing':
        print('already processing, clearing directory', ctdfile.processing_dir)
        for f in ctdfile.processing_dir.iterdir():
            f.unlink()

    setup_processing_dir(ctdfile, config_folder, exist_ok)

    # psa files for AIMS modules
    #add and adjust for cellTM and Wildedit
    psa_files = [
        "Filter.psa",
        "AlignCTD.psa",
        "CellTM.psa",
        "LoopEdit.psa",
        "WildEdit.psa",
        "Derive.psa",
        "BinAvg.psa",
    ]
    # Remove name appends and enter latitude
    for psa_file in psa_files:
        psa_file_path = ctdfile.processing_dir / psa_file
        rewrite_psa_file(psa_file_path, latitude)


    # Create instance of SBE functions with config_path files
    sbe = SBE(
        bin=CONFIG["SBEDataProcessing_PATH"],
        temp_path=ctdfile.processing_dir,  # default
        xmlcon=ctdfile.processing_dir / xmlcon_file.name,
        # AIMS processing modules
        psa_dat_cnv=ctdfile.processing_dir / "DatCnv.psa",
        psa_filter=ctdfile.processing_dir / "Filter.psa",
        psa_align_ctd=ctdfile.processing_dir / "AlignCTD.psa",
        psa_cell_thermal_mass=ctdfile.processing_dir / "CellTM.psa",
        psa_loop_edit=ctdfile.processing_dir / "LoopEdit.psa",
        psa_wild_edit=ctdfile.processing_dir / 'WildEdit.psa',
        psa_derive=ctdfile.processing_dir / "Derive.psa",
        psa_bin_avg=ctdfile.processing_dir / "BinAvg.psa",

        # unused for AIMS processing
        # psa_dat_cnv=os.path.join(cwd, 'psa', 'DatCnv.psa'),
        # psa_derive_teos10=os.path.join(cwd, 'psa', 'DeriveTEOS_10.psa'),
        # psa_sea_plot=os.path.join(cwd, 'psa', 'SeaPlot.psa'),
        # psa_section=os.path.join(cwd, 'psa', 'Section.psa'),

    )

    if audit:
        # audit log function that adds information in this context.
        def log(ctdfile, cnvpath, last_command: str):
            mixin_info: AuditInfo = {
                'con_filename': xmlcon_file,
                'latitude': latitude,
                'last_command': last_command
            }
            audit.log(ctdfile, cnvpath, mixin_info)
    else:
        log = None

    # run DatCnv
    convert_hex_to_cnv(ctdfile, sbe)

    # Run other AIMS modules
    process_cnv(ctdfile, sbe, send, log)
