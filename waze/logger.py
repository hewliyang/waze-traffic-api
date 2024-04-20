import sys
import logging
from logging import Logger
from typing import Literal, Optional


def get_logger(
    verbosity: Optional[Literal["quiet", "verbose", "normal"]] = "normal",
    name: str = "waze",
) -> Logger:
    """Returns a configured logger.Logger object which logs to stderr

    Args:
            verbosity (str, optional): verbose <=> debug/info,
                normal <=> warnings only, quiet <=> shows nothing. Defaults to "quiet".
            name (str, optional): logger name. Defaults to "waze".

    Returns:
            Logger: Configured logger.Logger object
    """
    logger = logging.getLogger(name)
    logger.handlers = []
    handler = logging.StreamHandler(sys.stderr)

    logger.setLevel(logging.WARNING)
    if verbosity == "verbose":
        logger.setLevel(logging.DEBUG)
    elif verbosity == "quiet":
        handler = logging.NullHandler()

    handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    return logger
