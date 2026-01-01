from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import re
import subprocess
import time
import subprocess

def verify_with_google(item_title, author_name):
    """
    Verilen başlık ve yazar ismini Google'da aratır.
    Eğer anlamlı bir sonuç varsa True döner.
    """
    query = f'"{item_title}" "{author_name}"'
    print(f"   🌐 Google'da Doğrulanıyor: {query[:50]}...")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        service = Service()
        service.creation_flags = subprocess.CREATE_NO_WINDOW
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        
        # Arama kutusunu bul
        search_box = driver.find_element(By.NAME, "q")
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        
        time.sleep(3)
        
        # Sonuçları kontrol et
        # id="search" genellikle sonuçların olduğu div
        results = driver.find_elements(By.XPATH, "//div[@id='search']//a")
        
        valid_hits = 0
        for res in results:
            href = res.get_attribute("href")
            text = res.text
            
            if not href: continue
            
            # Kendi sitemizi (YÖK) veya Google linklerini sayma
            if "google.com" in href or "akademik.yok.gov.tr" in href:
                continue
                
            # LinkedIn, ResearchGate, Üniversite siteleri, TR Dizin vb. geçerli sayılır.
            valid_hits += 1
            if valid_hits >= 1:
                print(f"      ✅ Bulundu: {href[:60]}...")
                return True

        print("      ⚠️ İnternette izine rastlanmadı.")
        return False

    except Exception as e:
        print(f"      ❌ Google Doğrulama Hatası: {e}")
        return False # Hata durumunda bulamadık varsayalım
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    verify_with_google("Investigation of...", "Cengiz Beşikçi")
