import sys
import os

# Add parent directory to path to import database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import create_admin_user, get_all_admin_users, init_db

def main():
    print("=" * 50)
    print("ADMIN KULLANICI OLUŞTURMA ARACI")
    print("=" * 50)
    
    # Veritabanını başlat (migration için)
    init_db()
    
    # Mevcut adminleri göster
    admins = get_all_admin_users()
    if admins:
        print(f"\n📋 Mevcut Admin Kullanıcılar ({len(admins)}):")
        for admin in admins:
            print(f"   - ID: {admin['id']}, İsim: {admin['name']}, Email: {admin['email']}")
    else:
        print("\n⚠️  Sistemde henüz admin kullanıcı yok.")
    
    print("\n" + "-" * 50)
    print("YENİ ADMIN OLUŞTUR")
    print("-" * 50)
    
    # Kullanıcıdan bilgileri al
    name = input("Admin Adı: ").strip()
    email = input("Admin Email: ").strip()
    password = input("Admin Şifre: ").strip()
    
    if not name or not email or not password:
        print("\n❌ Tüm alanlar doldurulmalıdır!")
        return
    
    # Onay iste
    print(f"\n📝 Özet:")
    print(f"   İsim: {name}")
    print(f"   Email: {email}")
    print(f"   Şifre: {'*' * len(password)}")
    
    confirm = input("\nOluşturmak için 'EVET' yazın: ").strip()
    
    if confirm.upper() == "EVET":
        user_id = create_admin_user(name, email, password)
        if user_id:
            print(f"\n✅ Başarılı! Admin kullanıcı ID: {user_id}")
            print(f"\nGiriş Bilgileri:")
            print(f"   Email: {email}")
            print(f"   Şifre: {password}")
            print(f"\n👉 http://127.0.0.1:5000/login adresinden giriş yapabilirsiniz.")
        else:
            print("\n❌ Admin oluşturulamadı. Lütfen email adresini kontrol edin.")
    else:
        print("\n❌ İşlem iptal edildi.")

if __name__ == "__main__":
    main()
