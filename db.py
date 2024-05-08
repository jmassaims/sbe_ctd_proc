import pandas as pd
import sqlalchemy as sa


def get_db_tables(db_file, mdw_file, db_user, db_password):
    # import ipdb; ipdb.set_trace()
    db_driver = r"{Microsoft Access Driver (*.mdb, *.accdb)}"
    if mdw_file is None:
        cnxn_str = (
            f"DRIVER={db_driver};"
            f"DBQ={db_file};"
            f"SYSTEMDB={mdw_file};"
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
    # import ipdb; ipdb.set_trace()
    connection_url = sa.engine.URL.create("access+pyodbc", username=db_user, password=db_password, query={"odbc_connect": cnxn_str})

    engine = sa.engine.create_engine(connection_url)
    #print(engine)
    with engine.connect() as conn:
        db_FieldTrips = pd.read_sql('SELECT * FROM FieldTrip', engine, parse_dates=['DateStart', 'DateEnd'])
        db_Sites = pd.read_sql('SELECT * FROM Sites', engine)
        db_DeploymentData = pd.read_sql('SELECT * FROM DeploymentData', engine, parse_dates=['TimeDriftGPS', 'TimeFirstGoodData', 'TimeLastGoodData', 'TimeSwitchOff',
                            'TimeDriftInstrument', 'TimeFirstInPos', 'TimeLastInPos', 'TimeSwitchOn'
                            'TimeEstimatedRetrieval', 'TimeFirstWet', 'TimeOnDeck'])
        db_Instruments = pd.read_sql('SELECT * FROM Instruments', engine)
        db_CTDData = pd.read_sql('SELECT * FROM CTDData', engine)
    engine.dispose()
    return db_FieldTrips, db_Sites, db_DeploymentData, db_Instruments, db_CTDData