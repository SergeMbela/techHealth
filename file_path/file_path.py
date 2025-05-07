import os

etlfile = os.environ.get("ETL_CSV_FILE")

class FilePath:
    def __init__(self, etlfile=etlfile):
        self.etlfile = etlfile

    def get_etlfile(self):
        return self.etlfile