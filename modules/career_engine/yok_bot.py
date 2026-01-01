# FILE: modules/career_engine/yok_bot.py (TAM HALİ)
import requests
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re

try:
    from googlesearch import search
except ImportError:
    search = None

def find_yok_id_by_name(name):
    print(f"🕵️‍♂️ YÖK Dedektifi İş Başında: '{name}' aranıyor...")
    query = f'site:akademik.yok.gov.tr "{name}"'
    
    # 1. Yöntem: googlesearch kütüphanesi
    try:
        if search:
            results = search(query, num_results=3, advanced=True)
        else:
            raise ImportError("googlesearch module not found")
        for result in results:
            match = re.search(r'Detay/(\d+)', result.url)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"⚠️ Google API Hatası: {e}")

    # 2. Yöntem: Selenium ile Google Arama (Fallback)
    print("   🌐 Google Araması (Selenium) deneniyor...")
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    
    # Pencere flash'ını engelle
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    driver = None
    try:
        service = Service()
        service.creation_flags = subprocess.CREATE_NO_WINDOW
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(f"https://www.google.com/search?q={query}")
        time.sleep(3)
        
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and "akademik.yok.gov.tr/AkademikArama/Akademisyen/Detay/" in href:
                match = re.search(r'Detay/(\d+)', href)
                if match:
                    return match.group(1)
    except Exception as e:
        print(f"❌ Selenium Arama Hatası: {e}")
    finally:
        if driver:
            driver.quit()
            
    return None
