import time
import sqlite3
import difflib
import re
from database import get_all_users, update_scholar_stats, DB_NAME, update_yok_id, get_user_profile_stats, get_user_by_id, save_career_analysis
from modules.career_engine.scholar_bot import search_scholar_profile, analyze_career_stats, search_scholar_by_id, get_scholar_publications
from modules.career_engine.yok_bot import get_yok_publications, find_yok_id_by_name
from modules.career_engine.google_search_bot import verify_with_google
from modules.career_engine.yok_bot import scrape_yok_profile, find_yok_id_by_name

def get_existing_scholar_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT scholar_id FROM user_profiles WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

def is_similar_title(t1, t2, threshold=0.85):
    """
    İki başlığın benzer olup olmadığını kontrol eder.
    Küçük/büyük harf ve noktalama işaretlerinden bağımsız karşılaştırma yapar.
    """
    # Basit temizlik
    # Basit temizlik (alfanümerik ve boşluk)
    # "voltage-tunable" -> "voltagetunable" gibi birleşmemesi için boşluğu koru
    # ama yine de difflib için clean versiyon da lazım.
    
    def clean_text(text):
        # Sadece harf ve rakamları bırak, gerisini boşluk yap
        text = re.sub(r'[^a-zA-Z0-9]', ' ', text).lower()
        # Fazla boşlukları temizle
        return ' '.join(text.split())

    t1_clean = clean_text(t1)
    t2_clean = clean_text(t2)
    
    # Boş ise
    if not t1_clean or not t2_clean:
        return False

    # 1. Tam Eşleşme
    if t1_clean == t2_clean:
        return True

    # 2. İçerme Kontrolü (Substring)
    # Örn: "Title" in "Longer Title with details"
    # Ancak çok kısa kelimeler için yapma (örn "Analysis")
    if len(t1_clean) > 15 and len(t2_clean) > 15:
        if t1_clean in t2_clean or t2_clean in t1_clean:
            return True

    # 3. Kelime Kümesi (Token Set) Karşılaştırması
    # "Large format dual band" vs "Large format voltage tunable dual band"
    s1 = set(t1_clean.split())
    s2 = set(t2_clean.split())
    
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    
    if union == 0: return False
    
    jaccard = intersection / union
    
    # Kelime çakışması %60'tan fazlaysa ve kelime sayısı yakınsa kabul et
    # Veya biri diğerinin %80'ini kapsıyorsa
    
    # Daha esnek: Kesişim, kısa olanın %85'ini oluşturuyor mu?
    min_len = min(len(s1), len(s2))
    if min_len > 0 and (intersection / min_len) > 0.8:
        return True

    # 4. Difflib (Karakter bazlı fuzzy match)
    return difflib.SequenceMatcher(None, t1_clean, t2_clean).ratio() > threshold

