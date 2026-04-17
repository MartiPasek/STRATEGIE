import logging
import sys
from core.config import settings


def setup_logging() -> None:
    """
    Inicializuje logování. Bezpečné pro opakované volání (reload, testy).
    Pokud root logger už má handlery, nic nepřidává.
    """
    root = logging.getLogger()

    if root.handlers:
        return

    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
