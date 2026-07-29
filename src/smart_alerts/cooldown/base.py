from abc import ABC, abstractmethod


class CooldownManager(ABC):
    """
    Interfaz base para la gestión de cooldown de alertas.
    Permite implementaciones en memoria, base de datos o Redis.
    """

    @abstractmethod
    def is_in_cooldown(self, alert_id: str) -> bool:
        """
        Verifica si una alerta está en cooldown.
        No modifica el registro de cooldown.
        """

    @abstractmethod
    def mark_as_sent(self, alert_id: str) -> None:
        """
        Registra el envío exitoso de una alerta, activando su cooldown.
        """

    @abstractmethod
    def cleanup(self) -> None:
        """
        Limpia registros de cooldown antiguos para liberar espacio.
        """
