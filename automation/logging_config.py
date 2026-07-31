import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging():
    """
    Configure console and rotating file logging.

    Returns:
        logging.Logger: Configured application logger.
    """

    logs_directory = Path(__file__).parent / "logs"
    logs_directory.mkdir(exist_ok=True)

    logger = logging.getLogger("ec2_resize")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        logs_directory / "resize_instances.log",
        maxBytes=5_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger