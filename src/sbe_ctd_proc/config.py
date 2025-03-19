import logging
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import tomlkit
import tomlkit.container
from tomlkit.items import Item, Table
from tomlkit.container import Container
import tomlkit.items

from .db import OceanDB
from .latitude_spreadsheet import LatitudeSpreadsheet

# map from old config keys to new Config attrs
old_mapping = {
    'USE_DATABASE': 'db_enabled',
    'RAW_PATH': 'raw_path',
    'PROCESSING_PATH': 'processing_path',
    'DESTINATION_PATH': 'destination_path',
    'CTD_CONFIG_PATH': 'ctd_config_path',
    'SBEDataProcessing_PATH': 'sbe_bin_path',
    'SET_DERIVE_LATITUDE': 'derive_latitude',
    'USE_DATABASE': 'db_enabled',
    'DATABASE_MDB_FILE': 'db_mdb_file',
    'DATABASE_MDW_FILE': 'db_mdw_file',
    'DATABASE_USER': 'db_user',
    'DATABASE_PASSWORD': 'db_password',
    'CTD_LIST': 'ctd_list',
    'LIVEWIRE_MAPPING': 'livewire_mapping',
    'LABEL_FONTS': 'label_fonts'
}

# mapping of Config attribute to config.toml path
# by default, names ending with _path or _file must exist or config value set to None.
config_map = {
    'raw_path': ('paths', 'raw'),
    'processing_path': ('paths', 'processing'),
    'destination_path': ('paths', 'destination'),
    'sbe_bin_path': {
        'toml_path': ('paths', 'SBEDataProcessing'),
        'default': r'C:\Program Files (x86)\Sea-Bird\SBEDataProcessing-Win32'
    },
    'auditlog_file': ('paths', 'auditlog_file'),

    'db_enabled': ('database', 'enabled'),
    'db_mdb_file': ('database', 'mdb_file'),
    'db_mdw_file': ('database', 'mdw_file'),
    'db_user': ('database', 'user'),
    'db_password': ('database', 'password'),

    'ctd_config_path': ('ctd', 'config_path'),
    # TODO should this default to directories within ctd_config_path
    'ctd_list': ('ctd', 'list'),
    'livewire_mapping': ('livewire_mapping',),

    'derive_latitude': ('options', 'derive_latitude'),
    'latitude_method': ('options', 'latitude_method'),
    'latitude_spreadsheet_file': ('options', 'latitude_spreadsheet_file'),
    # 'label_fonts': {
    #     'toml_path': ('options', 'label_fonts'),
    #     'default': '("Arial", 14, "bold")'
    # }
}

# path/file config attributes that are not required to exist.
may_not_exist = {'auditlog_file'}

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
    raw_path: Path
    processing_path: Path
    destination_path: Path
    sbe_bin_path: Path
    auditlog_file: Optional[Path]

    # database
    db_enabled: bool
    db_mdb_file: Path
    db_mdw_file: Path
    db_user: str
    db_password: str

    # CTD
    ctd_config_path: Path
    ctd_list: list[str]
    livewire_mapping: dict

    # options
    derive_latitude: bool

    # 'ask' | 'spreadsheet' | 'database'
    latitude_method: str

    latitude_spreadsheet_file: Path

    # ---- initialized attributes ----

    # Lookup latitude using the configured implementation.
    # Raises LookupError on lookup failure.
    lookup_latitude: Callable[[str], float] | None

    latitude_service: Optional[LatitudeSpreadsheet]
    oceandb: Optional[OceanDB]

    # old config for Tkinter app
    # needs to be a tuple, TBD if add to toml
    label_fonts = ("Arial", 14, "bold")

    def __init__(self, path = None) -> None:
        try:
            if path is None:
                path = self.find_config()

            self.config_file = path.resolve()

            with open(self.config_file, 'r', newline='') as f:
                toml_doc = tomlkit.load(f)

                # configure logging before other config so log level respected
                # TODO do this even earlier in startup?
                self.setup_logging(toml_doc)

                logging.info(f"loading config toml: {self.config_file}")
                self.load_config(toml_doc)

            self.check_psa_config_dir()
            self.setup_latitude_service()
        except FileNotFoundError as e:
            # if running unit tests, missing config file is expected.
            if 'unittest' in sys.modules:
                # initialize minimum config to support unit tests.
                self.__init_empty_config()
            else:
                logging.error('config.toml not found! see README')
                sys.exit(1)

    def __init_empty_config(self):
        """setup empty data structures for when toml is missing.
        This is to support running tests without config.toml"""
        self.livewire_mapping = {}

    def __getitem__(self, key: str):
        new_attr = old_mapping[key]
        return getattr(self, new_attr)

    def load_config(self, toml_doc: tomlkit.TOMLDocument):
        """Load configuration from config.toml
        Checks that _path and _file properties exist, otherwise sets None if not found,
        unless property in may_not_exist.
        """

        invalid = []
        self.invalid = invalid

        for attr, info in config_map.items():
            default_val = None
            if type(info) is tuple:
                toml_path = info
            else:
                toml_path = info['toml_path']
                default_val = info['default']

            assert type(toml_path) is tuple and len(toml_path) > 0

            try:
                item = toml_doc
                for segment in toml_path:
                    # should be iterating throgh TOML Containers up to final Item.
                    assert isinstance(item, (Container, Table))
                    item = item[segment]

            except KeyError:
                item = None
                # TODO this should be conditional. For example, latitude_spreadsheet_file
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
            if attr.endswith('_path'):
                assert isinstance(value, str)
                p = Path(value).resolve()
                if attr in may_not_exist or p.is_dir():
                    value = p
                else:
                    value = None
                    invalid.append(attr)
                    logging.warning(f'{attr} directory does not exist: {initial_value}')

            elif attr.endswith('_file'):
                assert isinstance(value, str)
                p = Path(value).resolve()
                if attr in may_not_exist or p.is_file():
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

    def check_psa_config_dir(self):
        """set default ctd_config_path if not configured by user"""
        if self.ctd_config_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            path = project_root / 'config'
            if path.exists():
                self.ctd_config_path = path
            else:
                raise ConfigError(f'[ctd] config_path not set and default config dir not found: {path}')

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

        logging.basicConfig(level=level, format=format)

    def setup_latitude_service(self):
        self.latitude_service = None
        self.lookup_latitude = None

        if self.latitude_method == 'spreadsheet':
            self.latitude_service = LatitudeSpreadsheet(self.latitude_spreadsheet_file)
            self.lookup_latitude = self.latitude_service.lookup_latitude
            print('Configured latitude lookup via spreadsheet', self.latitude_spreadsheet_file.absolute())
        elif self.latitude_method == 'database':
            oceandb = self.get_db()
            if oceandb is None:
                raise ConfigError('latitude_method is database, but database is disabled or not configured')

            self.lookup_latitude = oceandb.lookup_latitude
            print('Configured latitude lookup via database')
        elif self.latitude_method == 'ask':
            # default, handled by Manager send/recv messages.
            print('Configured to ask for latitude')
        else:
            raise Exception(f'Invalid latitude_method: {self.latitude_method}')

    def refresh_services(self):
        """Refresh service state that may have changed between processing runs."""

        if self.latitude_service:
            self.latitude_service.refresh()


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

            oceandb = self.__init_db()
            return oceandb


CONFIG = Config()
