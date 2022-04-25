from django.apps import AppConfig


class StoreAppConfig(AppConfig):

    name = 'store'

    def ready(self):
        import store.signals
