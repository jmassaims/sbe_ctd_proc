import pandas as pd


class LatitudeSpreadsheet:
    """Lookup latitude values in a XLSX spreadsheet."""

    def __init__(self, file):

        self.file = file

        self.df = pd.read_excel(self.file,
                                engine='openpyxl',
                                # only load the columns we actually need
                                usecols=['FileName', 'Latitude'],
                                )

    def lookup_latitude(self, base_name: str) -> float:
        """Lookup the latitude for the CTD file base name.
        Raises exception if not found or multiple found.
        """
        hex_name = f'{base_name}.hex'

        matching = self.df.loc[self.df['FileName'] == hex_name, 'Latitude']

        if len(matching) == 0:
            raise ValueError(f'No latitude found for {hex_name}')
        elif len(matching) > 1:
            raise ValueError(f'Multiple latitudes found for {hex_name}')

        return float(matching.values[0])
