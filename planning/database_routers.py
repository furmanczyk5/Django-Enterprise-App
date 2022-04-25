import random


class MasterSlaveRouter(object):
    def db_for_read(self, model, **hints):
        """
        Reads go to a randomly-chosen slave.
        """
        if model._meta.app_label == "imis":
            return "MSSQL"

        return 'default'
        #return random.choice(['default', 'slave1'])

    def db_for_write(self, model, **hints):
        """
        Writes always go to master.
        """
        if model._meta.app_label == "imis":
            return "MSSQL"
            
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Relations between objects are allowed if both objects are
        in the master/slave pool.
        """
        db_list = ('default', 'slave1',)
        if obj1._state.db in db_list and obj2._state.db in db_list:
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Explicitly put all models on all databases."
        """
        if db == 'MSSQL':
            return False
        return True