def scrape_yok_profile(yok_profile_id, name=None):
    """
    YÖK profilinden Yayınlar, Projeler, Ödüller ve Tezleri tek seferde çeker.
    Eğer ID hatalıysa ve 'name' verilmişse, isme göre arayıp doğru profili bulmaya çalışır.
    """
    base_url = "https://akademik.yok.gov.tr/AkademikArama/Akademisyen/Detay/"
    url = f"{base_url}{yok_profile_id}"
    
    # ID uzunsa ve yeni format ise direk URL bu olmayabilir ama deneyelim.
    # Eğer ID "12364" gibi kısaysa, muhtemelen hatalıdır ve isme göre arama gerekecektir.
    
    print(f"🌍 YÖK Profili Taranıyor (Tüm Veriler): {yok_profile_id}...")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")  # GPU rendering'i kapat (headless için önemli)
    options.add_argument("--disable-extensions")  # Extension'ları devre dışı bırak
    options.add_argument("--disable-logging")  # Console log'ları kapat
    options.add_argument("--log-level=3")  # Sadece fatal hataları göster
    options.add_argument("--silent")  # Sessiz mod
    
    # EKSTRA: Pencere flash'ını tamamen engelle
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    
    # SSL/Gizlilik Hatalarını Yoksay
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('--allow-insecure-localhost')
    options.add_argument('--allow-running-insecure-content')
    
    driver = None
    data = {
        'publications': [],
        'conference_papers': [],  # Separate list for conference papers
        'projects': [],
        'awards': [],
        'theses': [],
        'resolved_id': None # Eğer ID değişirse buraya yazacağız
    }

    try:
        service = Service()
        service.creation_flags = subprocess.CREATE_NO_WINDOW
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        time.sleep(3) 

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        page_text = soup.get_text()
        print(f"📄 Sayfa Başlığı/Metni (İlk 100): {page_text[:100].strip()}")
        
        # --- HATA KONTROLÜ VE AKILLI DÜZELTME ---
        if "İstediğiniz işleme cevap veremiyoruz" in page_text or "Records not found" in page_text:
            print("❌ ID ile direkt erişim başarısız.")
            
            if name:
                # İsmi temizle (Unvanlardan arındır)
                raw_name = name
                titles = [r'Prof\.?', r'Dr\.?', r'Doc\.?', r'Doç\.?', r'Arş\.?', r'Gör\.?', r'Öğr\.?', r'Üyesi\.?', r'Yrd\.?']
                for t in titles:
                    name = re.sub(t, '', name, flags=re.IGNORECASE).strip()
                
                print(f"🔄 Akıllı Mod: '{raw_name}' (Aranan: '{name}') ismiyle YÖK içinde aranıyor...")
                try:
                    driver.get("https://akademik.yok.gov.tr/AkademikArama/")
                    time.sleep(2)
                    
                    # Arama Kutusunu Bul
                    search_box = driver.find_element(By.ID, "aramaTerim")
                    search_box.clear()
                    search_box.send_keys(name)
                    
                    # Ara Butonu
                    search_btn = driver.find_element(By.ID, "searchButton")
                    search_btn.click()
                    print("➡️ Arama butonu tıklandı. 3 saniye bekleniyor...")
                    time.sleep(3)
                    
                    # "Akademisyenler" sekmesine geç (Garanti olsun)
                    try:
                        print("👀 'Akademisyenler' sekmesi aranıyor...")
                        akademisyen_tab = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Akademisyenler')]"))
                        )
                        akademisyen_tab.click()
                        print("➡️ 'Akademisyenler' sekmesi tıklandı. 2 saniye bekleniyor...")
                        time.sleep(2)
                    except Exception as tab_e:
                        print(f"⚠️ 'Akademisyenler' sekmesi bulunamadı veya tıklanamadı: {tab_e}")
                        # Devam et, belki varsayılan sekmedir.
                        
                    start_time = time.time()
                    found_profile = False
                    
                    while time.time() - start_time < 10: # 10 saniye bekle
                        all_links = driver.find_elements(By.TAG_NAME, "a")
                        for link in all_links:
                             try:
                                 href = link.get_attribute("href")
                                 text = link.text
                                 
                                 if href and ("viewAuthor.jsp" in href or "AkademisyenGorevOgrenimBilgileri" in href):
                                     print(f"   🔎 ADAY BULUNDU: '{text}' (Aranan: '{name}') URL: {href}")
                                     
                                     # İsim kontrolü
                                     search_term = name.split()[0].lower()
                                     link_text_lower = text.lower()
                                     
                                     mapping = {'İ': 'i', 'I': 'ı', 'Ş': 's', 'Ğ': 'g', 'Ü': 'u', 'Ö': 'o', 'Ç': 'c'}
                                     for k, v in mapping.items():
                                         link_text_lower = link_text_lower.replace(k.lower(), v)
                                         search_term = search_term.replace(k.lower(), v)

                                     if search_term in link_text_lower: 
                                         print(f"✅ EŞLEŞTİ: {text} - URL: {href}")
                                         
                                         # ID Çözümleme
                                         match_id = re.search(r'authorId=([a-zA-Z0-9]+)', href)
                                         if match_id:
                                             data['resolved_id'] = match_id.group(1)
                                             print(f"🆔 Linkten ID Çözüldü: {data['resolved_id']}")

                                         # YÖK Session Hatası almamak için DOĞRUDAN LİNKE TIKLA
                                         # driver.get() yeni istek yaptığı için session kopabiliyor.
                                         
                                         print(f"🔗 Sonuç linkine tıklanıyor: {href}")
                                         
                                         # Target blank kaldır
                                         driver.execute_script("arguments[0].removeAttribute('target')", link)
                                         time.sleep(0.5)
                                         
                                         # Tıkla
                                         driver.execute_script("arguments[0].click();", link)
                                         
                                         found_profile = True
                                         
                                         # Yeni sayfanın yüklenmesini bekle
                                         time.sleep(5) 
                                         break
                                     else:
                                         print(f"❌ EŞLEŞMEDİ: '{search_term}' vs '{link_text_lower}'")

                             except:
                                 continue
                        if found_profile: break
                        time.sleep(1)

                    if found_profile:
                        # Sayfanın yüklenmesini bekle
                        time.sleep(3)
                        print("✅ Profil sayfası yüklendi, HTML analizi başlıyor...")
                        
                        soup = BeautifulSoup(driver.page_source, 'html.parser')
                        
                        # --- YENİ SİSTEM SCRAPING (viewAuthorArticle.jsp) ---
                        # Bu sayfada makaleler genellikle bir liste veya tablo içindedir.
                        # Kullanıcı screenshot'ına göre: <span>Diffraction...</span> gibi.
                        
                        # Tüm metni alıp satır satır analiz edelim, daha güvenli.
                        # Veya belirli class'ları arayalım. Genellikle 'list-group-item' veya benzeri.
                        
                        # Önce basitçe tüm satırları (tr) ve divleri tarayalım.
                        # Başlıkları yakalamak için en garantisi: Yıl içeren satırları bulmak.
                        
                        rows = soup.find_all(['tr', 'div', 'p', 'span'])
                        pubs = []
                        for row in rows:
                            text = row.get_text().strip()
                            if len(text) > 20 and re.search(r'20[0-2][0-9]', text):
                                # Gereksizleri ele
                                if "Telif" in text or "Listele" in text or "Sonuçlar" in text: continue
                                # Temizle (Bazen sıra no başta olur "1. Title")
                                clean = re.sub(r'^\d+\.?\s*', '', text)
                                pubs.append(clean)
                        
                        # Duplicate temizle ve kaydet
                        data['publications'] = list(set(pubs))
                        print(f"   -> Makale (Tahmini): {len(data['publications'])} öge")

                        # Diğer sekmeler (Proje, Ödül) için URL değişimi gerekebilir
                        # Şimdilik ana hedef Makaleler (Publications). 
                        # Eğer proje istenirse: viewAuthorProject.jsp vb. tahmin edilebilir ama şimdilik ID çözüldüğü için yeterli.
                        
                    else:
                        print("❌ İsimle arama sonucunda kayıt bulunamadı.")
                        return data
                except Exception as e:
                    print(f"❌ Akıllı Arama Hatası: {e}")
                    return data
            else:
                return data

        # --- 1. YAYINLAR ---
        # Genellikle varsayılan sekme yayınlardır veya "Makale" sekmesi.
        # YÖK yapısında sekmeler genellikle id ile ayrılır.
        # Tüm tablo satırlarını (tr) alalım, ama sekmeleri gezmek daha garanti.
        # Şimdilik basitçe görüneni alalım, sonra tıklayalım.
        
        # --- SEKMELERİ GEZME MANTIĞI ---
        # YÖK Sayfasında sekmelerin ID'leri genellikle:
        # id="tab_Article" -> Makaleler
        # id="tab_Project" -> Projeler
        # id="tab_Award" -> Ödüller
        # id="tab_Thesis" -> Tezler
        # (Bu ID'ler tahminidir, ancak genellikle text içeriğine göre tıklayabiliriz)

        tabs_to_click = {
            "Makale": "publications",
            "Bildiri": "conference_papers",  # Conference papers section
            # "Proje": "projects",
            # "Ödül": "awards",
            # "Tez": "theses" # "Yönetilen Tezler" - User requested only publications
        }

        for tab_text, key in tabs_to_click.items():
            print(f"👉 Processing Tab: {key} ({tab_text})")
            try:
                # Sekmeyi bul ve tıkla (kısmi eşleşme)
                try:
                     # . kullanmak, iç içe elementlerdeki text'i de kapsar (ör: <span>Makale</span>)
                     tab_element = driver.find_element(By.XPATH, f"//a[contains(., '{tab_text}')]")
                     driver.execute_script("arguments[0].click();", tab_element)
                     time.sleep(2) # Yüklenmesini bekle
                except Exception as click_e:
                     # Eğer zaten Makale sayfasındaysak ve "Makale" sekmesi tıklanabilir değilse (active class vs) hata verebilir.
                     # Bu durumda devam etmeliyiz, çünkü zaten oradayızdır.
                     if key == "publications":
                         print(f"   ⚠️ '{tab_text}' tıklanamadı (Zaten aktif olabilir), devam ediliyor... Hata: {click_e}")
                     else:
                         raise click_e # Diğer sekmeler için kritik hata
                
                # --- INFINITE SCROLL ---
                # YÖK Lazy Load kullanıyor, tüm veriyi çekmek için aşağı kadar inmeliyiz.
                
                # 1. Strateji: Window Scroll
                last_height = driver.execute_script("return document.body.scrollHeight")
                stuck_counter = 0
                
                for i in range(10): # 15 -> 10'a düşürüldü, yeterli.
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1) # 2s -> 1s'e düşürüldü hız için.
                    
                    # 2. Strateji: HTML/Body Scroll (Bazı siteler için)
                    driver.execute_script("document.documentElement.scrollTop = document.documentElement.scrollHeight")
                    
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    
                    if new_height == last_height:
                        stuck_counter += 1
                        if stuck_counter >= 2: # 2 kere değişmezse dur
                            break
                    else:
                        stuck_counter = 0
                    last_height = new_height

                # İçeriği parse et
                soup = BeautifulSoup(driver.page_source, 'html.parser')
                
                # --- AKILLI ELEMENT SEÇİCİ ---
                # Hem tablo satırlarını (tr) hem de modern görünümdeki (div.list-group-item vb.) öğeleri ara
                candidate_elements = soup.find_all(['tr', 'div', 'p', 'li'])
                
                fetched_items = []
                seen_normalized = set()
                
                print(f"   📊 Analiz edilen öğe sayısı: {len(candidate_elements)}")

                for el in candidate_elements:
                    # Satırın ham metni
                    full_text = el.get_text(" ", strip=True) # Boşlukla birleştir
                    if not full_text or len(full_text) < 10: continue
                    
                    # Yıl Kontrolü (En belirleyici özellik)
                    # 1990-2030 arası yılları ara
                    year_matches = re.findall(r'\b(199[0-9]|20[0-2][0-9])\b', full_text)
                    if not year_matches:
                        continue # Yıl yoksa makale değildir (genellikle)
                    
                    found_year = year_matches[-1] # Genellikle en sondaki yıl yayın yılıdır
                    
                    # Başlık Ayıklama
                    # Genellikle yılın öncesindeki uzun metin parçası başlıktır.
                    # Ancak tam başlığı çekmek zor olabilir, bu yüzden temizlenmiş full text'i alalım
                    # veya eleman içindeki <a> tag'ine bakalım (çoğu makale linklidir)
                    
                    title_candidate = ""
                    link_text = ""
                    
                    # Varsa linkin textini al (En temizi)
                    a_tag = el.find('a')
                    if a_tag:
                         link_text = a_tag.get_text(strip=True)
                    
                    if link_text and len(link_text) > 20:
                        title_candidate = link_text
                    else:
                        # Link yoksa metni temizle
                        # Tarihleri ve "Telif", "Yazar" gibi keywordleri at
                        clean_text = full_text
                        for y in year_matches:
                            clean_text = clean_text.replace(y, "")
                        
                        # Kalan en uzun parça muhtemelen başlıktır
                        parts = [p.strip() for p in clean_text.split() if len(p.strip()) > 3]
                        if len(parts) > 3:
                            title_candidate = " ".join(parts) # Basit birleştirme
                        else:
                            title_candidate = full_text # Fallback
                            
                    # --- NOISE FILTER ---
                    # UI elementlerini temizle
                    noise_keywords = ["Toggle navigation", "Yükseköğretim Kurulu", "Kişisel Bilgiler", 
                                      "Telif Hakkı", "English", "Anasayfa", "Birlikte çalıştığı kişiler", 
                                      "Detaylı Arama", "Akademisyenler", "Bölümler"]
                    if any(nk in title_candidate for nk in noise_keywords):
                        continue

                    # --- URL/DOI FILTER (NEW) ---
                    # Check if the title candidate looks like a URL
                    tc_lower = title_candidate.lower()
                    if "http" in tc_lower or "www." in tc_lower or "doi.org" in tc_lower or "dx.doi" in tc_lower:
                        continue
                    
                    # Check if it's just a single long word (likely a compacted URL)
                    if " " not in title_candidate.strip() and len(title_candidate) > 20:
                        continue

                    # Son düzenleme
                    final_title = title_candidate
                    if found_year not in final_title:
                         final_title = f"{final_title} ({found_year})"

                    # Filtreleme
                    if key == "publications":
                        # Makale sekmesindeyiz, yıl bulduk, yeterli.
                        pass
                    
                    elif key == "conference_papers":
                        # Bildiri sekmesindeyiz, yıl bulduk, yeterli.
                        pass
                    
                    elif key == "projects" and ("Proje" in full_text or "TÜBİTAK" in full_text or "BAP" in full_text):
                        pass
                         
                    elif key == "awards" and ("Ödül" in full_text or "Award" in full_text):
                        pass
                    
                    elif key == "theses" and ("Tez" in full_text or "Danışman" in full_text):
                        pass
                    else:
                        # Eğer sekme spesifik keyword yoksa ama genel yapı uyuyorsa (Yıl var, uzun metin var)
                        # ve biz 'publications' veya 'conference_papers' sekmesindeysek kabul et.
                        if key not in ["publications", "conference_papers"]:
                            continue

                    # --- TYPE DETECTION ---
                    pub_type = 'Other'
                    full_text_lower = full_text.lower()
                    if 'makale' in full_text_lower or 'article' in full_text_lower:
                        pub_type = 'Journal'
                    elif 'bildiri' in full_text_lower or 'conference' in full_text_lower or 'proceeding' in full_text_lower or 'konferans' in full_text_lower:
                        pub_type = 'Conference'
                    elif 'kitap' in full_text_lower or 'chapter' in full_text_lower:
                        pub_type = 'Book'

                    # Normalization function
                    def normalize_title(t):
                         return re.sub(r'[^a-zA-Z0-9]', '', t.lower())

                    # Dedup Check
                    normalized = normalize_title(final_title)
                    
                    # Aşırı kısa veya anlamsızları ele
                    if len(normalized) < 15: continue
                    
                    if normalized not in seen_normalized:
                        seen_normalized.add(normalized)
                        # Store as dict
                        fetched_items.append({
                            'title': final_title,
                            'type': pub_type,
                            'year': found_year,
                            'raw_text': full_text[:200]
                        })
                
                data[key] = fetched_items
                print(f"   -> {tab_text}: {len(data[key])} öge (Dedup sonrası)")
                
                # İstatistik: Tür dağılımı
                if key == 'publications':
                    type_counts = {}
                    for item in fetched_items:
                        t = item['type']
                        type_counts[t] = type_counts.get(t, 0) + 1
                    print(f"      📊 Tür Dağılımı: {type_counts}")

            except Exception as e:
                print(f"   ⚠️ Sekme Hatası ({tab_text}): {e}")
                pass
        
        return data

        return data

    except Exception as e:
        print(f"❌ YÖK Genel Tarama Hatası: {e}")
        return data
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass # Zaten kapalıysa sorun yok

# Eski fonksiyonların yerine wrapperlar (uyumluluk için)
def get_yok_publications(yok_id, name=None):
    return scrape_yok_profile(yok_id, name)['publications']

def get_yok_projects(yok_id, name=None):
    return scrape_yok_profile(yok_id, name)['projects']

def get_yok_paper_count(yok_id, name=None):
    # Eğer isim verilmişse scrape fonksiyonu akıllı arama yapar
    data = scrape_yok_profile(yok_id, name)
    pubs = data['publications']
    
    # Eğer yeni bir ID çözüldüyse, onu da döndürmenin bir yolunu bulmalıyız.
    # Ancak bu basit wrapper sadece sayı döndürüyor.
    # ID güncelleme işini çağıran yer (app.py) yapmalı.
    
    return len(pubs), data.get('resolved_id')
