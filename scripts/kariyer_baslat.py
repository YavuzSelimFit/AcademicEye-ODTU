# Bu dosya Career Engine'i manuel tetiklemek içindir.
# Haftada 1 kez çalıştırılması yeterlidir.

from modules.career_engine.career_manager import update_all_career_stats

if __name__ == "__main__":
    try:
        update_all_career_stats()
        input("\nÇıkmak için Enter'a basın...")
    except ImportError as e:
        print("HATA: Import sorunu yaşandı.")
        print("Lütfen bu dosyayı 'modules' klasörünün dışından (ana dizinden) çalıştırdığınızdan emin olun.")
        print(f"Detay: {e}")
        input()