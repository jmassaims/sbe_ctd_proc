# dictionary of configuration options, or maybe should be frozen dataclass?
CONFIG = {}

# paths
CONFIG["RAW_PATH"] = r"C:\AIMS\sbe_ctd_proc\raw"
CONFIG["PROCESSED_PATH"] = r"C:\AIMS\sbe_ctd_proc\processed"
CONFIG["CTD_CONFIG_PATH"] = r"C:\AIMS\sbe_ctd_proc\config"
CONFIG["CTD_DATABASE_PATH"] = r"R:\Instrumentation\MMPDB\MMP_OceanDB\Backend"
CONFIG["DESTINATION_PATH"] = r"C:\AIMS\sbe_ctd_proc\COMPLETED"

# Set whether the program designates latitude for the Derive module (1 for yes, 0 for no)
CONFIG["SET_DERIVE_LATITUDE"] = True
CONFIG["USE_DATABASE"] = True
#

# CTD IDs
CONFIG["CTD_LIST"] = [
    "0597",
    "0890",
    "1009",
    "1233",
    "4409",
    "4525",
    "6180",
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
