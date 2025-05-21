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
from multiprocessing import Queue
import shutil
from typing import Callable, Optional

from .audit_log import AuditInfo, AuditLog
from .SBE import SBE
from .ctd_file import CTDFile
from .psa_file import rewrite_psa_file
from .config_util import *
from .config import CONFIG


def convert_hex_to_cnv(ctdfile: CTDFile, sbe: SBE) -> None:
    """Import hex file and convert to first stage cnv file (dat_cnv step)

    :param file_name: _description_
    :type file_name: _type_
    :param sbe: _description_
    :type sbe: _type_
    """
    # encoding option omitted to be more flexible.
    # Previously, this had encoding="utf-8", but we had one file (trip_6169_WQP143)
    # with strange file encoding that caused an error.
    with open(ctdfile.hex_path, "r") as hex_file:
        print("Processing file: ", ctdfile.hex_path)
        cnvfile = sbe.dat_cnv(hex_file.read())
        try:
            dest_file = ctdfile.processing_dir / f"{ctdfile.base_file_name}_C.cnv"
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


def process_cnv(
        ctdfile: CTDFile,
        sbe: SBE,
        send: Optional[Queue] = None,
        log: Optional[Callable] = None
    ) -> Path:
    """Run SBE data processing steps

    @param ctdfile file to process
    @param sbe Seabird processing service to use
    @param send Queue to send messages to GUI
    @param log function to call after every step
    @returns Path to final CNV file
    """

    # ensure log is always a function (avoids a bunch of if statements below)
    noop = lambda *args, **kwargs: None
    log = log or noop

    num_steps = len(CONFIG.process_steps)
    def send_step(name, num):
        if send:
            send.put(("process_step", name, num, num_steps))

    target_file_ext = '_C' # from dat_cnv
    allowed_func_names = ['dat_cnv', 'filter', 'align_ctd', 'cell_thermal_mass', 'loop_edit', 'wild_edit', 'derive', 'bin_avg', 'derive_teos10', 'wild_edit']
    for i, step in enumerate(CONFIG.process_steps):
        #import ipdb; ipdb.set_trace()
        func_name = step['function']
        if func_name not in allowed_func_names:
            raise ValueError(f"Invalid function name: {func_name}")
        if func_name == 'dat_cnv':
            # dat_cnv is already run before this function by convert_hex_to_cnv
            result_file_ext = '_C'
            continue
        psa_file = step['psa_file']
        append = step['append']
        send_step(func_name, i+1)
        result_file_ext = f"{target_file_ext}{append}"
        cnvpath = process_step(
            ctdfile,
            getattr(sbe, func_name),
            target_file_ext,
            result_file_ext,
            f"CNV file operation successful: {func_name}",
            f"Error while performing operation : {func_name}",
        )
        log(ctdfile, cnvpath, sbe.last_command)
        target_file_ext = result_file_ext

    return cnvpath

# TODO move to utils file
def smart_copy_file(src: Path, dst: Path) -> Path:
    """
    only copy file if it does not exist at destination.
    log copy action at DEBUG level.
    @returns Path to the file
    """
    assert src.is_file()

    file_dst = dst / src.name if dst.is_dir() else dst

    # check if file already exists
    if dst.is_dir():
        if file_dst.exists():
            logging.debug('file already exists: %s', file_dst)
            return file_dst

    elif dst.exists():
        logging.debug('file already exists: %s', dst)
        assert dst.is_file()
        return dst

    shutil.copy2(src, dst)
    logging.debug('cp %s %s', src, dst)
    return file_dst


def setup_processing_dir(ctdfile: CTDFile, config_folder: Path | None) -> Path:
    """
    Create/verify the processing directory and copy files to it from config_folder.

    Safe to run multiple times for the same ctdfile; existing files are never overwritten.
    Copies hex file, xmlcon, psa. If config_folder not provided, checks that:
    * directory has one xmlcon file
    * directory has at least one psa

    @returns xmlcon path to the single xmlcon in this directory
    @throws AssertionError if problem and processing should not move forward.
    """
    dir = ctdfile.processing_dir
    new_dir = not dir.exists()
    dir.mkdir(exist_ok=True)

    log_prefix = 'setup new processing dir' if new_dir else 'verified existing processing dir'

    smart_copy_file(ctdfile.hex_path, dir)

    # Note: xmlcon files can have various names whereas psa files are always the same
    # first check for existing xmlcon files, which will determine if we try to copy a xmlcon
    existing_xmlcons = list(dir.glob('*.xmlcon'))
    if len(existing_xmlcons) > 1:
        raise AssertionError(f'processing dir has multiple xmlcon files {dir}')

    xmlcon_file = None
    if config_folder:
        # have config folder, which should have psas and one xmlcon file
        for psa_file in config_folder.glob('*.psa'):
            if psa_file.is_file():
                smart_copy_file(psa_file, dir)
            else:
                logging.warning('Not a file: %s', psa_file)

        if len(existing_xmlcons) == 0:
            # no xmlcon files in processing directory, copy from config
            src_xmlcon_file = get_xmlcon(config_folder)
            xmlcon_file = smart_copy_file(src_xmlcon_file, dir)
        else:
            # have xmlcon config, but a xmlcon already exists, so use that
            xmlcon_file = existing_xmlcons[0]

            try:
                # check if names are identical
                cfg_xmlcon_file = get_xmlcon(config_folder)
                if cfg_xmlcon_file.name != xmlcon_file.name:
                    logging.info('existing xmlcon name (%s) differs from config directory (%s)',
                                 xmlcon_file.name, cfg_xmlcon_file.name)

            except AssertionError as e:
                logging.warning('Existing xmlcon in processing, but none in CTD config', exc_info=True)

        logging.info(f'{log_prefix} {dir} xmlcon={xmlcon_file.name}')

    else:
        # no config folder, see if needed files already exist.
        if len(existing_xmlcons) == 0:
            raise AssertionError('no ctd config dir and no existing xmlcon files')

        # check at least one psa
        psa_files = list(dir.glob('*.psa'))
        if len(psa_files) == 0:
            raise AssertionError(f"No psa files in: {dir}")

        logging.debug('No ctd config, but existing psa(s) and xmlcon found: %s', existing_xmlcons[0])
        xmlcon_file = existing_xmlcons[0]

        logging.info(f'{log_prefix} {dir} xmlcon={xmlcon_file.name}, no CTD config folder')

    assert xmlcon_file is not None
    return xmlcon_file

