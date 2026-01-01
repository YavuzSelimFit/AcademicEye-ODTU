# FILE: academic_eye_bot.py
# Ana makale tarayıcı + Soru-Cevap botu tek script'te birleştirilmiş hali.
# Batch Modu (Concurrent): Bot hemen dinlemeye başlar, tarama arka planda sürer.

import os
import time
import datetime
import asyncio
import threading
import logging
import signal
from dotenv import load_dotenv

# Telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Proje modülleri
from modules.feed_engine.scraper import get_latest_papers
from modules.feed_engine.processor import summarize_paper, get_model
from modules.feed_engine.pdf_engine import download_and_extract_text
from modules.feed_engine.vector_engine import search_relevant_users
from database import log_sent_paper, get_all_users, get_user_mendeley_token, get_user_history
from modules.feed_engine.notifier import send_notification, send_audio
from modules.feed_engine.audio import text_to_speech
from modules.feed_engine.mendeley_engine import add_paper_to_library
import paper_cache

load_dotenv()

# ===================== LOGGING =====================
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Global flag: Yeni makale gönderildi mi?
PAPER_SENT_FLAG = False


def log_message(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    try:
        with open("bot_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
    except:
        pass


# ===================== MAKALE TARAYICI =====================
def is_paper_sent_to_user(user_id, url):
    history = get_user_history(user_id)
    for paper in history:
        if paper['url'] == url:
            return True
    return False


def process_for_user(user):
    global PAPER_SENT_FLAG
    user_id = user['id']
    hoca_adi = user['name']
    chat_id = user['chat_id']
    kategori_kodlari = user['interests']
    anahtar_kelimeler = user['keywords']
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
            ozet = summarize_paper(makale, full_text=tam_metin, style=style, detail_level=detail)

            log_message(f"   📲 Gönderiliyor...")
            mesaj = f"👋 Sayın {hoca_adi},\n\n🚨 **Özel Seçki**\n\n{ozet}\n\n🔗 [Link]({makale['url']})"

            msg_id = None
            if chat_id:
                # Önce sesi oluştur (böylece mesajla aynı anda gider)
                ses = text_to_speech(ozet, style=style)
                
                # Sesi oluşturduktan sonra mesajı at
                msg_id = send_notification(mesaj, target_chat_id=chat_id)
                
                if ses:
                    send_audio(ses, target_chat_id=chat_id)

                # 30 dakikalık soru penceresi
                paper_cache.add_paper(chat_id, makale['title'], tam_metin if tam_metin else ozet)
                bilgi_mesaji = "📣 **30 dakika içinde** bu makaleyle ilgili sorularınızı yanıtlayabilirim! Sadece bu mesaja **Yanıtla** diyerek sorunuzu yazın."
                send_notification(bilgi_mesaji, target_chat_id=chat_id)
                
                # FLAG'i True yap (En az 1 makale gönderildi)
                PAPER_SENT_FLAG = True

            token = get_user_mendeley_token(user_id)
            if token:
                log_message("   📚 Mendeley'e ekleniyor...")
                basari = add_paper_to_library(token, makale['title'], makale['url'], makale['abstract'], user_id=user_id)
                if basari:
                    log_message("   ✅ Mendeley tamam.")
                else:
                    log_message("   ❌ Mendeley hatası.")

            log_sent_paper(user_id, makale['title'], makale['url'], ozet, full_text=tam_metin, telegram_message_id=msg_id)
            log_message("   ✅ Web paneline arşivlendi.")
            bulunan_makale = makale
            break

    if not bulunan_makale:
        log_message(f"   🏁 Uygun makale yok.")


def run_paper_scan():
    """Makale taramasını bir kez çalıştırır."""
    log_message("🚀 MAKALE TARAMASI BAŞLADI")
    users = get_all_users()
    if users:
        for user in users:
            process_for_user(user)
            print("-" * 40)
            time.sleep(2)
    log_message("🏁 Tarama Tamamlandı.\n")


# ===================== SORU-CEVAP BOTU =====================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # Log the incoming message (optional debugging)
    log_message(f"📩 Mesaj Alındı (Chat ID: {chat_id}): {text[:20]}...")

    # Cache'den makaleyi çek
    paper_data = paper_cache.get_paper(chat_id)

    if not paper_data:
        # Cache'de yoksa cevap dönme veya sessiz kal
        # Kullanıcı kafa karışıklığı yaşamaması için sessiz kalmak bazen iyidir ama
        # eğer süre dolduysa ve bot hala açıksa uyarmak mantıklı.
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏰ Şu an aktif bir makale oturumu yok veya süresi doldu."
        )
        return

    paper_title = paper_data['title']
    content = paper_data['content']

    # remaining_mins = paper_cache.get_remaining_time(chat_id)
    # await context.bot.send_message(
    #     chat_id=chat_id,
    #     text=f"🔍 **{paper_title[:50]}...** hakkında inceliyorum... (⏱ Kalan süre: ~{remaining_mins} dk)",
    #     parse_mode='Markdown'
    # )

    model = get_model()
    if not model:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Yapay zeka motoruna bağlanılamadı.")
        return

    prompt = f"""
    GÖREV: Sen bir akademik asistansın. Aşağıdaki makale hakkında kullanıcının sorusunu cevapla.
    
    MAKALE: {paper_title}
    İÇERİK: {content[:50000]}
    
    KULLANICI SORUSU: {text}
    
    KURALLAR:
    1. Sadece makale içeriğine dayanarak cevap ver.
    2. Türkçe ve samimi bir dille açıkla.
    3. Eğer makalede bilgi yoksa "Makalede bu bilgiye rastlayamadım" de.
    4. Cevap kısa ve öz olsun (maksimum 4000 karakter).
    """

    try:
        response = model.generate_content(prompt)
        reply_text = response.text
    except Exception as e:
        reply_text = f"⚠️ Bir hata oluştu: {str(e)}"

    try:
        await context.bot.send_message(chat_id=chat_id, text=reply_text, parse_mode='Markdown')
    except:
        await context.bot.send_message(chat_id=chat_id, text=reply_text)


# ===================== BACKGROUND YÖNETİCİSİ =====================
def background_scanner_loop():
    """Arka planda çalışacak tarama ve lifecycle mantığı"""
    # 1. Taramayı Başlat
    try:
        run_paper_scan()
    except Exception as e:
        log_message(f"❌ Tarama sırasında kritik hata: {e}")
    
    # 2. Tarama bitti, durumu kontrol et
    if PAPER_SENT_FLAG:
        print("\n✅ Makale gönderildi. 30 dakika boyunca bot açık kalacak...")
        time.sleep(30 * 60) # 30 Dakika bekle
        print("\n⏰ 30 Dakika doldu. Bot kapatılıyor.")
    else:
        print("\n🏁 Makale gönderilmedi. Bot kapatılıyor.")

    # 3. Kapatma Sinyali Gönder (Main Thread'i durdurur)
    os.kill(os.getpid(), signal.SIGINT)


# ===================== ANA BAŞLATICI =====================
def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
        return

    print("=" * 50)
    print("🎓 ACADEMIC EYE - Batch (Concurrent) Modu...")
    print("=" * 50)

    # 1. Bot Uygulamasını Hazırla
    async def post_init(application):
        # Bot hazır olduğunda tarama thread'ini başlat
        # Daemon=True: Ana process kapanınca bu da ölür
        threading.Thread(target=background_scanner_loop, daemon=True).start()

    application = ApplicationBuilder().token(token).post_init(post_init).build()
    handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(handler)

    print("🤖 Bot başlatılıyor (CTRL+C ile durdurulabilir)...")
    
    # 2. Botu ve Polling'i Başlat (Blocking)
    # scanner thread'i post_init içinde başlayacak
    application.run_polling()

if __name__ == '__main__':
    main()
