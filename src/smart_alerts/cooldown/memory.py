import time
from typing import Dict
from .base import CooldownManager

class MemoryCooldownManager(CooldownManager):
    """
    Implementación en memoria del gestor de cooldown.
    Usado para desarrollo y casos donde no se requiere persistencia distribuida.
    """
    def __init__(self, cooldown_seconds: int):
        self.cooldown_seconds = cooldown_seconds
        # Mapea alert_id -> timestamp (time.monotonic())
        self._registry: Dict[str, float] = {}
        
    def is_in_cooldown(self, alert_id: str) -> bool:
        current_time = time.monotonic()
        
        if alert_id in self._registry:
            last_sent = self._registry[alert_id]
            if current_time - last_sent < self.cooldown_seconds:
                return True
                
        return False
        
    def mark_as_sent(self, alert_id: str) -> None:
        self._registry[alert_id] = time.monotonic()
        
    def cleanup(self) -> None:
        """
        Elimina registros cuyo tiempo ya ha excedido el cooldown configurado.
        Esto previene fugas de memoria en ejecuciones prolongadas.
        """
        current_time = time.monotonic()
        expired_keys = [
            k for k, last_sent in self._registry.items()
            if current_time - last_sent >= self.cooldown_seconds
        ]
        for k in expired_keys:
            del self._registry[k]
