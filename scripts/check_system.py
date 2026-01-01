import sqlite3
import os

DB_NAME = "academic_memory.db"

def check_system():
    print("🩺 SİSTEM SAĞLIK KONTROLÜ")
    print("-------------------------")
    
    # 1. Veritabanı Dosyası
    if not os.path.exists(DB_NAME):
        print(f"❌ Veritabanı dosyası yok: {DB_NAME}")
        return
    else:
        print(f"✅ Veritabanı dosyası mevcut ({os.path.getsize(DB_NAME)} bytes)")

    # 2. Bağlantı Testi
    try:
        conn = sqlite3.connect(DB_NAME, timeout=5) # 5 saniye bekle
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM user_profiles")
        count = cursor.fetchone()[0]
        print(f"✅ Veritabanı bağlantısı BAŞARILI. (Profil Sayısı: {count})")
        conn.close()
    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            print("❌ KRİTİK HATA: Veritabanı KİLİTLİ (Locked)!")
            print("   -> Lütfen 'kill_zombies.py' scriptini çalıştırın.")
        else:
            print(f"❌ Veritabanı hatası: {e}")
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")

if __name__ == "__main__":
    check_system()
