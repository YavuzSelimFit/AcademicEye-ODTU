import time
import re
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import subprocess

# Standard webdriver import remains for type hinting or specific exceptions if needed, 
# but we primarily use 'uc' now.

def log_to_file(msg):
    with open("ieee_bot_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")

def get_headless_driver():
    msg = "🔧 Driver (UC) başlatılıyor... (Minimal Stealth)"
    print(msg)
    log_to_file(msg)
    try:
        options = uc.ChromeOptions()
        # options.add_argument("--headless=new") # Test için kapalı
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # UC Minimal Init
        driver = uc.Chrome(options=options, version_main=122, headless=False, use_subprocess=True)
        
        print("   ✅ Driver (UC) BAŞARILI başlatıldı.")
        return driver
    except Exception as e:
        err_msg = f"❌ Driver (UC) Başlatma Hatası: {e}"
        print(err_msg)
        log_to_file(err_msg)
        return None
        print(f"   ❌ Driver Başlatma Hatası: {e}")
        return None

def search_ieee_author(name):
    """
    IEEE Xplore üzerinde yazar arar ve profil ID'sini döner.
    """
    msg = f"📡 IEEE Dedektifi: '{name}' aranıyor..."
    print(msg)
    log_to_file(msg)
    
    driver = get_headless_driver()
    
    # IEEE Yazar Arama URL'si
    # https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText=Cengiz%20Besikci
    # Ancak Yazar sekmesi daha spesifik olabilir. En garantisi genel arama yapıp sol taraftan yazar filtresi veya 
    # doğrudan "Authors" sekmesine gitmek.
    # IEEE Author Search URL: https://ieeexplore.ieee.org/author/search/results?queryText=NAME
    
    # URL Encode (Önemli: Boşluklar %20 olmalı)
    import urllib.parse
    encoded_name = urllib.parse.quote(name)
    
    # Genel Arama URL'si (En güvenilir giriş noktası)
    base_url = f"https://ieeexplore.ieee.org/search/searchresult.jsp?newsearch=true&queryText={encoded_name}"
    
    # Author Facet URL'si (Alternatif: Doğrudan yazarları listelemeye çalışır)
    # Ancak önce genel aramaya gidip oradan "Authors" sekmesini bulmak daha doğal (bot koruması için)
    
    try:
        print(f"   ➡️ Arama Başlatılıyor: {base_url}")
        driver.get(base_url)
        time.sleep(5)
        
        print(f"📄 Sayfa Başlığı: {driver.title}")
        
        if "Page not Found" in driver.title or "404" in driver.title:
            print("❌ Hatalı URL yapısı veya 404.")
            driver.save_screenshot("ieee_404_error.png")
            return None
        
        # Anti-Bot Check: Sadece başlığa güveniyoruz.
        # CAPTCHA scriptleri sayfada her zaman olabilir, bu yüzden kaynak kodunda aramak hatalı.
        
        # Eğer sonuç yoksa da screenshot alalım
        if "no result" in driver.page_source.lower() and "search results" not in driver.title.lower():
             print("❌ Arama sonucu bulunamadı (No Result).")
             driver.save_screenshot("ieee_no_result.png")
             return None

        wait = WebDriverWait(driver, 20)
        
        # 1. Strateji: Sayfanın üst kısmında "Authors" sekmesi/önerisi var mı?
        # IEEE arayüzü bazen yazar araması olduğunu anlayıp en üste "Author Profile" kartı çıkarır.
        
        print("   🔍 'Authors' sekmesi veya Author sonuçları aranıyor...")
        try:
             # "Authors" sekmesine geçiş linkini ara (Sol panel veya üst tab)
             # Genellikle: <a href="..." ...>Authors</a>
             # XPath ile text kontrolü daha güvenli
             authors_tab = driver.find_element(By.XPATH, "//a[contains(text(), 'Authors')]")
             if authors_tab:
                 print("   ➡️ 'Authors' sekmesi bulundu, tıklanıyor...")
                 driver.execute_script("arguments[0].click();", authors_tab)
                 time.sleep(3)
        except:
             print("   ℹ️ 'Authors' sekmesi doğrudan bulunamadı, mevcut sonuçlar taranıyor...")

        
        # 2. Strateji: Sonuçlar içindeki Yazar Linklerini Topla
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Yazar linkleri genellikle: /author/37085387500
        results = soup.find_all('a', href=re.compile(r'/author/\d+'))
        
        candidates = []
        for res in results:
            href = res.get('href')
            text = res.get_text(strip=True)
            if not text: continue
            
            # ID'yi ayıkla
            aid = href.split('/author/')[-1].split('?')[0] # Query param temizliği
            
            if aid not in [c['id'] for c in candidates]:
                candidates.append({'name': text, 'id': aid})

        # print(f"   🔎 Bulunan Adaylar: {len(candidates)}")
        
        target_clean = name.lower().replace(" ", "")

        for cand in candidates:
             cand_clean = cand['name'].lower().replace(" ", "")
             
             # "CengizBesikci" == "cengizbesikci"
             if target_clean in cand_clean or cand_clean in target_clean:
                 success_msg = f"✅ EŞLEŞME: {cand['name']} (ID: {cand['id']})"
                 print(success_msg)
                 log_to_file(success_msg)
                 return cand['id']
        
        fail_msg = "❌ Uygun profil bulunamadı."
        print(fail_msg)
        log_to_file(fail_msg)
        return None
            
    except Exception as e:
        print(f"⚠️ IEEE Arama Hatası: {e}")
        try:
            driver.save_screenshot("ieee_error_search.png")
        except:
            pass
        return None
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def get_ieee_publications(author_id):
    """
    Yazar ID'sine göre yayınları çeker.
    Journals ve Conferences ayrımı yapar.
    """
    print(f"📚 IEEE Yayınları Çekiliyor (ID: {author_id})...")
    driver = get_headless_driver()
    
    # Author Profile URL
    url = f"https://ieeexplore.ieee.org/author/{author_id}"
    
    data = {
        'publications': [], # Tüm yayınlar (Comparison için)
        'journals': [],
        'conferences': [],
        'stats': {'total': 0, 'citation': 0}
    }
    
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 15)
        time.sleep(5)
        
        # Sayfayı aşağı kaydır (Lazy load)
        last_height = driver.execute_script("return document.body.scrollHeight")
        for i in range(5):
             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
             time.sleep(2)
             new_height = driver.execute_script("return document.body.scrollHeight")
             if new_height == last_height: break
             last_height = new_height

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Yayınları Bul
        # Genellikle "result-item-title" class'ı başlığı tutar.
        # "description" altında "Conference Paper" veya "Journal Article" yazar.
        
        # Yapıyı analiz edelim (tahmini, kesin yapı için HTML görmek gerek ama standart IEEE yapısı)
        # Class: list-result-item
        
        items = soup.find_all('div', class_=re.compile(r'result-item')) # Geniş arama
        
        pub_count = 0
        for item in items:
            title_tag = item.find('h3') or item.find('h2') # Bazen h2 bazen h3
            if not title_tag: continue
            
            title = title_tag.get_text(strip=True)
            
            # Yayın Tipi
            # Genellikle title'ın altında veya üstünde metadata vardır.
            full_text = item.get_text(" ", strip=True)
            
            ptype = "Unknown"
            if "Conference" in full_text or "Proceedings" in full_text:
                ptype = "Conference"
            elif "Journal" in full_text or "Transactions" in full_text or "Letters" in full_text:
                ptype = "Journal"
            elif "Early Access" in full_text:
                 ptype = "Early Access"
            
            # Yıl
            year_match = re.search(r'20[0-2][0-9]', full_text)
            year = year_match.group(0) if year_match else "????"
            
            pub_obj = {
                'title': title,
                'year': year,
                'type': ptype,
                'venue': 'IEEE Xplore'
            }
            
            # Listelere Ekle
            data['publications'].append(pub_obj) # Hepsini ekle
            
            if ptype == "Journal":
                data['journals'].append(pub_obj)
            elif ptype == "Conference":
                data['conferences'].append(pub_obj)
                
            pub_count += 1
            
        print(f"📊 Toplam {pub_count} yayın çekildi.")
        print(f"   -> {len(data['journals'])} Makale (Journal)")
        print(f"   -> {len(data['conferences'])} Bildiri (Conference)")

        return data

    except Exception as e:
        print(f"❌ IEEE Yayın Çekme Hatası: {e}")
        return data
    finally:
        driver.quit()

if __name__ == "__main__":
    # Test
    # Cengiz Beşikçi ID'si (Tahmini veya test için aratacağız)
    name = "Cengiz Besikci"
    aid = search_ieee_author(name)
    if aid:
        get_ieee_publications(aid)
