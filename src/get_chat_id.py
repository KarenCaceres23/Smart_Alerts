import os
import sys
import logging
import requests
from dotenv import load_dotenv

# Basic config just for this script
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

def main():
    load_dotenv()
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token or token == "your_telegram_bot_token":
        logger.error("❌ ERROR: TELEGRAM_BOT_TOKEN no configurado en tu archivo .env")
        sys.exit(1)
        
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    
    try:
        logger.info("Conectando con Telegram...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 401:
            logger.error("❌ ERROR 401: Token inválido. Verifica tu .env")
            sys.exit(1)
            
        response.raise_for_status()
        data = response.json()
        
        if not data.get("ok"):
            logger.error(f"❌ Telegram respondió con error: {data.get('description')}")
            sys.exit(1)
            
        results = data.get("result", [])
        if not results:
            logger.info("ℹ️ No hay mensajes nuevos. Por favor, envía un mensaje a tu bot en Telegram y vuelve a correr este script.")
            sys.exit(0)
            
        logger.info("\n--- CHATS DETECTADOS ---")
        logger.info("⚠️ NUNCA compartas capturas de pantalla de estos IDs en público.\n")
        
        # Encontrar el último mensaje de cada chat
        chats = {}
        for update in results:
            message = update.get("message", update.get("my_chat_member", {}))
            chat = message.get("chat")
            if chat:
                chat_id = chat.get("id")
                chat_type = chat.get("type")
                chat_title = chat.get("title", chat.get("username", "Sin nombre"))
                chats[chat_id] = {"title": chat_title, "type": chat_type}
                
        for cid, info in chats.items():
            # Ocultamos parcialmente para evitar filtraciones completas en logs públicos
            str_id = str(cid)
            safe_id = str_id[:3] + "*" * (len(str_id) - 5) + str_id[-2:] if len(str_id) > 5 else str_id
            
            logger.info(f"ID: {cid} (Seguro: {safe_id}) | Tipo: {info['type']} | Nombre/User: {info['title']}")
            
        logger.info("\nPara tu .env, usa el número completo (incluyendo el guion si es grupo).")
        
    except requests.exceptions.Timeout:
        logger.error("❌ ERROR: Tiempo de espera agotado. Revisa tu conexión a internet.")
    except requests.exceptions.ConnectionError:
        logger.error("❌ ERROR: No se pudo conectar a los servidores de Telegram.")
    except Exception as e:
        logger.error(f"❌ ERROR INESPERADO al obtener el chat_id.")

if __name__ == "__main__":
    main()
