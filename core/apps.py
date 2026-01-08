from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        """Run when Django starts"""
        # Register integration providers
        from integrations.registry import register_default_providers
        register_default_providers()
