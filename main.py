from modules.feed_engine.scraper import get_latest_papers
from modules.feed_engine.processor import summarize_paper
from modules.feed_engine.pdf_engine import download_and_extract_text
from modules.feed_engine.vector_engine import search_relevant_users
from database import log_sent_paper, get_all_users, get_user_mendeley_token, get_user_history
from modules.feed_engine.notifier import send_notification, send_audio
from modules.feed_engine.audio import text_to_speech
from modules.feed_engine.mendeley_engine import add_paper_to_library
import paper_cache  # YENİ: 30 dakikalık soru penceresi için
import time
import datetime
import os


def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    try:
        with open("bot_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass


def is_paper_sent_to_user(user_id, url):
    history = get_user_history(user_id)
    for paper in history:
        if paper['url'] == url:
            return True
    return False


def process_for_user(user):
    user_id = user['id']
    hoca_adi = user['name']
    chat_id = user['chat_id']

    kategori_kodlari = user['interests']
    anahtar_kelimeler = user['keywords']

    # YENİ: Kullanıcı tercihlerini çek (Eğer yoksa varsayılanları kullan)
    style = user['style'] if 'style' in user.keys() and user['style'] else 'samimi'
    detail = user['detail_level'] if 'detail_level' in user.keys() and user['detail_level'] else 'orta'

    log_message(f"🔍 KULLANICI: {hoca_adi} (Mod: {style}/{detail})")

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

            # YENİ: Tercihleri gönderiyoruz 👇
            ozet = summarize_paper(makale, full_text=tam_metin, style=style, detail_level=detail)

            log_message(f"   📲 Gönderiliyor...")
            mesaj = f"👋 Sayın {hoca_adi},\n\n🚨 **Özel Seçki**\n\n{ozet}\n\n🔗 [Link]({makale['url']})"

            msg_id = None
            if chat_id:
                msg_id = send_notification(mesaj, target_chat_id=chat_id)
                ses = text_to_speech(ozet, style=style)
                if ses: send_audio(ses, target_chat_id=chat_id)
                
                # YENİ: 30 dakikalık soru penceresi için cache'e ekle ve bilgilendir
                paper_cache.add_paper(chat_id, makale['title'], tam_metin if tam_metin else ozet)
                bilgi_mesaji = "📣 **30 dakika içinde** bu makaleyle ilgili sorularınızı yanıtlayabilirim! Sadece bu mesaja **Yanıtla** diyerek sorunuzu yazın."
                send_notification(bilgi_mesaji, target_chat_id=chat_id)

            token = get_user_mendeley_token(user_id)
            if token:
                log_message("   📚 Mendeley'e ekleniyor...")
                basari = add_paper_to_library(token, makale['title'], makale['url'], makale['abstract'],
                                              user_id=user_id)
                if basari:
                    log_message("   ✅ Mendeley tamam.")
                else:
                    log_message("   ❌ Mendeley hatası.")

            # YENİ: full_text ve msg_id kaydediliyor
            log_sent_paper(user_id, makale['title'], makale['url'], ozet, full_text=tam_metin, telegram_message_id=msg_id)
            log_message("   ✅ Web paneline arşivlendi.")

            bulunan_makale = makale
            break

    if not bulunan_makale:
        log_message(f"   🏁 Uygun makale yok.")


def main():
    log_message("🚀 GÜNLÜK GÖREV BAŞLADI")
    users = get_all_users()
    if users:
        for user in users:
            process_for_user(user)
            print("-" * 40)
            time.sleep(2)
    log_message("🏁 Görev Tamamlandı.\n")


if __name__ == "__main__":
    main()