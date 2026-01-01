import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from modules.feed_engine.processor import get_model
import paper_cache  # YENİ: RAM tabanlı geçici hafıza

load_dotenv()

# Logger Config
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text
    
    # 1. Cache'den makaleyi çek (30 dakika içindeyse)
    paper_data = paper_cache.get_paper(chat_id)
    
    if not paper_data:
        remaining = paper_cache.get_remaining_time(chat_id)
        if remaining == 0:
            await context.bot.send_message(
                chat_id=chat_id, 
                text="⏰ Şu an aktif bir makale oturumu yok. Yeni bir makale gönderildiğinde 30 dakika içinde sorularınızı yanıtlayabilirim!"
            )
        return
    
    paper_title = paper_data['title']
    content = paper_data['content']
    
    # Bilgi mesajı (kullanıcı beklerken)
    remaining_mins = paper_cache.get_remaining_time(chat_id)
    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"🔍 **{paper_title[:50]}...** hakkında inceliyorum... (⏱ Kalan süre: ~{remaining_mins} dk)", 
        parse_mode='Markdown'
    )
    
    # 2. Gemini'ye Sor
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
        
    # 3. Cevabı Gönder
    # Telegram Markdown hatalarına karşı düz metin fallback
    try:
        await context.bot.send_message(chat_id=chat_id, text=reply_text, parse_mode='Markdown')
    except:
        await context.bot.send_message(chat_id=chat_id, text=reply_text)

def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN bulunamadı!")
        return

    print("🤖 Akademik Asistan (30dk Sohbet Modu) Başlatılıyor...")
    
    application = ApplicationBuilder().token(token).build()
    
    # Sadece metin mesajlarını dinle
    handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    application.add_handler(handler)
    
    print("✅ Bot dinlemeye başladı. Çıkış için CTRL+C")
    application.run_polling()

if __name__ == '__main__':
    main()
