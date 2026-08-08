import os
import sys
import time
from datetime import datetime, timezone

from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Asegurar que la raíz del proyecto está en el PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.main import MonitoringService


def write_reading(write_api, bucket, org, measurement, sensor_id, flow_rate, daily_volume):
    point = (
        Point(measurement)
        .tag("sensor_id", sensor_id)
        .field("flow_rate", float(flow_rate))
        .field("daily_volume", float(daily_volume))
        .time(datetime.now(timezone.utc))
    )
    write_api.write(bucket=bucket, org=org, record=point)
    print(f"[*] Dato escrito en InfluxDB: Flow={flow_rate} L/min")


def run():
    # Cargar variables de entorno de integración
    load_dotenv(".env.integration")

    url = os.getenv("INFLUXDB_URL")
    token = os.getenv("INFLUXDB_TOKEN")
    org = os.getenv("INFLUXDB_ORG")
    bucket = os.getenv("INFLUXDB_BUCKET")
    measurement = os.getenv("INFLUXDB_MEASUREMENT")

    # Configuraremos el sensor que existe en main.py: "SH2O-ZA-001"
    sensor_id = "SH2O-ZA-001"

    print("\n=== INICIANDO PRUEBA DE INTEGRACIÓN END-TO-END ===")

    client = InfluxDBClient(url=url, token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    # Inicializar el servicio con el estado (debounce, cooldown)
    service = MonitoringService()
    # Evitamos que run_detection_cycle cierre la conexión a la base de datos
    # para poder llamarlo varias veces manteniendo el estado de memoria (debounce/cooldown).
    original_close = service.repository.close
    service.repository.close = lambda: None

    print("\n--- ESCENARIO 1: LECTURA NORMAL ---")
    write_reading(write_api, bucket, org, measurement, sensor_id, 10.0, 500.0)
    time.sleep(1)  # Dar tiempo a InfluxDB
    service.run_detection_cycle()

    print("\n--- ESCENARIO 2: LECTURA ANÓMALA (INICIA DEBOUNCE) ---")
    write_reading(write_api, bucket, org, measurement, sensor_id, 30.0, 500.0)
    time.sleep(1)
    service.run_detection_cycle()

    print("\n--- ESPERANDO QUE EL DEBOUNCE TERMINE (> 5 segs) ---")
    time.sleep(6)

    print("\n--- ESCENARIO 3: ANOMALÍA PERSISTE (ENVÍA ALERTA TELEGRAM) ---")
    write_reading(write_api, bucket, org, measurement, sensor_id, 35.0, 500.0)
    time.sleep(1)
    service.run_detection_cycle()

    print("\n--- ESCENARIO 4: ANOMALÍA SIGUE (SUPRIMIDA POR COOLDOWN) ---")
    write_reading(write_api, bucket, org, measurement, sensor_id, 40.0, 500.0)
    time.sleep(1)
    service.run_detection_cycle()

    print("\n--- ESCENARIO 5: RECUPERACIÓN PARCIAL A LECTURA NORMAL (R01 se resuelve) ---")
    write_reading(write_api, bucket, org, measurement, sensor_id, 12.0, 500.0)
    time.sleep(1)
    service.run_detection_cycle()

    print("\n--- ESCENARIO 6: RECUPERACIÓN TOTAL A LECTURA NORMAL (R02 se resuelve) ---")
    write_reading(write_api, bucket, org, measurement, sensor_id, 3.0, 500.0)
    time.sleep(1)
    service.run_detection_cycle()

    client.close()
    print("\n=== PRUEBA DE INTEGRACIÓN COMPLETADA ===")
    print("Revisa tu Telegram y el archivo audit_integration.jsonl")


if __name__ == "__main__":
    run()
