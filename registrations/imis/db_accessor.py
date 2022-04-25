import pyodbc
from django.conf import settings
from sentry_sdk import capture_exception


class DbAccessor:

    @staticmethod
    def connection_config():
        config = getattr(settings, "DATABASES").get("MSSQL")
        return (
            'DRIVER={0};SERVER={1};PORT={2};'
            'DATABASE=imis_live;UID={3};PWD={4};'
            'TDS_Version=7.4'
        ).format(
            '{FreeTDS}',
            config.get('HOST'),
            config.get('PORT'),
            config.get('USER'),
            config.get('PASSWORD')
        )

    def connect(self):
        config_string = self.connection_config()
        self.connection = pyodbc.connect(config_string, autocommit=True)
        self.cursor = self.connection.cursor()

    def close(self):
        self.cursor.close()
        self.cursor = None
        self.connection.close()
        
    def execute(self, query, parameters):
        self.connect()
        result = self.cursor.execute(query, parameters)
        self.close()
        return result

    def get_row(self, query, parameters):
        self.connect()
        try:
            result = self.cursor.execute(query, parameters).fetchone()
        except Exception as e:
            capture_exception(e)
            result = []  
        self.close()
        return result

    def get_rows(self, query, parameters):
        self.connect()
        try:
            result = self.cursor.execute(query, parameters).fetchall()
        except Exception as e:
            capture_exception(e)
            result = []
        self.close()
        return result
