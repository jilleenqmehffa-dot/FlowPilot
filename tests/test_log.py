import logging
import unittest
from unittest.mock import patch

from backend.app.core.log import LOG_DATE_FORMAT, LOG_FORMAT, configure_logging


class LoggingTests(unittest.TestCase):
    @patch("backend.app.core.log.logging.getLogger")
    @patch("backend.app.core.log.logging.basicConfig")
    def test_configure_logging_sets_format_and_root_level(self, basic_config, get_logger):
        configure_logging("DEBUG")

        basic_config.assert_called_once_with(
            level="DEBUG",
            format=LOG_FORMAT,
            datefmt=LOG_DATE_FORMAT,
        )
        get_logger.return_value.setLevel.assert_called_once_with("DEBUG")


if __name__ == "__main__":
    unittest.main()
