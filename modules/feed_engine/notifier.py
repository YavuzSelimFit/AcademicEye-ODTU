import os
import requests
from dotenv import load_dotenv

load_dotenv()


def clean_markdown(text):
    """
    Telegram'ın sevmediği Markdown karakterlerini temizler.
    """
    chars = ['*', '_', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for c in chars:
        text = text.replace(c, '')
    return text


def send_chunk(chat_id, text, token):
    """Tek bir parça mesajı göndermeyi dener."""
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    # 1. Önce Markdown ile dene (Güzel görünsün diye)
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }

    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print(f"✅ Mesaj parça olarak iletildi.")
            return response.json().get('result', {}).get('message_id')
        else:
            # Hata verdiyse (muhtemelen Markdown hatası)
            print(f"⚠️ Format hatası, düz metin deneniyor...")

            # Parse mode'u tamamen kaldır ve metni temizle
            del payload["parse_mode"]
            # Basit temizlik yapıp gönder
            payload["text"] = text  # Veya clean_markdown(text)

            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print("✅ Düz metin olarak kurtarıldı ve iletildi.")
                return response.json().get('result', {}).get('message_id')
            else:
                print(f"❌ Telegram Hatası: {response.text}")
                return None

    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
        return None


def send_notification(message, target_chat_id=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = target_chat_id if target_chat_id else os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("❌ HATA: Token veya Chat ID eksik.")
        return None

    # TELEGRAM LİMİTİ: 4096 Karakter.
    # Güvenlik payı ile 4000 karakterde bir bölelim.
    limit = 4000
    sent_ids = []

    if len(message) <= limit:
        msg_id = send_chunk(chat_id, message, token)
        if msg_id: sent_ids.append(msg_id)
    else:
        print(f"📦 Mesaj çok uzun ({len(message)} karakter), bölünüyor...")
        parts = [message[i:i + limit] for i in range(0, len(message), limit)]

        for i, part in enumerate(parts):
            print(f"   📤 Parça {i + 1}/{len(parts)} gönderiliyor...")
            msg_id = send_chunk(chat_id, part, token)
            if msg_id: sent_ids.append(msg_id)
            
    # İlk mesajın ID'sini döndür (Reply takibi için genellikle başlık kısmı önemlidir)
    return sent_ids[0] if sent_ids else None


def send_audio(filename, target_chat_id=None):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = target_chat_id if target_chat_id else os.getenv("TELEGRAM_CHAT_ID")
    url = f"https://api.telegram.org/bot{token}/sendAudio"

    try:
        with open(filename, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'chat_id': chat_id, 'title': 'Makale Özeti (Yapay Zeka)'}
            requests.post(url, data=data, files=files)
            print("✅ Ses dosyası gönderildi! 🎧")
    except Exception as e:
        print(f"❌ Ses hatası: {e}")