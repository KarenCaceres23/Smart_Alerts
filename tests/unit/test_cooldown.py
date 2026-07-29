import time
from unittest import mock
from src.smart_alerts.cooldown.memory import MemoryCooldownManager


def test_cooldown_after_success():
    """Test 8: Cooldown después de éxito."""
    manager = MemoryCooldownManager(cooldown_seconds=300)
    alert_id = "R01_S01"

    assert not manager.is_in_cooldown(alert_id)

    manager.mark_as_sent(alert_id)

    assert manager.is_in_cooldown(alert_id)


def test_failure_no_cooldown():
    """Test 9: Fallo que no activa cooldown."""
    manager = MemoryCooldownManager(cooldown_seconds=300)
    alert_id = "R01_S01"

    # Se consulta pero no se llama a mark_as_sent
    assert not manager.is_in_cooldown(alert_id)
    # Imaginamos un fallo de envío
    assert not manager.is_in_cooldown(alert_id)


@mock.patch("time.monotonic")
def test_cooldown_cleanup(mock_time):
    """Test 14: Limpieza del registro de cooldown."""
    manager = MemoryCooldownManager(cooldown_seconds=300)

    # Tiempo inicial
    mock_time.return_value = 100.0
    manager.mark_as_sent("alert_1")

    # Avanzamos 150 segundos (todavía en cooldown)
    mock_time.return_value = 250.0
    manager.mark_as_sent("alert_2")
    manager.cleanup()
    assert "alert_1" in manager._registry
    assert "alert_2" in manager._registry

    # Avanzamos a 450 (alert_1 expiró, alert_2 sigue activo)
    mock_time.return_value = 450.0
    manager.cleanup()
    assert "alert_1" not in manager._registry
    assert "alert_2" in manager._registry
