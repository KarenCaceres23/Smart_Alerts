import os
import html
import time
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict

import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

class Severity(str, Enum):
    """Enumeración para los niveles de severidad admitidos."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class SendStatus(str, Enum):
    """Enumeración para los posibles estados de envío de una alerta."""
    SENT = "sent"
    SUPPRESSED = "suppressed"
    FAILED = "failed"

@dataclass(frozen=True)
class Alert:
    """
    Estructura de datos inmutable para estandarizar la información de las alertas.
    
    Atributos:
        rule_id (str): Identificador de la regla que disparó la alerta (ej. 'R01').
        sensor_id (str): Identificador único del sensor.
        zone (str): Ubicación física del sensor.
        value (float | None): Valor actual medido que disparó la regla.
        threshold (float | None): Valor límite esperado para esa regla.
        severity (Severity): Nivel de severidad de la alerta.
        description (str): Descripción humana del evento anómalo.
        recommended_action (str): Acción sugerida para el operador.
    """
    rule_id: str
    sensor_id: str
    zone: str
    value: float | None
    threshold: float | None
    severity: Severity
    description: str
    recommended_action: str

class TelegramBot:
    """
    Clase para manejar la conexión y envíos de mensajes a Telegram de forma segura.
    Implementa plantillas de mensajes y política de debounce estricta por sensor y regla.
    """
    def __init__(self) -> None:
        """Inicializa el bot leyendo las credenciales y configuración del entorno."""
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = "https://api.telegram.org/bot{}/sendMessage"
        
        # Diccionario para almacenar el registro de cooldowns en memoria: clave (sensor_id, rule_id) -> timestamp
        self._cooldown_registry: Dict[tuple[str, str], float] = {}
        
        try:
            self.cooldown_seconds = int(os.getenv("ALERT_COOLDOWN_SECONDS", 300))
        except ValueError:
            self.cooldown_seconds = 300
            
    def _validate_config(self) -> bool:
        """Valida que las credenciales existan en el entorno."""
        if not self.token or not self.chat_id:
            return False
        return True

    def _get_severity_emoji(self, severity: Severity) -> str:
        """Retorna un emoji visual dependiendo del nivel de severidad."""
        emojis = {
            Severity.INFO: "ℹ️",
            Severity.WARNING: "⚠️",
            Severity.CRITICAL: "🚨"
        }
        return emojis.get(severity, "ℹ️")

    def _get_severity_title(self, severity: Severity) -> str:
        """Retorna un título descriptivo dependiendo del nivel de severidad."""
        titles = {
            Severity.INFO: "ALERTA INFORMATIVA",
            Severity.WARNING: "ALERTA DE ADVERTENCIA",
            Severity.CRITICAL: "ALERTA CRÍTICA"
        }
        return titles.get(severity, "ALERTA")

    def _is_in_cooldown(self, sensor_id: str, rule_id: str) -> bool:
        """
        Verifica si la alerta está en cooldown utilizando (sensor_id, rule_id).
        NO modifica el registro, solo verifica.
        
        Retorna:
            bool: True si la alerta debe ser suprimida, False en caso contrario.
        """
        key = (sensor_id, rule_id)
        current_time = time.time()
        
        if key in self._cooldown_registry:
            last_sent_time = self._cooldown_registry[key]
            if current_time - last_sent_time < self.cooldown_seconds:
                return True
        return False
        
    def _register_cooldown(self, sensor_id: str, rule_id: str) -> None:
        """Registra el tiempo de envío exitoso para un sensor y regla específicos."""
        key = (sensor_id, rule_id)
        self._cooldown_registry[key] = time.time()

    def _build_message_template(self, alert: Alert) -> str:
        """Genera la plantilla HTML estándar para los mensajes de alerta."""
        emoji = self._get_severity_emoji(alert.severity)
        title_severity = self._get_severity_title(alert.severity)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        safe_rule = html.escape(alert.rule_id)
        safe_sensor = html.escape(alert.sensor_id)
        safe_zone = html.escape(alert.zone)
        safe_desc = html.escape(alert.description)
        safe_action = html.escape(alert.recommended_action)

        val_str = f"{alert.value:.2f} L/min" if alert.value is not None else "No disponible"
        thresh_str = f"{alert.threshold:.2f} L/min" if alert.threshold is not None else "No disponible"

        mensaje = (
            f"{emoji} <b>{title_severity} – SmartH2O</b>\n\n"
            f"<b>Regla:</b> {safe_rule}\n"
            f"<b>Sensor:</b> {safe_sensor}\n"
            f"<b>Zona:</b> {safe_zone}\n"
            f"<b>Valor detectado:</b> {val_str}\n"
            f"<b>Umbral:</b> {thresh_str}\n\n"
            f"<b>Descripción:</b>\n{safe_desc}\n\n"
            f"<b>Acción recomendada:</b>\n{safe_action}\n\n"
            f"<b>Fecha:</b> {current_time}"
        )

        return mensaje

    def send_alert(self, alert: Alert) -> SendStatus:
        """
        Envía una alerta estructurada aplicando la política de debounce.
        
        Args:
            alert (Alert): El objeto de alerta inmutable con los datos del evento.
            
        Retorna:
            SendStatus: SENT si se envió, SUPPRESSED si está en cooldown, FAILED si hubo error.
        """
        if not self._validate_config():
            print("❌ Error: TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID no están configurados.")
            return SendStatus.FAILED

        if self._is_in_cooldown(alert.sensor_id, alert.rule_id):
            print(f"⏳ Alerta omitida (cooldown). Sensor: {alert.sensor_id}, Regla: {alert.rule_id}")
            return SendStatus.SUPPRESSED

        mensaje = self._build_message_template(alert)
        success = self._execute_http_post(mensaje)
        
        # Solo se registra en cooldown si el POST a Telegram fue exitoso.
        if success:
            self._register_cooldown(alert.sensor_id, alert.rule_id)
            return SendStatus.SENT
            
        return SendStatus.FAILED

    def _execute_http_post(self, mensaje: str) -> bool:
        """Maneja exclusivamente la petición HTTP hacia la API de Telegram."""
        url = self.base_url.format(self.token)
        payload = {
            "chat_id": self.chat_id,
            "text": mensaje,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get("ok"):
                return True
            else:
                error_desc = data.get('description', 'Desconocido')
                print(f"❌ Error devuelto por Telegram: {error_desc}")
                return False

        except requests.exceptions.Timeout:
            print("❌ Error: Tiempo de espera agotado al conectar con Telegram.")
        except requests.exceptions.ConnectionError:
            print("❌ Error: Fallo de conexión al intentar comunicarse con Telegram.")
        except requests.exceptions.HTTPError as err:
            safe_error = str(err).replace(str(self.token), "***TOKEN_OCULTO***") if self.token else str(err)
            print(f"❌ Error HTTP al enviar el mensaje: {safe_error}")
        except Exception as e:
            safe_error = str(e).replace(str(self.token), "***TOKEN_OCULTO***") if self.token else str(e)
            print(f"❌ Error inesperado: {safe_error}")
        
        return False
