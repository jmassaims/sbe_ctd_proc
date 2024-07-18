from pathlib import Path
import tomlkit

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

config_map = {
    'raw_path': ('paths', 'raw'),
    'processing_path': ('paths', 'processing'),
    'destination_path': ('paths', 'destination'),
    'sbe_bin_path': {
        'toml_path': ('paths', 'SBEDataProcessing'),
        'default': r'C:\Program Files (x86)\Sea-Bird\SBEDataProcessing-Win32'
    },

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
    # 'label_fonts': {
    #     'toml_path': ('options', 'label_fonts'),
    #     'default': '("Arial", 14, "bold")'
    # }
}

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

    # old config for Tkinter app
    # needs to be a tuple, TBD if add to toml
    label_fonts = ("Arial", 14, "bold")

    def __init__(self, path = None) -> None:
        if path is None:
            path = self.find_config()

        self.config_file = path.resolve()

        self.load_config()

    def __getitem__(self, key: str):
        new_attr = old_mapping[key]
        return getattr(self, new_attr)

    def load_config(self):
        with open(self.config_file, 'r', newline='') as f:
            cfg = tomlkit.load(f)
            print("loaded config toml: ", self.config_file)

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
                val = cfg
                for segment in toml_path:
                    val = val[segment]

            except KeyError:
                val = None
                print(f'{self.config_file} missing "{toml_path}"')
                setattr(self, attr, default_val)
                continue

            # naming convention for Path config values.
            if attr.endswith('_path'):
                p = Path(val).resolve()
                if p.is_dir():
                    val = p
                else:
                    val = None
                    invalid.append(attr)

            elif attr.endswith('_file'):
                p = Path(val).resolve()
                if p.is_file():
                    val = p
                else:
                    val = None
                    invalid.append(attr)

            setattr(self, attr, val)

    def find_config(self) -> Path:
        # standard local location? python lib support?

        p = Path('config.toml')
        if p.is_file():
            return p.resolve()


CONFIG = Config()
