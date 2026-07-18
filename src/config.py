from src.models import SensorConfig

def get_sensor_configs() -> list[SensorConfig]:
    """
    Simula la carga de configuraciones por sensor.
    En una fase posterior esto vendrá de una base de datos o archivo JSON.
    """
    return [
        SensorConfig(
            sensor_id="SH2O-ZA-001",
            zone="Sanitarios piso 1",
            critical_flow_threshold=20.0,
            off_hours_flow_threshold=5.0,
            daily_volume_limit=1000.0,
            operating_start_hour=7,
            operating_end_hour=19,
            critical_persistence_seconds=600,
            off_hours_persistence_seconds=300,
            offline_timeout_seconds=600
        ),
        SensorConfig(
            sensor_id="SH2O-ZB-001",
            zone="Cocina / comedor institucional",
            critical_flow_threshold=25.0,
            off_hours_flow_threshold=5.0,
            daily_volume_limit=800.0,
            operating_start_hour=11,
            operating_end_hour=16,
            critical_persistence_seconds=600,
            off_hours_persistence_seconds=300,
            offline_timeout_seconds=600
        )
    ]
