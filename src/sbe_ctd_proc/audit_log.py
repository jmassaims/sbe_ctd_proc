from io import TextIOWrapper
from pathlib import Path
from typing import TypedDict
from csv import DictReader, DictWriter

from .ctd_file import CTDFile
from .cnv_parser import CnvInfoRaw, SensorInfo

# TODO logreq from DB
class AuditInfo(TypedDict):
    """Data structure with information from .cnv file"""
    hex_filename: str
    # aka 'base name' in code
    folder_name: str
    con_filename: str
    hex_dir: str
    processed_dir: str
    cast_date: str
    latitude: float
    # "meters: 1"
    interval: str
    # last processing step command
    last_command: str
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

    datacnv_in: str

    filter_in: str
    filter_low_pass_tc_B: str
    filter_low_pass_A_vars: str
    filter_low_pass_B_vars: str

    alignctd_in: str

    celltm_in: str
    celltm_alpha: str
    celltmp_tau: str

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


class AuditLog:

    filepath: Path
    file: TextIOWrapper

    # order to write columns to csv
    columns: list[str] = [
        'hex_filename',
        'folder_name',
        'cast_date',
        'latitude',
        'hex_dir',
        'processed_dir',
        'con_filename',
        # CNV info
        'interval',

        'datacnv_in',

        'filter_in',
        'filter_low_pass_tc_B',
        'filter_low_pass_A_vars',
        'filter_low_pass_B_vars',

        'alignctd_in',

        'celltm_in',
        'celltm_alpha',
        'celltmp_tau',

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

        # sensor meta
        'n_sensors',
        'sensors',
        # sensor columns
        'cndc_name',
        'cndc_sn',
        'cndc_calibdate',
        'temp_name',
        'temp_sn',
        'temp_calibdate',
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

        'last_command'
    ]

    # cnv variablesadded to AuditInfo with a simple get(name)
    simple_info = [
        'interval',

        'datacnv_in',

        'filter_in',
        'filter_low_pass_tc_B',
        'filter_low_pass_A_vars',
        'filter_low_pass_B_vars',

        'alignctd_in',

        'celltm_in',
        'celltm_alpha',
        'celltmp_tau',

        'loopedit_in',
        'loopedit_minVelocity',
        'loopedit_surfaceSoak',
        'loopedit_excl_bad_scans',

        'wildedit_in',

        'Derive_in',

        'binavg_in',
        'binavg_bintype',
        'binavg_binsize',
        'binavg_excl_bad_scans'
    ]

    def __init__(self, filepath: str | Path) -> None:
        filepath = Path(filepath)
        self.filepath = filepath

        if filepath.is_dir():
            raise Exception("path to directory")

        is_newfile = not filepath.exists()

        if is_newfile:
            self.file = open(filepath, 'x', newline='')
        else:
            self.check_existing_file()
            self.file = open(filepath, 'a', newline='')

        self.writer = DictWriter(self.file, fieldnames=self.columns, dialect='excel')
        if is_newfile:
            self.writer.writeheader()

    def close(self):
        self.file.close()

    def check_existing_file(self):
        with open(self.filepath, 'r', newline='') as f:
            # need to use DictReader for fieldname attr to exist
            r = DictReader(f, dialect='excel')
            if self.columns != r.fieldnames:
                # for now user should move old file.
                # Idea: auto-rename *_2.csv, *_3.csv, ...
                raise Exception(f"Cannot append to audit log '{self.filepath.resolve()}'; columns have changed since audit log written")


    def log(self, ctd_file: CTDFile, cnv_file: str, mixin_info: AuditInfo):
        cnv = CnvInfoRaw(cnv_file)

        # ctd_file.serial_number
        sensor_info = cnv.get_sensors_info()

        info: AuditInfo = {
            'hex_filename': ctd_file.hex_path.name,
            'hex_dir': ctd_file.hex_path.parent,
            'folder_name': ctd_file.base_file_name,
            'processed_dir': ctd_file.destination_dir.resolve(),
            'cast_date': ctd_file.cast_date,
            'n_sensors': len(sensor_info),
        }

        for name in self.simple_info:
            try:
                info[name] = cnv.get(name)
            except KeyError as e:
                # warn, but keep going
                # TODO improve warning, expect missing if that step not done yet.
                print(e)
                pass

        for name, val in mixin_info.items():
            # not expecting to override variables, should be additional info.
            if name in info:
                raise Exception(f'{name}={info[name]} already in AuditInfo!')

            info[name] = val

        self._add_sensor_info(info, sensor_info)

        self.writer.writerow(info)

    def _add_sensor_info(self, info: AuditInfo, sensor_info: list[SensorInfo]):
        """adds columns for each sensor as well as 'sensors' field"""

        used_prefixes = set()
        for si in sensor_info:
            prefix = self._get_prefix(si)

            if prefix in used_prefixes:
                # TODO support cndc_2, temp_2, need a test file
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
