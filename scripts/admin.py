
from database import add_user, get_all_users
from modules.feed_engine.vector_engine import add_user_interest_vector
from modules.feed_engine.processor import suggest_arxiv_categories

def main():
    while True:
        print("\n--- 🎓 ACADEMIC EYE - AKILLI YÖNETİM ---")
        print("1. Yeni Hoca Ekle (Otomatik Kategori Tespiti)")
        print("2. Hocaları Listele")
        print("3. Çıkış")

        secim = input("Seçiminiz: ")

        if secim == "1":
            print("\n--- YENİ KAYIT ---")
            ad = input("Ad Soyad: ")
            chat_id = input("Chat ID: ")

            print("💡 İPUCU: Hocanın web sitesindeki 'Research Interests' kısmını yapıştırın.")
            keywords = input("Detaylı İlgi Alanları: ")

            # BURADA SİHİR DEVREYE GİRİYOR ✨
            # Kullanıcıya sormuyoruz, yapay zekaya soruyoruz.
            print("⏳ Uygun ArXiv kategorileri yapay zeka ile tespit ediliyor...")
            otomatik_kategori = suggest_arxiv_categories(keywords)

            # 1. SQLite'a ekle
            user_id = add_user(ad, chat_id, otomatik_kategori, keywords)

            # 2. Vektör DB'ye ekle
            if user_id:
                print("🧠 İlgi alanları vektörel uzaya işleniyor...")
                add_user_interest_vector(user_id, keywords)
                print("✨ İşlem tamam! Hoca eklendi.")

        elif secim == "2":
            print("\n--- KAYITLI HOCALAR ---")
            users = get_all_users()
            if not users:
                print("Listede kimse yok.")
            for u in users:
                print(f"👤 {u['name']}")
                print(f"   └─ 🎯 Tespit Edilen Kategoriler: {u['interests']}")
                print(f"   └─ 🔬 Orijinal İlgi Alanları: {u['keywords']}")
                print("-" * 40)

        elif secim == "3":
            break


if __name__ == "__main__":
    main()