def analyze_single_user(user_id):
    """
    Tek bir kullanıcı için YÖK ve Scholar verilerini çeker, karşılaştırır ve raporu kaydeder.
    App.py tarafından 'Otomatik Bağla' sonrası tetiklenebilir.
    """
    user = get_user_by_id(user_id)
    if not user:
        print(f"❌ User ID {user_id} bulunamadı.")
        return None

    name = user['name']
    university = user['university']
    print(f"\\n👤 DETAYLI ANALİZ BAŞLATILIYOR: {name} | {university}")

    # 1. MEVCUT PROFİL VERİLERİNİ ÇEK
    user_profile = get_user_profile_stats(user_id)
    current_yok_id = user_profile['yok_id']
    current_scholar_id = user_profile['scholar_id']

    # 2. YÖK ID KONTROL
    if not current_yok_id:
        print(f"   🔎 YÖK ID aranıyor...")
        found_yok_id = find_yok_id_by_name(name)
        if found_yok_id:
            current_yok_id = found_yok_id
            update_yok_id(user_id, current_yok_id)
        else:
            print(f"   ❌ YÖK ID bulunamadı.")
    
    # 3. VERİLERİ ÇEK (YÖK ve IEEE)
    yok_data = {'publications': [], 'projects': [], 'awards': [], 'theses': []}
    if current_yok_id:
        yok_data = scrape_yok_profile(current_yok_id, name=name)
        if yok_data.get('resolved_id') and yok_data['resolved_id'] != current_yok_id:
                update_yok_id(user_id, yok_data['resolved_id'])
                current_yok_id = yok_data['resolved_id']
                
        print(f"   📚 YÖK Verileri: {len(yok_data['publications'])} Yayın")

    # --- SCOPUS ENTEGRASYONU (IEEE/Scholar Yerine) ---
    from modules.career_engine.scopus_bot import search_scopus_author_via_google, get_scopus_publications
    
    current_scopus_id = user_profile.get('scopus_id')
    found_scopus_id = current_scopus_id
    
    if not found_scopus_id:
        print(f"   🔎 Scopus Profili aranıyor (Kayıtlı ID yok)...")
        found_scopus_id = search_scopus_author_via_google(name)
        # ID bulunursa kaydet
        if found_scopus_id:
             from database import update_scopus_id
             update_scopus_id(user_id, found_scopus_id)
    else:
        print(f"   ℹ️ Scopus ID zaten kayıtlı: {found_scopus_id}. Yeniden aranmıyor.")

    scopus_pubs_data = []
    if found_scopus_id:
        raw_data = get_scopus_publications(found_scopus_id)
        scopus_pubs_data = raw_data.get('publications', [])
        print(f"   🎓 Scopus Yayın Sayısı: {len(scopus_pubs_data)}")
    else:
        print("   ❌ Scopus Profili bulunamadı.")
    
    # Karşılaştırma için Scopus verilerini kullanacağız
    scholar_pubs_data = scopus_pubs_data 
    scholar_pub_titles = [p['title'] for p in scopus_pubs_data]
    print(f"   🎯 Karşılaştırma için Scopus Yayınları: {len(scholar_pubs_data)} adet")

    # 4. KARŞILAŞTIRMA VE DOĞRULAMA (Raporlama)
    analysis_report = {
        'missing_scopus_articles': [],      # YÖK'te var, Scopus'ta yok (Makale)
        'missing_yok_articles': [],         # Scopus'ta var, YÖK'te yok (Makale)
        'missing_scopus_conferences': [],   # YÖK'te var, Scopus'ta yok (Bildiri)
        'missing_yok_conferences': [],      # Scopus'ta var, YÖK'te yok (Bildiri)
        'stats': {
            'yok_article_count': len([p for p in yok_data['publications'] if isinstance(p, dict) and p.get('type') != 'Conference']),
            'yok_conference_count': len(yok_data.get('conference_papers', [])),
            'scopus_article_count': len([p for p in scholar_pubs_data if p.get('type') == 'Journal']),
            'scopus_conference_count': len([p for p in scholar_pubs_data if p.get('type') == 'Conference']),
            'scopus_citation': 0, 
            'scopus_h_index': 0  
        }
    }

    # A) MAKALE KARŞILAŞTIRMASI (Journal Articles)
    if yok_data['publications'] and scholar_pubs_data:
        print("\n   🔍 [MAKALE KONTROLÜ] Scopus vs YÖK Analiz...")
        
        # YÖK makale başlıkları (sadece Journal type olanlar)
        yok_article_titles = []
        for yp in yok_data['publications']:
            if isinstance(yp, dict):
                t_title = yp.get('title', '')
                t_type = yp.get('type', 'Other')
                # Conference olmayan her şey makale sayılır
                if t_type != 'Conference':
                    yok_article_titles.append(t_title)
            else:
                # String ise varsayılan olarak makale kabul et
                yok_article_titles.append(str(yp))
        
        # Scopus makale listesi (sadece Journal)
        scopus_articles = [p for p in scholar_pubs_data if p.get('type') == 'Journal']
        
        # Scopus'ta olup YÖK'te olmayan makaleler
        for s_pub_obj in scopus_articles:
            s_title = s_pub_obj['title']
            found = False
            for y_title in yok_article_titles:
                if is_similar_title(s_title, y_title):
                    found = True
                    break
            if not found:
                analysis_report['missing_yok_articles'].append(s_pub_obj)
        
        if analysis_report['missing_yok_articles']:
            print(f"      ⚠️ {len(analysis_report['missing_yok_articles'])} makale YÖK'te EKSİK.")
        else:
            print("      ✅ Makaleler tam senkronize (Scopus vs YÖK).")

    # B) BİLDİRİ KARŞILAŞTIRMASI (Conference Papers)
    if yok_data.get('conference_papers') and scholar_pubs_data:
        print("\n   🔍 [BİLDİRİ KONTROLÜ] Scopus vs YÖK Analiz...")
        
        # YÖK bildiri başlıkları
        yok_conference_titles = []
        for yc in yok_data['conference_papers']:
            if isinstance(yc, dict):
                yok_conference_titles.append(yc.get('title', ''))
            else:
                yok_conference_titles.append(str(yc))
        
        # Scopus bildiri listesi (sadece Conference)
        scopus_conferences = [p for p in scholar_pubs_data if p.get('type') == 'Conference']
        
        # Scopus'ta olup YÖK'te olmayan bildiriler
        for s_pub_obj in scopus_conferences:
            s_title = s_pub_obj['title']
            found = False
            for y_title in yok_conference_titles:
                if is_similar_title(s_title, y_title):
                    found = True
                    break
            if not found:
                analysis_report['missing_yok_conferences'].append(s_pub_obj)
        
        if analysis_report['missing_yok_conferences']:
            print(f"      ⚠️ {len(analysis_report['missing_yok_conferences'])} bildiri YÖK'te EKSİK.")
        else:
            print("      ✅ Bildiriler tam senkronize (Scopus vs YÖK).")
    elif scholar_pubs_data:
        # YÖK'te bildiri sekmesi boş ama Scopus'ta var
        scopus_conferences = [p for p in scholar_pubs_data if p.get('type') == 'Conference']
        if scopus_conferences:
            print(f"\n   ℹ️ YÖK'te bildiri sekmesi boş, Scopus'ta {len(scopus_conferences)} bildiri var.")
            # Kullanıcı bildiri eklemiyor olabilir, uyarı olarak gösterelim ama eksik olarak işaretlemeyelim
            # analysis_report['missing_yok_conferences'].extend(scopus_conferences)

    # B) TEZLER (Yönetilen Tezler vs IEEE Yayınları)
    if yok_data['theses'] and scholar_pub_titles:
        print("\\n   🔍 [TEZ KONTROLÜ] Yönetilen Tezler vs IEEE...")
        for thesis in yok_data['theses']:
            found = False
            for s_pub in scholar_pub_titles:
                # Eşik düşürüldü çünkü tez başlığı ile yayın başlığı değişebilir
                if is_similar_title(thesis, s_pub, threshold=0.6):
                    found = True
                    break
            if not found:
                    # analysis_report['unverified_theses'].append(thesis) # Eski yapı
                    pass # Şimdilik rapora eklemiyoruz, basit tutalım.

    # Veritabanı Kaydı (İstatistikleri güncelle)
    # update_scholar_stats yerine update_ieee_stats kullanmalıyız ama
    # DB'de hala scholar_paper_count vs var. Orayı "External Source" gibi görelim şimdilik.
    from database import update_scholar_stats # Geçici, bunu düzeltmek lazım
    
    # İstatistik Güncelleme (App.py'de yapılıyor ama burası da yapabilir)
    # IEEE ID kaydedildi mi? analyze_single_user'da kaydedilmemiş.
    # İstatistik Güncelleme (App.py'de yapılıyor ama burası da yapabilir)
    # Scopus ID kaydedildi mi?
    if found_scopus_id:
        from database import update_scopus_id
        update_scopus_id(user_id, found_scopus_id)
        
        update_scholar_stats(user_id, "SCOPUS_" + found_scopus_id, 0, 0, len(scholar_pubs_data))
        print(f"   📊 İstatistik Güncellendi: Tot:{len(scholar_pubs_data)}")

    # C) PROJELER (Google Doğrulama)
    if yok_data['projects']:
        # print("\\n   🔍 [PROJE KONTROLÜ] Google Taraması...")
        # for proj in yok_data['projects']:
        #     # verify_with_google(title_search, name)
        #     pass 
        pass

    # 5. RAPORU KAYDET
    save_career_analysis(user_id, analysis_report)
    print("✅ Analiz raporu veritabanına kaydedildi.")
    return analysis_report

def update_all_career_stats():
    print("🚀 KARİYER MOTORU (TAM AKILLI MOD - GENİŞLETİLMİŞ) BAŞLATILIYOR...")
    print("-" * 50)

    users = get_all_users()

    if not users:
        print("❌ Kullanıcı yok.")
        return

    for user in users:
        analyze_single_user(user['id'])
        time.sleep(2)
    
    print("-" * 50)
    print("✅ Tüm kullanıcılar işlendi.")