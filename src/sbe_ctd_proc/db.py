import os.path as P
import pandas as pd
import sqlalchemy as sa

class OceanDB:
    def __init__(self, db_file, mdw_file, db_user, db_password) -> None:
        db_driver = r"{Microsoft Access Driver (*.mdb, *.accdb)}"
        if mdw_file is None:
            cnxn_str = (
                f"DRIVER={db_driver};"
                f"DBQ={db_file};"
                f"UID={db_user};"
                f"PWD={db_password};"
                f"READONLY=TRUE;"
                f"ExtendedAnsiSQL=1;"
            )
        else:
            cnxn_str = (
                f"DRIVER={db_driver};"
                f"DBQ={db_file};"
                f"SYSTEMDB={mdw_file};"
                f"UID={db_user};"
                f"PWD={db_password};"
                f"READONLY=TRUE;"
                f"ExtendedAnsiSQL=1;"
            )

        self.connection_url = sa.engine.URL.create("access+pyodbc", username=db_user, password=db_password, query={"odbc_connect": cnxn_str})

    # TODO private
    def get_db_tables(self):
        """load and store the tables needed for OceanDB methods"""

        engine = sa.engine.create_engine(self.connection_url)

        with engine.connect() as conn:
            self.field_trip = pd.read_sql('SELECT * FROM FieldTrip', engine, parse_dates=['DateStart', 'DateEnd'])
            self.sites = pd.read_sql('SELECT * FROM Sites', engine)
            self.deployment_data = pd.read_sql('SELECT * FROM DeploymentData', engine, parse_dates=['TimeDriftGPS', 'TimeFirstGoodData', 'TimeLastGoodData', 'TimeSwitchOff',
                                'TimeDriftInstrument', 'TimeFirstInPos', 'TimeLastInPos', 'TimeSwitchOn'
                                'TimeEstimatedRetrieval', 'TimeFirstWet', 'TimeOnDeck'])
            self.instruments = pd.read_sql('SELECT * FROM Instruments', engine)
            self.ctd_data = pd.read_sql('SELECT * FROM CTDData', engine)

        engine.dispose()

    def lookup_latitude(self, base_file_name) -> float:
        """"Get the latitutude for the file name
        :param base_file_name
        """
        if base_file_name.endswith(".hex"):
            raise Exception("expected base file name, shouldn't have .hex extension")

        if not hasattr(self, "ctd_data"):
            self.get_db_tables()

        ctd_data = self.ctd_data

        ctd_deployment = ctd_data[
            ctd_data['FileName'].str.contains(f'^{base_file_name + ".hex"}', case=False, regex=True,
                                                na=False)]
        if not ctd_deployment.empty:
            # hex filename in db
            latitude = str(ctd_deployment['Latitude'].values[0])
            print(
                f"Using latitude = {latitude} from site = {ctd_deployment['Site'].values[0]}, station = {ctd_deployment['Station'].values[0]}")
        else:
            # maybe has been processed in the past so db filename includes processing steps appended
            ctd_deployment = ctd_data[
                ctd_data['FileName'].str.contains(f'^{base_file_name}', regex=True, na=False)]

            if len(ctd_deployment) == 1:
                latitude = str(ctd_deployment['Latitude'].values[0])
                print(
                    f"Using latitude = {latitude} from site = {ctd_deployment['Site'].values[0]}, station = {ctd_deployment['Station'].values[0]}")
            else:
                # filename not in the db
                raise LookupError(f"no latitude found in database for '{base_file_name}'")

        return float(latitude)