def move_to_approved_dir(ctdfile: CTDFile)-> None:
    """
    Move the processing directory to the approved area.

    Reorganizes files in the directory by moving them into subdirectories.
    """
    approved_dir = ctdfile.approved_dir

    if approved_dir.exists():
        raise FileExistsError(f'destination directory already exists: {approved_dir}')

    logging.info("Approved: mv %s %s", ctdfile.processing_dir, approved_dir)

    shutil.move(ctdfile.processing_dir, approved_dir)

    dest_raw = approved_dir / "raw"
    dest_done = approved_dir / "done"
    dest_psa = approved_dir / "psa"
    dest_config = approved_dir / "config"

    # Ensure all sub directories are created
    for subdir in (dest_raw, dest_done, dest_psa, dest_config):
        try:
            subdir.mkdir()
        except FileExistsError:
            logging.warning("subdirectory already existed in processing? %s", subdir)

    # reorganize files
    for file in ctdfile.approved_dir.iterdir():
        # only consider files
        if not file.is_file():
            continue

        if file.suffix == ".cnv":
            shutil.move(file, dest_done)
        elif file.suffix == ".psa":
            shutil.move(file, dest_psa)
        elif file.suffix == ".xmlcon":
            shutil.move(file, dest_config)
        elif file.suffix == '.hex':
            shutil.move(file, dest_raw)
        else:
            logging.warning(f"unexpected file in approved dir: {file}")

# not used yet
def reset_processing_dir(ctdfile: CTDFile):
    # TODO maybe only remove files this program creates?
    logging.info('clearing directory', ctdfile.processing_dir)
    # delete all files in directory
    for f in ctdfile.processing_dir.iterdir():
        f.unlink()

def process_hex_file(ctdfile: CTDFile,
                     audit: Optional[AuditLog] = None,
                     send: Optional[Queue] = None,
                     exist_ok = False):
    """
    Process the CTDFile through all steps.
    exist_ok: no error if processing dir exists. use existing config files
    @throws Exception if latitude not set on CTDFile
    @throws ValueError for config value issues related to config dir lookup
    """

    base_file_name = ctdfile.base_file_name

    # Exception if caller specifies existing directory not ok.
    # Not relevant to the App, which runs with exist_ok True.
    if ctdfile.processing_dir.exists() and not exist_ok:
        raise Exception(f'Processing dir already exists: {ctdfile.processing_dir}')

    latitude = ctdfile.latitude
    if latitude is None or latitude == '':
        raise Exception('latitude is required')

    # need to parse to get cast date from the hex file.
    ctdfile.parse_hex()

    serial_number = ctdfile.serial_number
    cast_date = ctdfile.cast_date

    logging.debug(f"{base_file_name} CTD Serial Number: {serial_number}, Cast date: {cast_date}")
    if send:
        send.put(("hex_info", serial_number, cast_date))

    # try to get the config folder, but allow for user to supply all files manually
    config_folder = None
    try:
        config_folder = get_config_dir(serial_number, cast_date)
        logging.debug("%s Configuration Folder Selected: %s", base_file_name, config_folder)
    except Exception as ex:
        # Always setup the processing directory, which allows user to manually fix issues
        # with psa and xmlcon files.
        logging.exception(f'Could not get ctd config directory for {ctdfile.hex_path}')

    xmlcon_file = setup_processing_dir(ctdfile, config_folder)
    if config_folder is None:
        logging.info('Continuing processing with existing psa,xmlcon files')

    logging.debug("%s xmlcon config file: %s", base_file_name, xmlcon_file)

    for i, step in enumerate(CONFIG.process_steps):
        func_name = step['function']
        psa_file = step['psa_file']
        psa_file_path = ctdfile.processing_dir / psa_file
        rewrite_psa_file(psa_file_path, latitude)

    # Create instance of SBE with local processing dir psa/xmlcon files.
    sbe = SBE(
        bin=CONFIG.sbe_bin_dir,
        temp_path=ctdfile.processing_dir,  # default
        xmlcon=ctdfile.processing_dir / xmlcon_file.name,
        process_steps=CONFIG.process_steps,
    )

    if audit:
        # audit log function that adds information in this context.
        def log(ctdfile, cnvpath, last_command: str):
            mixin_info: AuditInfo = {
                'con_filename': str(xmlcon_file.name),
                'latitude': latitude,
                'last_command': last_command
            } # type: ignore partial dict
            audit.log(ctdfile, cnvpath, mixin_info)
    else:
        log = None

    # run DatCnv
    convert_hex_to_cnv(ctdfile, sbe)

    # Run other AIMS modules
    # Note: can add log argument here to log after every step.
    cnvpath = process_cnv(ctdfile, sbe, send)

    log(ctdfile, cnvpath, sbe.last_command)
