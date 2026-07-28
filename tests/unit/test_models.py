import pytest
from datetime import datetime, timezone
from src.smart_alerts.models import Alert, Severity

def test_valid_severity():
    """Test 11: Severidad válida."""
    alert = Alert("R01", "S01", "Title", "Desc", "BAJA")
    assert alert.severity == Severity.BAJA
    
    alert = Alert("R01", "S01", "Title", "Desc", "MEDIA")
    assert alert.severity == Severity.MEDIA

def test_invalid_severity():
    """Test 12: Severidad inválida (Lanza ValueError)."""
    with pytest.raises(ValueError):
        Alert("R01", "S01", "Title", "Desc", "INEXISTENTE")

def test_normalize_critical():
    """Test 13: Normalización de CRÍTICA."""
    alert1 = Alert("R01", "S01", "Title", "Desc", "CRÍTICA")
    assert alert1.severity == Severity.CRITICA
    
    alert2 = Alert("R01", "S01", "Title", "Desc", "CRITICAL")
    assert alert2.severity == Severity.CRITICA
    
    alert3 = Alert("R01", "S01", "Title", "Desc", "CRITICA")
    assert alert3.severity == Severity.CRITICA

def test_timestamp_with_timezone():
    """Test 16: Timestamp con timezone."""
    now_tz = datetime.now(timezone.utc)
    alert = Alert("R01", "S01", "Title", "Desc", "BAJA", occurred_at=now_tz)
    assert alert.occurred_at.tzinfo is not None
