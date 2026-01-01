import os
import requests
from dotenv import load_dotenv

load_dotenv()


def send_whatsapp_message(phone_number, message_text):
    """
    Meta Cloud API ile WhatsApp mesajı gönderir.
    
    Args:
        phone_number: Alıcı telefon numarası (örn: 905411378835)
        message_text: Gönderilecek mesaj
        
    Returns:
        Message ID veya None
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not access_token or not phone_number_id:
        print("❌ HATA: WhatsApp API bilgileri eksik (.env kontrol et)")
        return None
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {
            "body": message_text
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id')
            print(f"✅ WhatsApp mesajı gönderildi! ID: {message_id}")
            return message_id
        else:
            print(f"❌ WhatsApp API Hatası: {response.status_code}")
            print(f"Yanıt: {response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
        return None


def send_whatsapp_audio(phone_number, audio_file_path):
    """
    Meta Cloud API ile ses dosyası gönderir.
    
    Args:
        phone_number: Alıcı telefon numarası
        audio_file_path: Ses dosyasının yolu (örn: ozet_sesi.wav)
        
    Returns:
        Message ID veya None
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not access_token or not phone_number_id:
        print("❌ HATA: WhatsApp API bilgileri eksik")
        return None
    
    if not os.path.exists(audio_file_path):
        print(f"❌ Ses dosyası bulunamadı: {audio_file_path}")
        return None
    
    # Adım 1: Medya dosyasını Meta'ya yükle
    upload_url = f"https://graph.facebook.com/v18.0/{phone_number_id}/media"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        # Dosyayı yükle
        # MIME type explicit olarak audio/mpeg verilmeli (MP3 için)
        with open(audio_file_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(audio_file_path), audio_file, 'audio/mpeg'),
                'messaging_product': (None, 'whatsapp'),
                'type': (None, 'audio/mpeg') # Bazen bu da gerekebilir
            }
            
            print(f"📤 Ses dosyası yükleniyor ({os.path.getsize(audio_file_path)} bytes): {audio_file_path}")
            
            # 30 saniye timeout ekle
            upload_response = requests.post(
                upload_url, 
                headers=headers, 
                files=files,
                timeout=30
            )
            
            if upload_response.status_code != 200:
                print(f"❌ Dosya yükleme hatası ({upload_response.status_code}): {upload_response.text}")
                return None
            
            media_id = upload_response.json().get('id')
            print(f"✅ Medya yüklendi! ID: {media_id}")
        
        # Adım 2: Media ID ile mesaj gönder
        message_url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
        
        headers_json = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": phone_number,
            "type": "audio",
            "audio": {
                "id": media_id
            }
        }
        
        send_response = requests.post(message_url, headers=headers_json, json=data)
        
        if send_response.status_code == 200:
            result = send_response.json()
            message_id = result.get('messages', [{}])[0].get('id')
            print(f"✅ WhatsApp ses gönderildi! ID: {message_id}")
            return message_id
        else:
            print(f"❌ Ses gönderme hatası: {send_response.json()}")
            return None
            
    except Exception as e:
        print(f"❌ Ses gönderme hatası: {e}")
        return None


def send_whatsapp_template(phone_number, template_name, language_code="tr", parameters=[]):
    """
    Meta Cloud API ile bir Template mesajı gönderir.
    
    Args:
        phone_number: Alıcı telefon numarası
        template_name: Şablon adı (örn: makale_bildirimi)
        language_code: Dil kodu (tr, en_US)
        parameters: Şablondaki değişkenler listesi [v1, v2, v3]
        
    Returns:
        Message ID veya None
    """
    access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    if not access_token or not phone_number_id:
        print("❌ HATA: WhatsApp API bilgileri eksik (.env kontrol et)")
        return None
    
    url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    # Parametreleri Meta formatına çevir
    components = []
    if parameters:
        body_params = []
        for param in parameters:
            body_params.append({
                "type": "text",
                "text": str(param)
            })
        
        components.append({
            "type": "body",
            "parameters": body_params
        })
    
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
            "components": components
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            message_id = result.get('messages', [{}])[0].get('id')
            print(f"✅ Template gönderildi ({template_name})! ID: {message_id}")
            return message_id
        else:
            print(f"❌ Template API Hatası: {response.status_code}")
            print(f"Yanıt: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
        return None


def send_whatsapp_notification(message, target_phone_number):
    """
    WhatsApp bildirimi gönderir (Telegram notifier ile uyumlu interface)
    
    Args:
        message: Mesaj metni
        target_phone_number: Alıcı telefon numarası
        
    Returns:
        Message ID veya None
    """
    # WhatsApp için 4096 karakter limiti yok ama 65536 karakter limiti var
    # Şimdilik bölmeye gerek yok, direkt gönder
    return send_whatsapp_message(target_phone_number, message)
