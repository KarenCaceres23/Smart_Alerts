import html
import time
import logging
from typing import Optional

import requests
from requests.exceptions import Timeout, ConnectionError, RequestException

from src.smart_alerts.models import Alert, Severity, SendStatus, AuditState
from src.smart_alerts.config import AppConfig
from src.smart_alerts.cooldown.base import CooldownManager
from src.smart_alerts.audit import AuditLogger
from .base import BaseNotifier, NotifierResult

logger = logging.getLogger(__name__)


class TelegramNotifier(BaseNotifier):
    """
    Notificador de Telegram robusto con manejo de reintentos,
    control de límites (HTTP 429) y cooldown integrado.
    """

    def __init__(
        self,
        config: AppConfig,
        cooldown_manager: CooldownManager,
        audit_logger: Optional[AuditLogger] = None,
    ):
        self.config = config
        self.cooldown_manager = cooldown_manager
        self.audit_logger = audit_logger
        self.base_url = "https://api.telegram.org/bot{}/sendMessage"

    def _get_severity_emoji(self, severity: Severity) -> str:
        emojis = {
            Severity.BAJA: "🟢",
            Severity.MEDIA: "🟡",
            Severity.ALTA: "🟠",
            Severity.CRITICA: "🔴",
        }
        return emojis.get(severity, "ℹ️")

    def _build_message(self, alert: Alert) -> str:
        emoji = self._get_severity_emoji(alert.severity)

        # El timestamp viene con zona horaria en occurred_at, o lo formateamos directamente
        time_str = alert.occurred_at.strftime("%Y-%m-%d %H:%M:%S %Z").strip()

        safe_title = html.escape(alert.title)
        safe_desc = html.escape(alert.description)
        safe_rule = html.escape(alert.rule_id)
        safe_sensor = html.escape(alert.sensor_id)

        mensaje = (
            f"{emoji} <b>{safe_title}</b>\n\n"
            f"<b>Regla:</b> {safe_rule}\n"
            f"<b>Sensor:</b> {safe_sensor}\n\n"
            f"<b>Descripción:</b>\n{safe_desc}\n\n"
            f"<b>Fecha:</b> {time_str}"
        )
        return mensaje

    def send(self, alert: Alert) -> NotifierResult:
        """
        Envía la alerta asegurando primero que no esté en cooldown.
        Maneja reintentos para errores recuperables.
        """
        # Contexto base para todos los logs de esta alerta
        log_context = {
            "alert_id": alert.alert_id,
            "sensor_id": alert.sensor_id,
            "rule_id": alert.rule_id,
            "severity": alert.severity.name,
        }

        # 1. Verificar cooldown
        if self.cooldown_manager.is_in_cooldown(alert.alert_id):
            logger.info(
                f"Alerta suprimida por cooldown",
                extra={**log_context, "motivo": "suprimida por cooldown"},
            )
            if self.audit_logger:
                self.audit_logger.log_event(
                    state=AuditState.SUPPRESSED,
                    alert_id=alert.alert_id,
                    rule_id=alert.rule_id,
                    sensor_id=alert.sensor_id,
                    severity=alert.severity,
                    reason="Cooldown activo",
                )
            return NotifierResult(
                status=SendStatus.SUPPRESSED, attempts=0, skipped_by_cooldown=True
            )

        mensaje = self._build_message(alert)
        url = self.base_url.format(self.config.telegram_bot_token)
        payload = {"chat_id": self.config.telegram_chat_id, "text": mensaje, "parse_mode": "HTML"}

        attempts = 0
        rate_limit_attempts = 0
        MAX_429_RETRIES = 3
        last_error = None
        last_status_code = None

        while attempts < self.config.telegram_max_retries:
            attempts += 1
            try:
                start_time = time.time()
                response = requests.post(
                    url, json=payload, timeout=self.config.telegram_timeout_seconds
                )
                latency = int((time.time() - start_time) * 1000)
                last_status_code = response.status_code

                if response.status_code == 429:
                    attempts -= 1  # No gastar el contador de errores de red
                    rate_limit_attempts += 1
                    if rate_limit_attempts > MAX_429_RETRIES:
                        last_error = "HTTP 429 Rate Limit Exceeded permanently"
                        logger.error(last_error, extra=log_context)
                        break

                    # Too Many Requests - Telegram envía retry_after
                    data = response.json()
                    retry_after = data.get("parameters", {}).get(
                        "retry_after", self.config.telegram_backoff_seconds
                    )
                    logger.warning(
                        f"HTTP 429 Limit reached. Waiting {retry_after}s.",
                        extra={**log_context, "latency_ms": latency, "retry_after": retry_after},
                    )
                    time.sleep(retry_after)
                    continue  # Try again

                response.raise_for_status()
                data = response.json()

                if data.get("ok"):
                    # ÉXITO
                    logger.info(
                        "Alerta enviada con éxito",
                        extra={
                            **log_context,
                            "attempts": attempts,
                            "latency_ms": latency,
                            "resultado": "exito",
                        },
                    )
                    # 2. Registrar cooldown SÓLO en caso de éxito
                    self.cooldown_manager.mark_as_sent(alert.alert_id)
                    if self.audit_logger:
                        self.audit_logger.log_event(
                            state=AuditState.SENT,
                            alert_id=alert.alert_id,
                            rule_id=alert.rule_id,
                            sensor_id=alert.sensor_id,
                            severity=alert.severity,
                            attempts=attempts,
                            latency_ms=latency,
                        )
                    return NotifierResult(
                        status=SendStatus.SENT, attempts=attempts, status_code=last_status_code
                    )
                else:
                    # Telegram devolvió 200 pero ok=False
                    last_error = data.get("description", "Unknown Telegram Error")
                    logger.error(
                        f"Error lógico de Telegram: {last_error}",
                        extra={**log_context, "attempts": attempts},
                    )
                    break  # No es recuperable normalmente

            except Timeout:
                last_error = "Timeout Error"
                logger.warning(
                    f"Timeout al conectar con Telegram (intento {attempts}/{self.config.telegram_max_retries})",
                    extra=log_context,
                )
                if self.audit_logger:
                    self.audit_logger.log_event(
                        state=AuditState.RETRYING,
                        alert_id=alert.alert_id,
                        rule_id=alert.rule_id,
                        sensor_id=alert.sensor_id,
                        severity=alert.severity,
                        reason=last_error,
                        attempts=attempts,
                    )
                time.sleep(self.config.telegram_backoff_seconds)

            except ConnectionError:
                last_error = "Connection Error"
                logger.warning(
                    f"Error de conexión (intento {attempts}/{self.config.telegram_max_retries})",
                    extra=log_context,
                )
                if self.audit_logger:
                    self.audit_logger.log_event(
                        state=AuditState.RETRYING,
                        alert_id=alert.alert_id,
                        rule_id=alert.rule_id,
                        sensor_id=alert.sensor_id,
                        severity=alert.severity,
                        reason=last_error,
                        attempts=attempts,
                    )
                time.sleep(self.config.telegram_backoff_seconds)

            except RequestException as e:
                # HTTP errors
                if hasattr(e, "response") and e.response is not None:
                    last_status_code = e.response.status_code
                    if last_status_code in [400, 401, 403, 404]:
                        # No recuperables
                        last_error = f"HTTP Error {last_status_code}"
                        logger.error(f"Error no recuperable: {last_error}", extra=log_context)
                        break

                last_error = str(e)
                logger.warning(
                    f"Excepción en petición (intento {attempts}): HTTP {last_status_code}",
                    extra=log_context,
                )
                time.sleep(self.config.telegram_backoff_seconds)

            except Exception as e:
                last_error = str(e)
                logger.error(f"Error inesperado al enviar alerta", extra=log_context)
                break

        # Si salió del bucle sin retornar, fracasó
        logger.error(
            "Fallo definitivo al enviar alerta",
            extra={**log_context, "attempts": attempts, "error": last_error, "resultado": "fallo"},
        )
        if self.audit_logger:
            self.audit_logger.log_event(
                state=AuditState.FAILED,
                alert_id=alert.alert_id,
                rule_id=alert.rule_id,
                sensor_id=alert.sensor_id,
                severity=alert.severity,
                error=last_error,
                attempts=attempts,
            )
        return NotifierResult(
            status=SendStatus.FAILED,
            attempts=attempts,
            status_code=last_status_code,
            error=last_error,
        )
