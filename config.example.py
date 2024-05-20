# dictionary of configuration options, or maybe should be frozen dataclass?
CONFIG = {}

# Paths
CONFIG["RAW_PATH"] = r"C:\AIMS\sbe_ctd_proc\raw"
CONFIG["PROCESSING_PATH"] = r"C:\AIMS\sbe_ctd_proc\processing"
CONFIG["DESTINATION_PATH"] = r"C:\AIMS\sbe_ctd_proc\PROCESSED"

CONFIG["CTD_CONFIG_PATH"] = r"C:\AIMS\sbe_ctd_proc\config"

# Location where you installed SBE Data Processing
CONFIG["SBEDataProcessing_PATH"] = r"C:\Program Files (x86)\Sea-Bird\SBEDataProcessing-Win32"

# Set whether the program designates latitude for the Derive module (1 for yes, 0 for no)
CONFIG["SET_DERIVE_LATITUDE"] = True

# Database
CONFIG["USE_DATABASE"] = True
CONFIG["DATABASE_MDB_FILE"] = r"C:\Users\awhite\data\CTD\OceanDBMMP_be.mdb"
CONFIG["DATABASE_MDW_FILE"] = r"C:\Users\awhite\data\CTD\OceanDBMMPSecurity.mdw"
CONFIG["DATABASE_USER"] = "readonly"
CONFIG["DATABASE_PASSWORD"] = "readonly"

# CTD IDs
CONFIG["CTD_LIST"] = [
    "597",
    "0597",
    "0890",
    "1009",
    "1233",
    "4409",
    "4525",
    "6180",
    "6383",
    "6390",
    "7053",
    "7360",
    "7816",
]

# # Livewire ctds have different temperature IDs - Adjust them here
# if ctd_id == '5165':
#     ctd_id = '1233'
# if ctd_id == '4851':
#     ctd_id = '0890'
CONFIG["LIVEWIRE_MAPPING"] = {"5165": "1233", "4851": "0890"}


CONFIG["LABEL_FONTS"] = ("Arial", 14, 'bold')
