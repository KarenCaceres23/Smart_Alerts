import os
import html
import time
from datetime import datetime
import requests
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Diccionario para almacenar el registro de cooldowns en memoria
_cooldown_registry = {}

class TelegramBot:
    """
    Clase para manejar la conexión y envíos de mensajes a Telegram de forma segura.
    Reutilizable para futuros módulos (ej: rules, detector, notifier).
    """
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = "https://api.telegram.org/bot{}/sendMessage"
        
        # Cargar configuración de cooldown (por defecto 60 segundos)
        try:
            self.cooldown_seconds = int(os.getenv("ALERT_COOLDOWN_SECONDS", 60))
        except ValueError:
            self.cooldown_seconds = 60
            
    def validate_config(self):
        """Valida que las credenciales existan en el entorno."""
        if not self.token:
            print("❌ Error: TELEGRAM_BOT_TOKEN no está configurado en el archivo .env.")
            return False
        if not self.chat_id:
            print("❌ Error: TELEGRAM_CHAT_ID no está configurado en el archivo .env.")
            return False
        return True

    def get_severity_emoji(self, severity):
        """Retorna un emoji visual dependiendo del nivel de severidad."""
        emojis = {
            "BAJA": "🟢",
            "MEDIA": "🟡",
            "ALTA": "🟠",
            "CRITICA": "🔴",
            "CRÍTICA": "🔴"
        }
        return emojis.get(severity.upper(), "⚪")

    def _is_in_cooldown(self, title, description, severity):
        """Verifica si la alerta está en cooldown para evitar spam."""
        key = f"{title}_{description}_{severity}"
        current_time = time.time()
        
        if key in _cooldown_registry:
            last_sent_time = _cooldown_registry[key]
            if current_time - last_sent_time < self.cooldown_seconds:
                return True
        
        # Registrar o actualizar el último tiempo de envío
        _cooldown_registry[key] = current_time
        return False

    def send_message(self, title, description, severity="MEDIA"):
        """Envía el mensaje formateado en HTML escapando caracteres peligrosos."""
        if not self.validate_config():
            return False
            
        if not title or not description:
            print("❌ Error: El título y la descripción del mensaje no pueden estar vacíos.")
            return False

        # Protección anti-spam / cooldown
        if self._is_in_cooldown(title, description, severity):
            print(f"Alerta omitida para evitar spam. Intenta nuevamente en {self.cooldown_seconds} segundos.")
            return False

        # Escapar contenido dinámico para evitar inyección o ruptura de etiquetas HTML
        safe_title = html.escape(title)
        safe_description = html.escape(description)
        safe_severity = html.escape(severity.upper())
        emoji = self.get_severity_emoji(severity)
        
        # Obtener hora de envío
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Formatear el mensaje usando HTML para mayor robustez y aspecto profesional
        mensaje = (
            "🚨 <b>Alerta SmartH2O</b>\n\n"
            "<b>Sistema:</b> SmartH2O\n"
            f"<b>Severidad:</b> {emoji} {safe_severity}\n"
            f"<b>Título:</b> {safe_title}\n"
            f"<b>Hora:</b> {current_time}\n"
            f"<b>Descripción:</b> {safe_description}"
        )

        url = self.base_url.format(self.token)
        payload = {
            "chat_id": self.chat_id,
            "text": mensaje,
            "parse_mode": "HTML"
        }

        try:
            # Se utiliza timeout de 10 segundos según buenas prácticas
            response = requests.post(url, json=payload, timeout=10)
            
            # Validar si la respuesta HTTP es exitosa
            response.raise_for_status()
            
            # Validar si Telegram procesó correctamente la solicitud
            data = response.json()
            if data.get("ok"):
                return True
            else:
                # Extraer error sin exponer el token
                error_desc = data.get('description', 'Desconocido')
                print(f"❌ Error devuelto por Telegram: {error_desc}")
                return False

        except requests.exceptions.Timeout:
            print("❌ Error: Tiempo de espera agotado al conectar con Telegram.")
        except requests.exceptions.ConnectionError:
            print("❌ Error: Fallo de conexión al intentar comunicarse con Telegram.")
        except requests.exceptions.HTTPError as err:
            # Ocultar token en caso de venir en la URL de error
            safe_error = str(err).replace(str(self.token), "***TOKEN_OCULTO***") if self.token else str(err)
            print(f"❌ Error HTTP al enviar el mensaje: {safe_error}")
        except Exception as e:
            # Ocultar token en excepciones genéricas
            safe_error = str(e).replace(str(self.token), "***TOKEN_OCULTO***") if self.token else str(e)
            print(f"❌ Error inesperado: {safe_error}")
        
        return False

def send_telegram_alert(title, description, severity="MEDIA"):
    """
    Envía una alerta de SmartH2O a través del bot de Telegram.
    (Mantiene compatibilidad con la versión anterior para no romper el código actual).

    Args:
        title (str): El título de la alerta.
        description (str): La descripción detallada de la alerta.
        severity (str, opcional): La severidad de la alerta (por defecto "MEDIA").
    
    Returns:
        bool: True si el mensaje se envió con éxito, False en error o si fue omitido por cooldown.
    """
    bot = TelegramBot()
    return bot.send_message(title, description, severity)
