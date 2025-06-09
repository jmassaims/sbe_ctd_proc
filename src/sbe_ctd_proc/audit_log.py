from io import TextIOWrapper
import logging
from pathlib import Path
from typing import TypedDict
from csv import DictReader, DictWriter

from .ctd_file import CTDFile
from .parsing.cnv_info import CnvInfo, SensorInfo


# TODO logreq from DB
class AuditInfoCTDFile(TypedDict):
    """
    Data structure with information derived directly from CTDfile object or files.

    This is mostly .cnv file information.
    """
    hex_filename: str
    # aka 'base name' in code
    folder_name: str

    hex_dir: str
    processed_dir: str
    cast_date: str
    cast_date_type: str
    start_time: str
    start_time_type: str

    # "meters: 1"
    interval: str

    # number of active sensors
    n_sensors: int
    # concatenated active sensors "CNDC+TEMP+PRES+BAT_PERCENT+CPHL+OBS+PAR"
    sensors: str

    cndc_name: str
    cndc_sn: str
    cndc_calibdate: str
    temp_name: str
    temp_sn: str
    temp_calibdate: str
    pres_name: str
    pres_sn: str
    pres_calibdate: str
    bat_name: str
    bat_sn: str
    bat_calibdate: str
    cphl_name: str
    cphl_sn: str
    cphl_calibdate: str
    obs_name: str
    obs_sn: str
    obs_calibdate: str
    par_name: str
    par_sn: str
    par_calibdate: str

    datcnv_in: str

    filter_in: str
    filter_low_pass_tc_A: str
    filter_low_pass_tc_B: str
    filter_low_pass_A_vars: str
    filter_low_pass_B_vars: str

    alignctd_in: str
    alignctd_adv: str


    celltm_in: str
    celltm_alpha: str
    celltm_tau: str

    loopedit_in: str
    loopedit_minVelocity: str
    loopedit_surfaceSoak: str
    loopedit_excl_bad_scans: str

    wildedit_in: str

    # uppercase in cnv file
    Derive_in: str

    binavg_in: str
    binavg_bintype: str
    binavg_binsize: str
    binavg_excl_bad_scans: str
    binavg_skipover: str
    binavg_omit: str


class AuditInfoProcessing(TypedDict):
    """
    Audit log information from the processing/execution context.
    """
    con_filename: str
    latitude: float
    # last processing step command
    last_command: str

    approve_date: str
    # TODO verify if newlines supported
    approve_comment: str

class AuditInfo(AuditInfoCTDFile, AuditInfoProcessing):
    """
    Combined information for the audit log
    """
    pass

