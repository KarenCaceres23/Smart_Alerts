import logging
import logging.config
import os
import pytz
from datetime import datetime

class TimezoneFormatter(logging.Formatter):
    """
    Formatter personalizado para inyectar zona horaria en los logs y
    enmascarar tokens sensibles.
    """
    def __init__(self, fmt=None, datefmt=None, tz_str=None, mask_token=None):
        super().__init__(fmt, datefmt)
        self.tz = pytz.timezone(tz_str) if tz_str else pytz.utc
        self.mask_token = mask_token

    def converter(self, timestamp):
        dt = datetime.fromtimestamp(timestamp, tz=pytz.utc)
        return dt.astimezone(self.tz)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

    def format(self, record):
        formatted_message = super().format(record)
        if self.mask_token and self.mask_token in formatted_message:
            formatted_message = formatted_message.replace(self.mask_token, "***TOKEN_OCULTO***")
        return formatted_message

def setup_logging(level_str="INFO", tz_str="UTC", mask_token=None):
    """Configura el sistema de logs con zona horaria y enmascaramiento."""
    level = getattr(logging, level_str.upper(), logging.INFO)
    
    formatter = TimezoneFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        tz_str=tz_str,
        mask_token=mask_token
    )
    
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    
    root_logger = logging.getLogger()
    # Limpiar handlers previos para no duplicar
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.setLevel(level)
    root_logger.addHandler(handler)
