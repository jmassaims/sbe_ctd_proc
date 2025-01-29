import pandas as pd


class LatitudeSpreadsheet:
    """Lookup latitude values in a XLSX spreadsheet."""

    df: pd.DataFrame

    def __init__(self, file):

        self.file = file

        if not file.is_file():
            raise FileNotFoundError(f'Latitude spreadsheet not found: {file}')

        # don't refresh now as this can crash the entire app if the
        # file is opened by Excel.

    def refresh(self):
        """Load/reload the dataframe from the spreadsheet."""

        self.df = pd.read_excel(self.file,
                                engine='openpyxl',
                                # only load the columns we actually need
                                usecols=['FileName', 'Latitude'],
                                )

    def lookup_latitude(self, base_name: str) -> float:
        """Lookup the latitude for the CTD file base name.
        Raises LookupError if not found or multiple found.
        """

        # lazy load the dataframe.
        if not hasattr(self, 'df'):
            self.refresh()

        hex_name = f'{base_name}.hex'

        matching = self.df.loc[self.df['FileName'] == hex_name, 'Latitude']

        if len(matching) == 0:
            raise LookupError(f'No latitude found for {hex_name}')
        elif len(matching) > 1:
            raise LookupError(f'Multiple latitudes found for {hex_name}')

        lat = float(matching.values[0])
        print(f'Latitude for {hex_name}: {lat} (from spreadsheet)')
        return lat
