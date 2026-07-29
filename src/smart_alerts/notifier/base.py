from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.smart_alerts.models import Alert, SendStatus


@dataclass
class NotifierResult:
    """Resultado estructurado del intento de envío de una notificación."""

    status: SendStatus
    attempts: int
    status_code: int | None = None
    error: str | None = None
    skipped_by_cooldown: bool = False


class BaseNotifier(ABC):
    """
    Interfaz base para todos los notificadores.
    """

    @abstractmethod
    def send(self, alert: Alert) -> NotifierResult:
        """
        Intenta enviar una alerta.
        """
