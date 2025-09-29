import os 
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram(msg: str) -> bool:
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print('Telegram no configurado')
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={'chat_id': TELEGRAM_CHAT_ID, 'text': msg})
        return r.ok
    except Exception as e:
        print('Error al enviar mensaje')
        return False
    
def notify(subject: str, msg: str):
    full_msg = f"{subject}\n\n {msg}"
    ok_tg = send_telegram(full_msg)
    return ok_tg