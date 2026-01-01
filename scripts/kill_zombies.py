import os
import subprocess

def kill_process(name):
    print(f"🔪 {name} süreçleri sonlandırılıyor...")
    try:
        # /F: Force, /IM: Image Name
        result = subprocess.run(['taskkill', '/F', '/IM', name], capture_output=True, text=True)
        if "SUCCESS" in result.stdout:
            print(f"   ✅ {name} temizlendi.")
        elif "not found" in result.stderr:
            print(f"   ℹ️ {name} zaten çalışmıyor.")
        else:
            print(f"   ⚠️ {name} için sonuç: {result.stdout} {result.stderr}")
    except Exception as e:
        print(f"   ❌ Hata: {e}")

if __name__ == "__main__":
    print("🧹 TEMİZLİK BAŞLIYOR...")
    print("--------------------------------")
    
    # 1. Chrome ve Driver'lar (En önemli kısım)
    kill_process("chrome.exe")
    kill_process("chromedriver.exe")
    
    # 2. Python (Dikkat: Bu scripti de öldürebilir ama sona koyarsak sorun olmaz)
    # Kendi kendimizi öldürmemek için PID kontrolü yapabiliriz ama basite kaçalım.
    # Kullanıcıdan App'i kapatmasını isteyeceğiz zaten.
    # kill_process("python.exe") 
    
    print("--------------------------------")
    print("✅ Temizlik tamamlandı. Şimdi 'python app.py' ile tekrar başlatabilirsiniz.")
