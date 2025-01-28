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
        Raises LookupError if not found or multiple found.
        """
        hex_name = f'{base_name}.hex'

        matching = self.df.loc[self.df['FileName'] == hex_name, 'Latitude']

        if len(matching) == 0:
            raise LookupError(f'No latitude found for {hex_name}')
        elif len(matching) > 1:
            raise LookupError(f'Multiple latitudes found for {hex_name}')

        lat = float(matching.values[0])
        print(f'Latitude for {hex_name}: {lat} (from spreadsheet)')
        return lat
