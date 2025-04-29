from dataclasses import dataclass
import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import tomlkit
from tomlkit.items import Item, Table
from tomlkit.container import Container
from tomlkit.exceptions import NonExistentKey

from .db import OceanDB
from .latitude_spreadsheet import LatitudeSpreadsheet

# map from old config keys to new Config attrs
old_mapping = {
    'USE_DATABASE': 'db_enabled',
    'RAW_PATH': 'raw_dir',
    'PROCESSING_PATH': 'processing_dir',
    'DESTINATION_PATH': 'approved_dir',
    'CTD_CONFIG_PATH': 'ctd_config_dir',
    'SBEDataProcessing_PATH': 'sbe_bin_dir',
    'USE_DATABASE': 'db_enabled',
    'DATABASE_MDB_FILE': 'db_mdb_file',
    'DATABASE_MDW_FILE': 'db_mdw_file',
    'DATABASE_USER': 'db_user',
    'DATABASE_PASSWORD': 'db_password',
    'LIVEWIRE_MAPPING': 'livewire_mapping',
    'LABEL_FONTS': 'label_fonts'
}

# mapping of Config attribute to config.toml path
# by convention, names ending with _dir or _file become Path values;
# if they don't exist, set to None unless may_not_exist=True
# default - set this value instead of None if config prop missing.
# mkdir - make directory if it does not exist
config_map = {
    'raw_dir': {
        'toml_path': ('paths', 'raw'),
        'mkdir': True
    },
    'processing_dir': {
        'toml_path': ('paths', 'processing'),
        'mkdir': True
    },
    'approved_dir': {
        'toml_path': ('paths', 'approved'),
        'mkdir': True
    },
    'ctd_config_dir': {
        'toml_path': ('paths', 'ctd_config'),
        # final CONFIG.ctd_config_dir should exist, but there's fallback behavior in check_ctd_config_dir()
        'may_not_exist': True
    },
    'sbe_bin_dir': {
        'toml_path': ('paths', 'SBEDataProcessing'),
        'default': r'C:\Program Files (x86)\Sea-Bird\SBEDataProcessing-Win32'
    },
    'auditlog_file': {
        'toml_path': ('paths', 'auditlog_file'),
        'may_not_exist': True
    },
    'db_enabled': ('database', 'enabled'),
    'db_mdb_file': ('database', 'mdb_file'),
    'db_mdw_file': ('database', 'mdw_file'),
    'db_user': ('database', 'user'),
    'db_password': ('database', 'password'),

    'livewire_mapping': ('livewire_mapping',),

    'latitude_method': ('options', 'latitude_method'),
    'latitude_spreadsheet_file': ('options', 'latitude_spreadsheet_file'),
    'chart_default_sensors': ('chart', 'default_sensors')
    # 'label_fonts': {
    #     'toml_path': ('options', 'label_fonts'),
    #     'default': '("Arial", 14, "bold")'
    # }
}

@dataclass
class RenamedConfigProp:
    old_path: tuple[str, ...]
    message: str

    def check(self, doc: tomlkit.TOMLDocument) -> str | None:
        try:
            item = resolve_toml_path(doc, self.old_path)
            if item:
                return self.message
        except NonExistentKey:
            pass

deprecated = [
    RenamedConfigProp(
        ('paths', 'destination'),
        '[paths] destination renamed to approved'
        )
]

class ConfigError(Exception):
    """Logical configuration error with app config system."""

