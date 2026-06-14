import os
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Obtener solo el token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_chat_id():
    """
    Obtiene los últimos mensajes enviados al bot para extraer el chat_id.
    """
    print("========================================")
    print("🔍 Herramienta para obtener CHAT_ID")
    print("========================================\n")
    
    if not TELEGRAM_BOT_TOKEN:
        print("❌ Error: TELEGRAM_BOT_TOKEN no está configurado.")
        print("💡 Por favor, configura tu archivo .env primero.")
        return

    print("⏳ Obteniendo actualizaciones de Telegram de forma segura...\n")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get("ok"):
            print(f"❌ Error de Telegram: {data.get('description')}")
            return
            
        resultados = data.get("result", [])
        
        if not resultados:
            print("⚠️ No se encontraron mensajes recientes.")
            print("\n💡 INSTRUCCIONES:")
            print("1. Abre Telegram.")
            print("2. Busca tu bot o ve al grupo donde lo agregaste.")
            print("3. Escríbele cualquier mensaje (por ejemplo: 'Hola').")
            print("4. Vuelve aquí y ejecuta este script nuevamente.")
            return
            
        print("✅ ¡Se encontraron mensajes!\n")
        print("--- RESULTADOS ---")
        
        for actualizacion in resultados:
            # Soportar tanto mensajes directos como notificaciones de añadir al grupo
            msg_data = actualizacion.get("message") or actualizacion.get("my_chat_member", {}).get("chat", {})
            
            if not msg_data:
                continue
                
            chat = msg_data if "id" in msg_data else msg_data.get("chat", {})
            
            chat_id = chat.get('id', 'Desconocido')
            tipo_chat = chat.get('type', 'Desconocido')
            titulo = chat.get('title', chat.get('first_name', 'Sin Nombre'))
            
            # Formatear el tipo de chat
            if tipo_chat == "private":
                tipo_str = "👤 Chat Privado"
            elif tipo_chat in ["group", "supergroup"]:
                tipo_str = "👥 Grupo / Supergrupo"
            elif tipo_chat == "channel":
                tipo_str = "📢 Canal"
            else:
                tipo_str = f"Otro ({tipo_chat})"
                
            print(f"Tipo: {tipo_str}")
            print(f"Nombre: {titulo}")
            print(f"👉 TU CHAT_ID ES: {chat_id}")
            
            # Aclaración para IDs de grupos
            if str(chat_id).startswith("-"):
                print("ℹ️ Nota: En grupos es completamente normal que el CHAT_ID empiece con un número negativo (ej. -100...).")
                
            print("-" * 30)
            
        print("\n📋 Copia el CHAT_ID correspondiente y pégalo en tu archivo .env")
        
    except Exception as e:
        # Nunca imprimir el error directo si contiene el token
        safe_error = str(e).replace(TELEGRAM_BOT_TOKEN, "***TOKEN_OCULTO***")
        print(f"❌ Error al conectar con Telegram: {safe_error}")

if __name__ == "__main__":
    get_chat_id()
