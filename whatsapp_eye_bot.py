# FILE: whatsapp_eye_bot.py
# WhatsApp ile makale tarayıcı - Template + Webhook akışı

import os
import time
import datetime
from dotenv import load_dotenv

# Proje modülleri
from modules.feed_engine.scraper import get_latest_papers
from modules.feed_engine.processor import summarize_paper
from modules.feed_engine.pdf_engine import download_and_extract_text
from modules.feed_engine.vector_engine import search_relevant_users
from database import (
    log_sent_paper, get_all_users, get_user_mendeley_token, 
    get_user_history, add_pending_paper
)
from modules.feed_engine.whatsapp_notifier import send_whatsapp_template
from modules.feed_engine.audio import text_to_speech
from modules.feed_engine.mendeley_engine import add_paper_to_library

load_dotenv()


def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    try:
        with open("whatsapp_bot_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass


def is_paper_sent_to_user(user_id, url):
    """Kullanıcıya daha önce bu makale gönderilmiş mi?"""
    history = get_user_history(user_id)
    for paper in history:
        if paper['url'] == url:
            return True
    return False


def process_for_user(user):
    """
    Bir kullanıcı için makale tarar.
    Bulursa: WhatsApp template gönderir, pending_papers'a kaydeder.
    Webhook gelince app.py tam özeti gönderir.
    """
    # sqlite3.Row'u dict'e çevir
    user = dict(user)
    
    user_id = user['id']
    hoca_adi = user['name']
    whatsapp_phone = user.get('whatsapp_phone')
    kategori_kodlari = user['interests']
    anahtar_kelimeler = user['keywords']
    style = user.get('style', 'samimi')
    detail = user.get('detail_level', 'orta')

    if not whatsapp_phone:
        log_message(f"⚠️ KULLANICI: {hoca_adi} - WhatsApp numarası yok, atlanıyor.")
        return

    log_message(f"🔍 KULLANICI: {hoca_adi} (WhatsApp: {whatsapp_phone}) (Mod: {style}/{detail})")

    try:
        makaleler = get_latest_papers(interests_code=kategori_kodlari, keywords_text=anahtar_kelimeler, limit=50)
    except Exception as e:
        log_message(f"❌ Tarama Hatası: {e}")
        return

    if not makaleler:
        log_message("   ❌ Makale bulunamadı.")
        return

    bulunan_makale = None

    for i, makale in enumerate(makaleler):
        if is_paper_sent_to_user(user_id, makale['url']):
            continue

        try:
            uygun_hocalar = search_relevant_users(makale['abstract'], threshold=1.6)
        except:
            continue

        if user_id in uygun_hocalar:
            log_message(f"   🎯 EŞLEŞME: {makale['title'][:40]}...")
            log_message("   📄 PDF Analiz Ediliyor...")
            tam_metin = download_and_extract_text(makale['url'])
            ozet = summarize_paper(makale, full_text=tam_metin, style=style, detail_level=detail)

            log_message(f"   📲 WhatsApp Template Gönderiliyor...")
            
            # Template parametreleri
            template_params = [
                hoca_adi,                  # {{1}} - İsim
                makale['title'][:100],     # {{2}} - Başlık (kısaltılmış)
                anahtar_kelimeler[:50]     # {{3}} - Anahtar kelimeler
            ]
            
            # Template gönder
            msg_id = send_whatsapp_template(
                phone_number=whatsapp_phone,
                template_name="makale_bildirimi",
                language_code="en",  # Template İngilizce olarak kayıtlı
                parameters=template_params
            )

            if msg_id:
                # Pending papers'a ekle (Webhook gelince tam özet gönderilecek)
                add_pending_paper(
                    user_id=user_id,
                    paper_title=makale['title'],
                    paper_url=makale['url'],
                    paper_summary=ozet,
                    full_text=tam_metin if tam_metin else ozet,
                    paper_keywords=anahtar_kelimeler
                )
                log_message("   ✅ Template gönderildi, pending kayıt yapıldı.")
                log_message("   ⏳ Kullanıcının 'Evet' butonuna basması bekleniyor...")
            
            # Mendeley'e ekle
            token = get_user_mendeley_token(user_id)
            if token:
                log_message("   📚 Mendeley'e ekleniyor...")
                basari = add_paper_to_library(token, makale['title'], makale['url'], makale['abstract'], user_id=user_id)
                if basari:
                    log_message("   ✅ Mendeley tamam.")
                else:
                    log_message("   ❌ Mendeley hatası.")

            bulunan_makale = makale
            break

    if not bulunan_makale:
        log_message(f"   🏁 Uygun makale yok.")


def main():
    """Ana tarama fonksiyonu"""
    log_message("🚀 WHATSAPP MAKALE TARAMASI BAŞLADI (Template + Webhook Akışı)")
    log_message("=" * 50)
    
    users = get_all_users()
    
    if not users:
        log_message("❌ Kullanıcı bulunamadı!")
        return
    
    for user in users:
        process_for_user(user)
        print("-" * 40)
        time.sleep(2)  # Rate limiting
    
    log_message("=" * 50)
    log_message("🏁 Tarama Tamamlandı. Webhook dinleniyor...")
    log_message("ℹ️  Kullanıcılar 'Evet' butonuna bastığında app.py webhook tam özeti gönderecek.\n")


if __name__ == '__main__':
    main()
