import logging
import logging.config
import os
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler

import pytz

# Singleton para evitar múltiples configuraciones
_logging_configured = False

logger = logging.getLogger(__name__)


class TimezoneFormatter(logging.Formatter):
    """
    Formatter personalizado para inyectar zona horaria en los logs y
    enmascarar tokens sensibles.
    """

    # Regex para detectar tokens (bearer tokens, API keys, etc.)
    TOKEN_PATTERN = re.compile(r"(?:bearer\s+|token[=:\s]*)([a-zA-Z0-9_\-]{20,})", re.IGNORECASE)

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = None,
        tz_str: str | None = None,
        mask_token: str | None = None,
    ):
        super().__init__(fmt, datefmt)
        try:
            self.tz = pytz.timezone(tz_str) if tz_str else pytz.UTC
        except pytz.exceptions.UnknownTimeZoneError:
            self.tz = pytz.UTC
        self.mask_token = mask_token

    def converter(self, timestamp) -> datetime:
        """Convierte timestamp a datetime en la zona horaria configurada."""
        dt = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
        return dt.astimezone(self.tz)

    def formatTime(self, record, datefmt=None) -> str:
        """Formatea el tiempo con zona horaria correcta."""
        dt = self.converter(record.created)
        if datefmt:
            return dt.strftime(datefmt)
        return dt.isoformat()

    def format(self, record) -> str:
        """Formatea el mensaje y aplica enmascaramiento de tokens."""
        formatted_message = super().format(record)

        if self.mask_token:
            # Enmascarar tokens específicos
            formatted_message = formatted_message.replace(self.mask_token, "***TOKEN_OCULTO***")

        # También limpiar tokens detectados por patrón
        if self.TOKEN_PATTERN.search(formatted_message):
            formatted_message = self.TOKEN_PATTERN.sub(
                lambda m: m.group(0).split()[-1][:10] + "***", formatted_message
            )

        return formatted_message


def setup_logging(
    level_str: str = "INFO",
    tz_str: str = "UTC",
    mask_token: str | None = None,
    log_file: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Configura el sistema de logs con zona horaria, enmascaramiento y rotación.

    Args:
        level_str: Nivel de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        tz_str: Zona horaria para los timestamps
        mask_token: Token a enmascarar en los logs
        log_file: Ruta del archivo de log (opcional, si se especifica usa RotatingFileHandler)
        max_bytes: Tamaño máximo del archivo de log antes de rotar
        backup_count: Número máximo de archivos de respaldo a mantener
    """
    global _logging_configured

    # Evitar configurar múltiples veces (singleton pattern)
    if _logging_configured:
        return

    # Validar nivel de log
    level = getattr(logging, level_str.upper(), logging.INFO)
    if not isinstance(level, int):
        level = logging.INFO

    # Validar zona horaria
    try:
        pytz.timezone(tz_str)
    except pytz.exceptions.UnknownTimeZoneError:
        tz_str = "UTC"

    formatter = TimezoneFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        tz_str=tz_str,
        mask_token=mask_token,
    )

    # Limpiar handlers previos para no duplicar
    root_logger = logging.getLogger()
    if root_logger.handlers:
        for handler in root_logger.handlers[:]:
            try:
                handler.close()
                root_logger.removeHandler(handler)
            except Exception as e:
                logger.debug(f"No se pudo cerrar un handler previo (ignorado): {e}")

    # Crear handler de consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    handlers = [console_handler]

    # Opcionalmente agregar archivo con rotación
    if log_file:
        try:
            # Asegurar directorio existe
            log_path = os.path.abspath(log_file)
            log_dir = os.path.dirname(log_path)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)
        except OSError as e:
            logger.warning(f"No se pudo crear archivo de log: {e}")

    # Configurar nivel y handlers
    root_logger.setLevel(level)
    for handler in handlers:
        root_logger.addHandler(handler)

    _logging_configured = True


def reset_logging() -> None:
    """
    Reinicia la configuración de logging.
    Útil para pruebas o reciclaje de configuración.
    """
    global _logging_configured

    # Limpiar todos los handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        try:
            handler.close()
            root_logger.removeHandler(handler)
        except Exception as e:
            logger.debug(f"No se pudo cerrar un handler al resetear (ignorado): {e}")

    # Limpiar loggers existentes
    logging.Logger.manager.loggerDict.clear()

    # Resetear el estado
    _logging_configured = False
