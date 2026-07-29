import logging
import os

from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError

from src.smart_alerts.models import SensorReading

logger = logging.getLogger(__name__)


class InfluxSensorRepository:
    """Repositorio para consultar métricas de sensores en InfluxDB."""

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        org: str | None = None,
        bucket: str | None = None,
    ):
        self.url = url or os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = token or os.getenv("INFLUXDB_TOKEN", "")
        self.org = org or os.getenv("INFLUXDB_ORG", "")
        self.bucket = bucket or os.getenv("INFLUXDB_BUCKET", "")

        self.measurement = os.getenv("INFLUXDB_MEASUREMENT", "water_flow")
        self.flow_field = os.getenv("INFLUXDB_FLOW_FIELD", "flow_rate")
        self.volume_field = os.getenv("INFLUXDB_VOLUME_FIELD", "daily_volume")

        self.client = None
        self.query_api = None

        if self.token:
            try:
                self.client = InfluxDBClient(url=self.url, token=self.token, org=self.org)
                self.query_api = self.client.query_api()
            except Exception:
                logger.error("Error al inicializar el cliente InfluxDB")

    def get_latest_reading(
        self, sensor_id: str, zone: str, time_window_minutes: int = 15
    ) -> SensorReading | None:
        """Obtiene la lectura más reciente de un sensor dentro de una ventana de tiempo."""
        if not self.query_api:
            logger.warning(
                f"Cliente InfluxDB no configurado. Retornando None para sensor {sensor_id}."
            )
            return None

        # Consulta Flux base
        query = f"""
        from(bucket: "{self.bucket}")
          |> range(start: -{time_window_minutes}m)
          |> filter(fn: (r) => r["_measurement"] == "{self.measurement}")
          |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 1)
        """

        try:
            result = self.query_api.query(query, org=self.org)

            if not result or not result[0].records:
                return None

            record = result[0].records[0]
            values = record.values

            # Extraer campos
            flow_rate = values.get(self.flow_field)
            daily_volume = values.get(self.volume_field)
            timestamp = record.get_time()

            # Asegurar que no sean negativos
            if flow_rate is not None and flow_rate < 0:
                flow_rate = 0.0
            if daily_volume is not None and daily_volume < 0:
                daily_volume = 0.0

            return SensorReading(
                sensor_id=sensor_id,
                zone=zone,
                timestamp=timestamp,
                flow_rate=flow_rate,
                daily_volume=daily_volume,
            )

        except InfluxDBError as e:
            logger.error(f"Error de conexión al consultar InfluxDB para {sensor_id}: {e!s}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al procesar lectura de {sensor_id}: {e!s}")
            return None

    def close(self):
        """Cierra el cliente de InfluxDB de forma segura."""
        if self.client:
            self.client.close()
            self.client = None
