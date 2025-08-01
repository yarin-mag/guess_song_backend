import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

logger = logging.getLogger("Backend")

def log_info(message: str):
    logger.info(message)


def log_error(message: str):
    logger.error(message)


def log_debug(message: str):
    logger.debug(message)

def log_action(actor: str, action: str, context: dict = None):
    message = f"📌 Action by {actor}: {action}"
    if context:
        message += f" | Context: {context}"
    logger.info(message)
