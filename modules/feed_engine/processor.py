import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
MODEL_NAME = 'gemini-2.5-flash'


def get_model():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(MODEL_NAME)


def summarize_paper(paper_data, full_text=None, style="samimi", detail_level="orta"):
    model = get_model()
    if not model: return "Hata: Model yüklenemedi."

    content = full_text if full_text else paper_data['abstract']

    # --- 1. STİL AYARI (TONLAMA) ---
    # --- 1. STİL AYARI (TONLAMA) ---
    if style == "resmi":
        tone_desc = "TON: Bir Fakülte Toplantısında sunum yapan akademisyen gibi. Ciddi, saygılı, kurumsal. 'Hocam' hitabı resmiyet içermeli. Şaka veya laubali ifadeler yasak."
    elif style == "orta":
        # YENİ SEÇENEK: NORMAL HAYAT
        tone_desc = "TON: İdeal bir ofis sohbeti. Ne çok kasıntı ne de çok gevşek. Saygılı ama samimi bir asistan gibi. Akıcı, anlaşılır, net bir İstanbul Türkçesi."
    elif style == "dogal":
         tone_desc = "TON: Arkadaşça bir sohbet. Bir kafede kahve içerken anlatır gibi. 'Bak hocam şöyle bir şey çıkmış' dermişçesine doğal, duraksamalı, düşünme sesleri (hmm, yani vb.) içerebilen ultra-doğal yapı."
    else:  # samimi (varsayılan)
        tone_desc = "TON: Heyecanlı bir Teknoloji YouTuber'ı veya Podcast sunucusu gibi. Enerjik, vurgulu, dinleyeni uyandıran, ilham verici bir üslup."

    # --- 2. DETAY AYARI (İÇERİK) ---
    # --- 2. DETAY AYARI (İÇERİK) ---
    if detail_level == "detayli":
        content_desc = "İÇERİK: BU BİR DERİNLEMESİNE TEKNİK ANALİZDİR. Makalenin sadece ne yaptığını değil, NASIL yaptığını anlat. Metodolojiyi, kullanılan algoritmaları, veri setlerini ve özellikle SAYISAL SONUÇLARI (Accuracy, F1 Score, vb.) madde madde konuşma diline yedirerek ver. Hocanın 'Bu makale teknik olarak ne katıyor?' sorusuna eksiksiz cevap ver."
    elif detail_level == "kisa":
        content_desc = "İÇERİK: ASANSÖR KONUŞMASI (ELEVATOR PITCH). Vaktimiz yok. Sadece en çarpıcı 'Yenilik Nedir?' ve 'Sonuç Nedir?' bilgisini ver. Gereksiz giriş-gelişme yapma. 30-45 saniyede bitecek şekilde nokta atışı yap."
    else:  # orta / ana_mantik
        content_desc = "İÇERİK: DENGELİ ÖZET. Problemi tanımla, önerilen çözümün ana fikrini (core idea) anlat ve en önemli 1-2 bulguyu paylaş. Teknik terimleri kullanmaktan çekinme ama boğucu olma. Ortalama 2-3 dakikalık bir radyo haberi kıvamında olsun."

    # --- ANA PROMPT ---
    prompt = f"""
    GÖREV: Sen ODTÜ'lü bir profesörün akıllı asistanısın. Hocana yeni bir makalenin sözlü sunumunu yapıyorsun.

    HEDEF: Metin sesli okunacak (TTS). {tone_desc}

    TALİMAT: {content_desc}

    KURALLAR:
    1. GİRİŞ: Sadece selam ver ve konuya gir. (Örn: "Hocam merhaba, yeni bir çalışma var...")
    2. OKUNABİLİRLİK: Formül, denklem veya parantez içi atıf (Author, 2023) ASLA okuma. Bunlar sesli anlaşılmaz.
    3. AKICILIK: Metni tamamen konuşma diline dök.

    MAKALE BİLGİSİ:
    Başlık: {paper_data['title']}
    İçerik: {content[:60000]} 

    ÇIKTI:
    (Sadece konuşma metnini yaz. Başlık veya madde işareti koyma.)
    """

    # --- MODEL DENEME ZİNCİRİ (FALLBACK MECHANISM) ---
    # Screenshot analizine göre 2.5 Pro yok, 2.5 Flash var (Limit: 5 RPM)
    # 3.0 Flash da listede var, onu da deneyebiliriz.
    models_to_try = [
        'gemini-3-flash',         # Kullanıcının tercihi (RPM 5)
        'gemini-2.5-flash',       # Güvenli Liman (RPM 5)
        'gemini-1.5-flash'        # Son Çare
    ]
    
    for current_model_name in models_to_try:
        try:
            # print(f"🧠 Model deneniyor: {current_model_name}") 
            active_model = genai.GenerativeModel(current_model_name)
            response = active_model.generate_content(prompt)
            return response.text
        except Exception as e:
            # print(f"⚠️ {current_model_name} hata verdi: {e}")
            continue # Bir sonraki modele geç
    
    # Hiçbiri çalışmazsa
    # print("❌ Tüm modeller başarısız oldu.")
    return "Hocam, makale analizinde teknik bir sorun oluştu ancak başlık ilginizi çekebilir."


def suggest_arxiv_categories(keywords):
    model = get_model()
    if not model: return "eess.SP"
    prompt = f"Bu konular için en uygun ArXiv kategorileri nelerdir? Sadece kodları virgülle ayır: {keywords}"
    try:
        return model.generate_content(prompt).text.strip()
    except:
        return "eess.SP"