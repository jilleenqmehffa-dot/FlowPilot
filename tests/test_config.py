import os
import unittest
from unittest.mock import patch

from backend.app.core.config import Settings, get_settings
from backend.app.db.database import get_engine


class SettingsTests(unittest.TestCase):
    def tearDown(self) -> None:
        get_settings.cache_clear()
        get_engine.cache_clear()

    def test_defaults_do_not_require_environment_variables(self):
        settings = Settings(_env_file=None)

        self.assertEqual(settings.app_name, "FlowPilot")
        self.assertIsNone(settings.database_url)
        self.assertEqual(settings.celery_broker_url, "redis://localhost:6379/0")
        self.assertEqual(settings.celery_result_backend, "redis://localhost:6379/1")

    def test_settings_are_loaded_from_environment_and_cached(self):
        environment = {
            "APP_NAME": "FlowPilot Test",
            "DATABASE_URL": "postgresql+psycopg://user:pass@localhost/test",
            "CELERY_BROKER_URL": "redis://redis:6379/2",
            "CELERY_RESULT_BACKEND": "redis://redis:6379/3",
        }
        with patch.dict(os.environ, environment, clear=True):
            first = get_settings()
            second = get_settings()

        self.assertIs(first, second)
        self.assertEqual(first.app_name, "FlowPilot Test")
        self.assertEqual(first.database_url, environment["DATABASE_URL"])
        self.assertEqual(first.celery_broker_url, environment["CELERY_BROKER_URL"])
        self.assertEqual(first.celery_result_backend, environment["CELERY_RESULT_BACKEND"])

    def test_database_configuration_remains_lazy(self):
        empty_settings = Settings(_env_file=None)
        with patch("backend.app.db.database.get_settings", return_value=empty_settings):
            with self.assertRaisesRegex(RuntimeError, "Set DATABASE_URL"):
                get_engine()


if __name__ == "__main__":
    unittest.main()