class AuditLog:

    filepath: Path
    "path to csv file"

    file: TextIOWrapper
    "open handle for csv file"

    update_rows: bool
    "look for previous rows with basename and update instead of always appending"

    flush_after_log: bool

    rows: list[dict | AuditInfo]
    """
    current rows updated/appended by log method.

    values may be mixed. i.e. appended rows will be types corresponding to AuditInfo
    while existing row's values will be strings.
    """

    # sensor prefixes that can have a second sensor and have created columns for it.
    # e.g. temp2

    possible_second_sensor = {'temp', 'cndc'}

    # order to write columns to csv
    # if these are changed, the program will not be able to append to old audit log and
    # will need to move the old audit log (or choose new path).
    # TODO could allow if initial columns subset of current
    columns: list[str] = [
        'hex_filename',
        'folder_name',
        'cast_date',
        'cast_date_type',
        'start_time',
        'start_time_type',
        'latitude',
        'hex_dir',
        'processed_dir',
        'con_filename',
        # CNV info
        'interval',

        'datcnv_in',

        'filter_in',
        'filter_low_pass_tc_A',
        'filter_low_pass_tc_B',
        'filter_low_pass_A_vars',
        'filter_low_pass_B_vars',

        'alignctd_in',
        'alignctd_adv',

        'celltm_in',
        'celltm_alpha',
        'celltm_tau',

        'loopedit_in',
        'loopedit_minVelocity',
        'loopedit_surfaceSoak',
        'loopedit_excl_bad_scans',

        'wildedit_in',

        'Derive_in',

        'binavg_in',
        'binavg_bintype',
        'binavg_binsize',
        'binavg_excl_bad_scans',
        'binavg_skipover',
        'binavg_omit',

        # sensor meta
        'n_sensors',
        'sensors',
        # sensor columns
        'cndc_name',
        'cndc_sn',
        'cndc_calibdate',
        'cndc2_name',
        'cndc2_sn',
        'cndc2_calibdate',
        'temp_name',
        'temp_sn',
        'temp_calibdate',
        'temp2_name',
        'temp2_sn',
        'temp2_calibdate',
        'pres_name',
        'pres_sn',
        'pres_calibdate',
        'cphl_name',
        'cphl_sn',
        'cphl_calibdate',
        'obs_name',
        'obs_sn',
        'obs_calibdate',
        'par_name',
        'par_sn',
        'par_calibdate',
        'spar_name',
        'spar_sn',
        'spar_calibdate',
        'turb_name',
        'turb_sn',
        'turb_calibdate',
        'dox2_name',
        'dox2_sn',
        'dox2_calibdate',
        'bat_name',
        'bat_sn',
        'bat_calibdate',
        'other_name',
        'other_sn',
        'other_calibdate',

        'last_command',

        'approve_date',
        'approve_comment'
    ]

    # cnv variables added to AuditInfo with a simple CnvInfo.get(name)
    simple_info = [
        'interval',

        'datcnv_in',

        'filter_in',
        'filter_low_pass_tc_A',
        'filter_low_pass_tc_B',
        'filter_low_pass_A_vars',
        'filter_low_pass_B_vars',

        'alignctd_in',
        'alignctd_adv',

        'celltm_in',
        'celltm_alpha',
        'celltm_tau',

        'loopedit_in',
        'loopedit_minVelocity',
        'loopedit_surfaceSoak',
        'loopedit_excl_bad_scans',

        'wildedit_in',

        'Derive_in',

        'binavg_in',
        'binavg_bintype',
        'binavg_binsize',
        'binavg_excl_bad_scans',
        'binavg_skipover',
        'binavg_omit',
    ]

    # Format for date+time columns
    datetime_format = '%Y-%m-%d %H:%M:%S'

    def __init__(self, filepath: str | Path, update_rows=False, flush_after_log=False) -> None:
        """
        Create AuditLog, open file. Check existing file's headers.
        @param update_rows log will edit existing rows (basename lookup) instead of appending
        @param flush_after_log flush after every log
        """
        filepath = Path(filepath)
        self.filepath = filepath
        self.update_rows = update_rows
        self.flush_after_log = flush_after_log
        self.needs_flush = False

        if filepath.is_dir():
            raise Exception("path to directory")

        is_newfile = True

        if filepath.exists():
            stat = filepath.stat()
            # consider existing files that are empty to be new files
            # Note: this was added to support test mkstemp behavior.
            is_newfile = stat.st_size == 0

        if is_newfile:
            # x is exclusive creation file mode
            mode = 'x' if not filepath.exists() else 'w'
            self.file = open(filepath, mode, newline='')
            # only used if update_rows True, but always initialize empty rows
            self.rows = []
        else:
            self.check_existing_file()
            self.file = open(filepath, 'a', newline='')

        self.writer = DictWriter(self.file, fieldnames=self.columns, dialect='excel')
        if is_newfile:
            self.writer.writeheader()

    def close(self):
        self.flush()
        self.file.close()

    def flush(self):
        if self.needs_flush:
            if self.file.closed:
                # reopen file for writing
                self.file = open(self.filepath, 'w', newline='')
                self.writer = DictWriter(self.file, fieldnames=self.columns, dialect='excel')
                self.writer.writeheader()

            self.writer.writerows(self.rows)
            self.file.close()
            self.needs_flush = False

    def check_existing_file(self):
        with open(self.filepath, 'r', newline='') as f:
            # need to use DictReader for fieldname attr to exist
            r = DictReader(f, dialect='excel')
            if self.columns != r.fieldnames:
                # for now user should move old file.
                # Idea: auto-rename *_2.csv, *_3.csv, ...
                raise Exception(f"Cannot append to audit log '{self.filepath.resolve()}'; columns have changed since audit log written")

            self.rows = [r for r in r]


    def log(self, ctd_file: CTDFile, cnv_file: str | Path, mixin_info: AuditInfoProcessing):
        """
        Log audit information to the log.
        @param flush write out rows to csv file now
        """
        info = self.build_info(ctd_file, cnv_file, mixin_info)

        if self.update_rows:
            # look for existing row by hex_filename
            existing_index = None
            for index in range(len(self.rows) - 1, 0, -1):
                if self.rows[index]['hex_filename'] == info['hex_filename']:
                    existing_index = index
                    break

            if existing_index is not None:
                self.rows[existing_index] = info
            else:
                self.rows.append(info)

            self.needs_flush = True
            if self.flush_after_log:
                self.flush()

        else:
            self.writer.writerow(info)

    def build_info(self, ctd_file, cnv_file, mixin_info):
        cnv = CnvInfo(cnv_file)

        # ctd_file.serial_number
        sensor_info = cnv.get_sensors_info()

        # initial AuditInfo with properties that are more compex.
        info: AuditInfo = {
            'hex_filename': ctd_file.hex_path.name,
            'hex_dir': str(ctd_file.hex_path.parent),
            'folder_name': ctd_file.base_file_name,
            'processed_dir': str(ctd_file.approved_dir.resolve()),
            'cast_date': ctd_file.cast_date.strftime(self.datetime_format) if ctd_file.cast_date else '',
            'cast_date_type': ctd_file.cast_date_type or '',
            'n_sensors': len(sensor_info),
        } # type: ignore ideally would be partial dict type

        # add simple properties with no special formatting
        for name in self.simple_info:
            try:
                info[name] = cnv.get(name)
            except KeyError as e:
                # warn about missing property, but keep going.
                logging.warning(e)

        for name, val in mixin_info.items():
            # not expecting to override variables, should be additional info.
            if name in info:
                raise Exception(f'{name}={info[name]} already in AuditInfo!')

            info[name] = val

        # add special groups of properties.
        self._add_sensor_info(info, sensor_info)
        self._add_start_time_info(info, cnv)
        return info

    def _add_sensor_info(self, info: AuditInfo, sensor_info: list[SensorInfo]):
        """adds columns for each sensor as well as 'sensors' field"""

        used_prefixes = set()
        for si in sensor_info:
            prefix = self._get_prefix(si)

            if prefix in used_prefixes:
                if prefix in self.possible_second_sensor:
                    prefix = f'{prefix}2'

                else:
                    # TODO support cndc2, need a test file
                    # old log had other sensors, but not needed at the moment.
                    #AltimeterSensor SensorID="0":
                    #'other_1'
                    #UserPolynomialSensor SensorID="61"
                    #'other_2'
                    raise Exception(f'prefix="{prefix}" already used. type={si["type"]}')

            used_prefixes.add(prefix)

            info[f'{prefix}_name'] = si['type']
            info[f'{prefix}_sn'] = si['sn']
            info[f'{prefix}_calibdate'] = si['calib_date']

        info['sensors'] = '+'.join(used_prefixes)

    def _add_start_time_info(self, info: AuditInfo, cnv: CnvInfo):
        start_time, time_type = cnv.get_start_time()
        info['start_time'] = start_time.strftime(self.datetime_format)
        info['start_time_type'] = time_type

    def _get_prefix(self, sensor_info: SensorInfo) -> str:
        """get standardized prefix for the sensor type"""

        type = sensor_info['type']

        for prefix, starter_text in simple_sensor_prefixes.items():
            if type.startswith(starter_text):
                return prefix

        # bat sensor type name is more complex
        # WET_LabsCStar SensorID="71"
        # TransChelseaSeatechWetlabCStarSensor SensorID="59"
        if 'CStar' in type:
            return 'bat'

        return 'other'


# sensor prefix that can be determined with a simple startswith
simple_sensor_prefixes = {
    'cndc': 'Conductivity',
    'temp': 'Temperature',
    'pres':'Pressure',

    # FluoroWetlabECO_AFL_FL_Sensor SensorID="20", FluoroWetlabWetstarSensor SensorID="21"
    'cphl': 'FluoroWetlab',

    # OBS_DA_3BackscatteranceSensor SensorID="28":, OBS_3plusSensor SensorID="63"
    'obs': 'OBS',

    # PARLog_SatlanticSensor SensorID="76", PAR_BiosphericalLicorChelseaSensor SensorID="42"
    'par': 'PAR',

    # SPAR_Sensor SensorID="51"
    'spar': 'SPAR',

    #TurbidityMeter SensorID="67"
    'turb': 'Turbidity',

    'dox2': 'Oxygen',
}

#all_sensor_prefixes = [*simple_sensor_prefixes.keys(), 'bat', 'other']
#for p in all_sensor_prefixes:
#    for v in ['name', 'sn', 'calibdate']:
#        print(f"'{p}_{v}',")
