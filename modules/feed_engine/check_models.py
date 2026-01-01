import google.generativeai as genai
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
# If environment variable not found, the code will fail safely below

if not api_key:
    print("HATA: API Key bulunamadı.")
else:
    try:
        genai.configure(api_key=api_key)
        print(f"✅ API Key formatı doğru. Bağlantı deneniyor...\n")

        print("📋 ERİŞİLEBİLİR MODELLER LİSTESİ:")
        print("-" * 40)

        available_models = []
        for m in genai.list_models():
            # Sadece metin üretme yeteneği olanları filtrele
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model Adı: {m.name}")
                available_models.append(m.name)

        print("-" * 40)
        if not available_models:
            print("❌ Hiçbir model bulunamadı. API Anahtarı yetkilerini kontrol et.")
        else:
            print(
                "İpucu: processor.py dosyasındaki 'model=' kısmına yukarıdaki isimlerden birini (başındaki 'models/' kısmını atarak) yazmalısın.")

    except Exception as e:
        print(f"❌ BAĞLANTI HATASI: {e}")