# TODO test for Config, check default feature
class Config:
    # path to file used for this Config
    _config_file: Path
    # list of invalid attrs
    invalid: list[str]

    # configuration from toml file
    # these attrs will always be set, but may be None if invalid

    # paths
    raw_dir: Path
    processing_dir: Path
    approved_dir: Path
    sbe_bin_dir: Path
    auditlog_file: Optional[Path]

    # database
    db_enabled: bool
    db_mdb_file: Path
    db_mdw_file: Path
    db_user: str
    db_password: str

    # CTD
    ctd_config_dir: Path
    livewire_mapping: dict

    # options

    # 'ask' | 'spreadsheet' | 'database'
    latitude_method: str

    latitude_spreadsheet_file: Path

    # charts
    chart_default_sensors: list[str]
    chart_axis: dict[str, list[float]]
    sensor_map: dict[str, list[str]]

    # ---- initialized attributes ----

    # Lookup latitude using the configured implementation.
    # Raises LookupError on lookup failure.
    lookup_latitude: Callable[[str], float] | None

    latitude_service: Optional[LatitudeSpreadsheet]

    # present if latitude_method is 'constant'
    constant_latitude: float

    oceandb: Optional[OceanDB]

    # old config for Tkinter app
    # needs to be a tuple, TBD if add to toml
    label_fonts = ("Arial", 14, "bold")

    def __init__(self, path = None) -> None:
        try:
            if path is None:
                path = self.find_config()

            self.config_file = path.resolve()
            self.__read_config_file()

        except FileNotFoundError as e:
            # if running unit tests, missing config file is expected.
            if 'unittest' in sys.modules:
                # initialize minimum config to support unit tests.
                self.__init_empty_config()
            else:
                logging.error('config.toml not found! see README')
                sys.exit(1)

    def __read_config_file(self):
        """
        Read properties from config_file TOML and initialize config attributes.
        Note: may execute multiple times due to config reload mechanism.
        """
        with open(self.config_file, 'r', newline='') as f:
                toml_doc = tomlkit.load(f)

                # configure logging before other config so log level respected
                # TODO do this even earlier in startup?
                # Note: has no effect when run again unless we force, better to use log config file anyway.
                self.setup_logging(toml_doc)

                logging.info(f"loading config toml: {self.config_file}")
                self.check_problems(toml_doc)
                self.load_config(toml_doc)

                self.check_ctd_config_dir()
                self.setup_latitude_service(toml_doc)
                self.setup_charts(toml_doc)

    def __init_empty_config(self):
        """setup empty data structures for when toml is missing.
        This is to support running tests without config.toml"""
        self.livewire_mapping = {}

    def __getitem__(self, key: str):
        new_attr = old_mapping[key]
        return getattr(self, new_attr)

    def check_problems(self, toml_doc: tomlkit.TOMLDocument):
        """
        Check for config file problems
        Exits program if any problems are found.
        """
        problems = []
        for rule in deprecated:
            msg = rule.check(toml_doc)
            if msg:
                problems.append(rule.message)

        if problems:
            lines = '\n'.join(problems)
            s = 's' if len(problems) > 1 else ''
            logging.error(f'config.toml has {len(problems)} problem{s} that must be fixed:\n{lines}')

            sys.exit(1)


    def load_config(self, toml_doc: tomlkit.TOMLDocument):
        """
        Load configuration from config.toml using the config_map definition.
        Checks that _dir and _file properties exist, otherwise sets None if not found,
        unless property in may_not_exist.
        """

        invalid = []
        self.invalid = invalid

        for attr, info in config_map.items():
            if type(info) is tuple:
                toml_path = info
                default_val = None
                may_not_exist = False
                mkdir = False
            else:
                toml_path = info['toml_path']
                default_val = info['default'] if 'default'in info else None
                may_not_exist = info['may_not_exist'] if 'may_not_exist' in info else False
                mkdir = info['mkdir'] if 'mkdir' in info else False

            assert type(toml_path) is tuple and len(toml_path) > 0

            try:
                item = toml_doc
                for segment in toml_path:
                    # should be iterating throgh TOML Containers up to final Item.
                    assert isinstance(item, (Container, Table))
                    item = item[segment]

            except KeyError:
                item = None
                # TODO this warning should be conditional. For example, latitude_spreadsheet_file
                # only required when latitude_method is 'spreadsheet'
                logging.warning(f'{self.config_file} missing "{toml_path}"')
                setattr(self, attr, default_val)
                continue

            if isinstance(item, Item):
                value = item.value
            else:
                value = item

            initial_value = value

            # naming convention for Path config values.
            if attr.endswith('_dir'):
                assert isinstance(value, str)
                p = Path(value).resolve()
                if mkdir:
                    p.mkdir(parents=False, exist_ok=True)
                    value = p
                elif may_not_exist or p.is_dir():
                    # keep Path value when exists or not required to exist
                    value = p
                else:
                    # set final value to None
                    value = None
                    invalid.append(attr)
                    logging.warning(f'{attr} directory does not exist: {initial_value}')

            elif attr.endswith('_file'):
                assert isinstance(value, str)
                p = Path(value).resolve()
                if may_not_exist or p.is_file():
                    value = p
                else:
                    value = None
                    invalid.append(attr)
                    logging.warning(f'{attr} directory does not exist: {initial_value}')

            setattr(self, attr, value)

        if invalid:
            invalid_str = ', '.join(invalid)
            logging.warning(f'''Invalid config properties: {invalid_str}
    These values are set to None and may crash the app with None/NoneType errors, see above warnings.''')

    def check_ctd_config_dir(self):
        """set default ctd_config_dir if not configured by user"""
        if self.ctd_config_dir is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            path = project_root / 'config'
            if path.exists():
                self.ctd_config_dir = path
            else:
                raise ConfigError(f'[ctd] config_dir not set and default config dir not found: {path}')

        elif not self.ctd_config_dir.is_dir():
            raise ConfigError(f'[paths] ctd_config directory does not exist: {self.ctd_config_dir}')

    def find_config(self) -> Path:
        """Look for the app config file in the standard locations."""
        # TODO standard local config location? python lib support? NiceGUI?

        p = Path('config.toml')
        if p.is_file():
            return p.resolve()

        raise FileNotFoundError('config.toml not found')

    def setup_logging(self, toml_doc: tomlkit.TOMLDocument):
        # we're using our config.toml file for simplicity, but may want to consider:
        # https://docs.python.org/3/library/logging.config.html#logging-config-fileformat

        logging_config = toml_doc['logging']
        assert isinstance(logging_config, (Container, Table))

        level: str = logging_config['level']
        level = level.upper()

        format: str = logging_config['format']

        logging.basicConfig(level=level, format=format, force=True)

    def setup_latitude_service(self, toml_doc: tomlkit.TOMLDocument):
        self.latitude_service = None
        self.lookup_latitude = None

        if self.latitude_method == 'spreadsheet':
            self.latitude_service = LatitudeSpreadsheet(self.latitude_spreadsheet_file)
            self.lookup_latitude = self.latitude_service.lookup_latitude
            logging.info('Configured latitude lookup via spreadsheet', self.latitude_spreadsheet_file.absolute())
        elif self.latitude_method == 'database':
            oceandb = self.get_db()
            if oceandb is None:
                raise ConfigError('latitude_method is database, but database is disabled or not configured')

            self.lookup_latitude = oceandb.lookup_latitude
            logging.info('Configured latitude lookup via database')
        elif self.latitude_method == 'ask':
            # default, handled by Manager send/recv messages.
            logging.info('Configured to ask for latitude')
        elif self.latitude_method == 'constant':
            lat = float(toml_doc['options']['constant_latitude'])

            def lookup_latitude(base_file_name: str) -> float:
                return lat

            self.lookup_latitude = lookup_latitude
            logging.info(f'All files will use constant latitude: {lat}')

        else:
            raise Exception(f'Invalid latitude_method: {self.latitude_method}')

    def setup_charts(self, toml_doc: tomlkit.TOMLDocument):
        sensor_map: Table = toml_doc['sensor_map']
        self.sensor_map = sensor_map.unwrap()

        axis: Table = toml_doc['chart_axis']
        self.chart_axis = axis.unwrap()

    def refresh_services(self):
        """Refresh service state that may have changed between processing runs."""

        if self.latitude_service:
            self.latitude_service.refresh()

    def reload(self):
        """Reload the config toml file and refresh services"""
        self.__read_config_file()

    def __init_db(self) -> OceanDB:
        """Initialize new OceanDB instance from config."""

        # TODO: if opening the db backend just need to supply the mdb file and not mdw and skip security check
        mdb_file = self.db_mdb_file
        if not mdb_file.exists():
            raise FileNotFoundError(mdb_file)

        try:
            mdw_file = self.db_mdw_file
            if not mdw_file.exists():
                raise FileNotFoundError(mdw_file)
        except KeyError:
            # TODO test exception handling
            mdw_file = None

        return OceanDB(mdb_file, mdw_file, self.db_user, self.db_password)


    def get_db(self) -> OceanDB | None:
        """get the OceanDB instance (initializing if needed).
        returns None if database disabled.
        """

        # check if already initialized
        if hasattr(self, 'oceandb') and self.oceandb is not None:
            return self.oceandb
        else:
            if not self.db_enabled:
                return None

            self.oceandb = self.__init_db()
            return self.oceandb

    def get_chart_axis(self, id: str) -> list[float]:
        """
        get the chart axis min/max for the id
        @throws LookupError if not found
        """
        try:
            return self.chart_axis[id]
        except KeyError:
            pass

        standard_id = None
        # find mapping for this id
        for x, alias in self.sensor_map.items():
            if id in alias:
                standard_id = x
                break

        if standard_id is None:
            raise LookupError(f'"{id} not mapped in [sensor_map]"')

        return self.chart_axis[standard_id]


def resolve_toml_path(doc: tomlkit.TOMLDocument, path: tuple[str, ...]):
    """
    Get the toml item at the path.
    @throws NonExistentKey if path invalid
    """
    item = doc
    for x in path:
        item = item[x] # type: ignore

    return item

CONFIG = Config()
