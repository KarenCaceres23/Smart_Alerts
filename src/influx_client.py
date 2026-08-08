import logging
import os
import re

# NOTE: HttpValidationError no existe en las versiones recientes de
# influxdb-client (>=1.40); solo InfluxDBError es el nombre público.
from influxdb_client import InfluxDBClient
from influxdb_client.client.exceptions import InfluxDBError

from src.smart_alerts.models import SensorReading

logger = logging.getLogger(__name__)


class InfluxClientError(Exception):
    """Excepción personalizada para errores del cliente InfluxDB."""


class InfluxSensorRepository:
    """
    Repositorio para consultar métricas de sensores en InfluxDB.

    Proporciona una interfaz segura y validada para consultas a InfluxDB
    con reconexión automática y manejo de errores robusto.
    """

    # Patrón para validar URL de InfluxDB
    URL_PATTERN = re.compile(r"^https?://[a-zA-Z0-9][\w.-]+(:\d+)?(/.*)?$")

    def __init__(
        self,
        url: str | None = None,
        token: str | None = None,
        org: str | None = None,
        bucket: str | None = None,
    ):
        self._url = self._validate_url(url or os.getenv("INFLUXDB_URL", "http://localhost:8086"))
        self._token = (
            (token or os.getenv("INFLUXDB_TOKEN", "")).strip()
            if token
            else os.getenv("INFLUXDB_TOKEN", "").strip()
        )
        self._org = (
            (org or os.getenv("INFLUXDB_ORG", "")).strip()
            if org
            else os.getenv("INFLUXDB_ORG", "").strip()
        )
        self._bucket = (
            (bucket or os.getenv("INFLUXDB_BUCKET", "")).strip()
            if bucket
            else os.getenv("INFLUXDB_BUCKET", "").strip()
        )

        self.measurement = os.getenv("INFLUXDB_MEASUREMENT", "water_flow").strip() or "water_flow"
        self.flow_field = os.getenv("INFLUXDB_FLOW_FIELD", "flow_rate").strip() or "flow_rate"

        # Internamente el código utiliza 'daily_volume' para el modelo.
        # En InfluxDB esto se asocia con el campo real, por ejemplo 'cumulative_volume',
        # mediante la variable de entorno INFLUXDB_VOLUME_FIELD.
        self.volume_field = (
            os.getenv("INFLUXDB_VOLUME_FIELD", "daily_volume").strip() or "daily_volume"
        )

        self._client: InfluxDBClient | None = None
        self._query_api = None
        self._connected = False

        # Solo inicializar si hay token válido
        if self._token:
            self._initialize_client()
        else:
            logger.warning(
                "INFLUXDB_TOKEN no configurado. Las consultas a InfluxDB estarán deshabilitadas."
            )

    def _validate_url(self, url: str) -> str:
        """Valida el formato de la URL de InfluxDB."""
        if not url:
            raise ValueError("URL de InfluxDB no puede estar vacía")
        if not self.URL_PATTERN.match(url):
            raise ValueError(f"URL de InfluxDB inválida: {url}")
        return url

    def _initialize_client(self) -> bool:
        """
        Inicializa el cliente InfluxDB con manejo de errores.
        Retorna True si la inicialización fue exitosa.
        """
        try:
            self._client = InfluxDBClient(
                url=self._url,
                token=self._token,
                org=self._org,
            )
            self._query_api = self._client.query_api()

            # Verificar conexión con una consulta ligera
            if self._test_connection():
                self._connected = True
                logger.info(f"Conectado a InfluxDB en {self._url}")
                return True
            return False

        except InfluxDBError as e:
            logger.error(f"Error de conexión/validación HTTP al conectar a InfluxDB: {e}")
            self._cleanup_client()
            return False
        except Exception as e:
            logger.error(f"Error inesperado al inicializar InfluxDB: {e}")
            self._cleanup_client()
            return False

    def _test_connection(self) -> bool:
        """Prueba la conexión con una consulta ligera."""
        if not self._query_api:
            return False
        try:
            # Realizar una consulta mínima
            query = f'from(bucket: "{self._bucket}") |> range(start: -1m) |> limit(n: 1)'
            self._query_api.query(query, org=self._org)
            return True
        except Exception as e:
            logger.debug(f"Prueba de conexión fallida: {e}")
            return False

    def _cleanup_client(self) -> None:
        """Limpia referencias al cliente de forma segura."""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.debug(f"Error al cerrar cliente (ignorado): {e}")
        self._client = None
        self._query_api = None
        self._connected = False

    def get_latest_reading(
        self, sensor_id: str, zone: str, time_window_minutes: int = 15
    ) -> SensorReading | None:
        """
        Obtiene la lectura más reciente de un sensor dentro de una ventana de tiempo.

        Args:
            sensor_id: ID del sensor a consultar
            zone: Zona donde se encuentra el sensor
            time_window_minutes: Ventana de tiempo en minutos (default: 15)

        Returns:
            SensorReading si se encuentra, None en caso contrario
        """
        if not self.is_connected():
            logger.warning(
                f"Cliente InfluxDB no conectado. Retornando None para sensor {sensor_id}."
            )
            return None

        # Validar parámetros
        if not sensor_id or not zone:
            logger.warning("sensor_id y zone son obligatorios")
            return None

        if time_window_minutes <= 0 or time_window_minutes > 1440:  # Max 24 horas
            logger.warning(f"time_window_minutes fuera de rango: {time_window_minutes}")
            time_window_minutes = min(max(time_window_minutes, 1), 1440)

        # Consulta Flux
        query = f"""
        from(bucket: "{self._bucket}")
          |> range(start: -{time_window_minutes}m)
          |> filter(fn: (r) => r["_measurement"] == "{self.measurement}")
          |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
          |> sort(columns: ["_time"], desc: true)
          |> limit(n: 1)
        """

        try:
            result = self._query_api.query(query, org=self._org)

            if not result or not result[0].records:
                logger.debug(f"No se encontraron lecturas para {sensor_id}")
                return None

            record = result[0].records[0]
            values = record.values

            # Extraer campos
            flow_rate = self._safe_get_float(values, self.flow_field)
            daily_volume = self._safe_get_float(values, self.volume_field)
            timestamp = record.get_time()

            # Asegurar valores no negativos
            flow_rate = max(0.0, flow_rate) if flow_rate is not None else None
            daily_volume = max(0.0, daily_volume) if daily_volume is not None else None

            return SensorReading(
                sensor_id=sensor_id,
                zone=zone,
                timestamp=timestamp,
                flow_rate=flow_rate,
                daily_volume=daily_volume,
            )

        except InfluxDBError as e:
            logger.error(f"Error de conexión al consultar InfluxDB para {sensor_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al procesar lectura de {sensor_id}: {e}")
            return None

    def _safe_get_float(self, values: dict, key: str) -> float | None:
        """Extrae un valor flotante de forma segura."""
        value = values.get(key)
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def is_connected(self) -> bool:
        """Verifica si el cliente está conectado y listo para uso."""
        if not self._connected and self._client is None and self._token:
            self._initialize_client()
        return self._connected and self._query_api is not None

    def close(self) -> None:
        """Cierra el cliente de InfluxDB de forma segura."""
        if self._client:
            try:
                self._client.close()
            except Exception as e:
                logger.debug(f"Error al cerrar cliente (ignorado): {e}")
        self._cleanup_client()

    def reconnect(self) -> bool:
        """Intenta reconectar el cliente si está desconectado."""
        if self._token:
            logger.info("Intentando reconexión a InfluxDB...")
            return self._initialize_client()
        return False
