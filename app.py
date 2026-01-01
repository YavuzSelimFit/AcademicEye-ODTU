import os
import re

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from flask import Flask, render_template, request, redirect, url_for, session, flash
from functools import wraps

# --- VERİTABANI FONKSİYONLARI ---
from database import (
    init_db, add_user, check_user_login, get_user_by_id,
    get_user_history, update_user_preferences,
    update_user_mendeley_token, get_user_mendeley_token,
    update_scholar_stats, get_user_profile_stats,
    add_project, update_yok_id, update_yok_stats,
    is_user_admin
)

# --- MOTORLAR (FEED & CAREER) ---
from modules.feed_engine.vector_engine import add_user_interest_vector
from modules.feed_engine.processor import suggest_arxiv_categories
from modules.feed_engine.mendeley_engine import get_mendeley_auth_url, get_token_from_code
from modules.career_engine.scholar_bot import search_scholar_by_id, analyze_career_stats
from modules.career_engine.yok_bot import get_yok_projects, get_yok_paper_count

# Veritabanını Başlat (Her çalışma anında kontrol et)
init_db()

app = Flask(__name__)
app.secret_key = "gizli_anahtar_buraya"

# --- ADMIN DECORATOR ---
def admin_required(f):
    """Admin yetkisi gerektiren route'lar için decorator"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Lütfen önce giriş yapın.', 'error')
            return redirect(url_for('login'))
        if not is_user_admin(session['user_id']):
            flash('Bu sayfaya erişim yetkiniz yok.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function



# --- TEMEL ROTALAR ---
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/pricing')
def pricing():
    return render_template('pricing.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        ad = request.form.get('ad')
        soyad = request.form.get('soyad')
        email = request.form.get('email')
        password = request.form.get('password')
        chat_id = request.form.get('chat_id')
        whatsapp_phone = request.form.get('whatsapp_phone')  # Yeni: WhatsApp
        keywords = request.form.get('keywords')
        university = request.form.get('university')

        print("⏳ Kategori tahmin ediliyor...")
        kategori = suggest_arxiv_categories(keywords)
        full_name = f"{ad} {soyad}"

        user_id = add_user(full_name, chat_id, email, password, university, kategori, keywords)

        if user_id:
            add_user_interest_vector(user_id, keywords)
            
            # WhatsApp numarasını ekle (varsa)
            if whatsapp_phone:
                from database import update_user_whatsapp_phone
                update_user_whatsapp_phone(user_id, whatsapp_phone)
                print(f"✅ WhatsApp numarası kaydedildi: {whatsapp_phone}")
            
            return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = check_user_login(email, password)

        if user:
            session['user_id'] = user['id']
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error="Hatalı bilgiler!")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = get_user_by_id(user_id)
    papers = get_user_history(user_id)
    mendeley_status = True if user['mendeley_token'] else False

    # İstatistikleri Çek (Scholar, YÖK ID, Yayın Sayıları vb.)
    stats = get_user_profile_stats(user_id)
    
    # Admin kontrolü
    is_admin = is_user_admin(user_id)

    return render_template('dashboard.html',
                           user_name=user['name'],
                           interests=user['interests'],
                           keywords=user['keywords'],
                           current_style=user['style'],
                           current_detail=user['detail_level'],
                           papers=papers,
                           is_mendeley_connected=mendeley_status,
                           stats=stats,
                           is_admin=is_admin)



@app.route('/update_settings', methods=['POST'])
def update_settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    style = request.form.get('style')
    detail_level = request.form.get('detail_level')
    new_keywords = request.form.get('keywords')

    new_categories = suggest_arxiv_categories(new_keywords)
    add_user_interest_vector(user_id, new_keywords)
    update_user_preferences(user_id, style, detail_level, new_keywords, new_categories)

    return redirect(url_for('dashboard'))


# --- SCOPUS ENTEGRASYONU (IEEE/Scholar Yerine) ---
@app.route('/update_scopus_link', methods=['POST'])
def update_scopus_link():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    with open("app_debug.log", "a", encoding="utf-8") as f:
        f.write(f"DEBUG APP: Route hit. Method={request.method}, Action={request.form.get('action')}\n")

    user_id = session['user_id']
    input_val = request.form.get('scopus_input') # Link veya ID
    action = request.form.get('action') # 'auto' olabilir
    
    from modules.career_engine.scopus_bot import search_scopus_author_via_google, get_scopus_publications
    
    # 1. Input Analizi
    scopus_id = None
    target_name = None
    
    if action == 'auto' and not input_val:
        # DB'den ismi çek
        user = get_user_by_id(user_id)
        # İsmi unvanlardan temizle (Prof. Dr. vs)
        raw_name = user['name']
        titles = [r'Prof\.?', r'Dr\.?', r'Doc\.?', r'Doç\.?', r'Arş\.?', r'Gör\.?', r'Öğr\.?', r'Üyesi\.?', r'Yrd\.?']
        clean_name = raw_name
        for t in titles:
            clean_name = re.sub(t, '', clean_name, flags=re.IGNORECASE)
        target_name = clean_name.strip()
        print(f"🔄 Otomatik Scopus Bağlama: {target_name}")
    elif input_val:
        # Link ise: https://www.scopus.com/authid/detail.uri?authorId=37085387500
        if "scopus.com/authid" in input_val:
            match = re.search(r'authorId=(\d+)', input_val)
            if match:
                scopus_id = match.group(1)
        
        # Sadece sayı ise (ID varsayalım)
        elif input_val.isdigit() and len(input_val) > 5:
            scopus_id = input_val
            
        # Değilse İSİM olarak aratalım
        else:
            target_name = input_val
            
    # Eğer ID yoksa ama isim varsa, ismi arat
    if not scopus_id and target_name:
        print(f"🔎 Scopus İsim Araması: {target_name}")
        scopus_id = search_scopus_author_via_google(target_name)
        
    if scopus_id:
        print(f"✅ Scopus ID Tespit Edildi: {scopus_id}")
        
        from database import update_scopus_id
        update_scopus_id(user_id, scopus_id)

        # İlk taramayı hemen yap
        try:
            raw_data = get_scopus_publications(scopus_id)
            pubs = raw_data.get('publications', [])
            
            paper_count = len(pubs)
            
            # İstatistikleri güncelle (Scholar sütunlarını Scopus verisiyle dolduruyoruz ki UI çalışsın)
            # update_scholar_stats(user_id, scholar_id, citations, h_index, paper_count)
            # Metrikleri şimdilik 0 geçiyoruz, önemli olan yayın sayısı ve karşılaştırma.
            
            update_scholar_stats(user_id, "SCOPUS_" + scopus_id, 0, 0, paper_count)
            
            print(f"✅ İlk Scopus verisi çekildi: {paper_count} yayın.")

            # 3. Analizi Tetikle (Rapor oluşsun)
            from modules.career_engine.career_manager import analyze_single_user
            print(f"🔄 Scopus sonrası analiz tetikleniyor...")
            analyze_single_user(user_id)
            
        except Exception as e:
            print(f"⚠️ İlk Scopus tarama hatası: {e}")

    else:
        print("❌ Scopus Profili Bulunamadı.")

    return redirect(url_for('dashboard'))


# --- YÖK ENTEGRASYONU (DİREKT ID GİRİŞİ) ---
@app.route('/update_yok_id', methods=['POST'])
def update_yok_id_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    user = get_user_by_id(user_id) # İsim için kullanıcıyı çek
    
    # İsmi Temizle (Unvanlardan arındır: "Prof. Dr. Ali" -> "Ali")
    raw_name = user['name']
    titles = [r'Prof\.?', r'Dr\.?', r'Doc\.?', r'Doç\.?', r'Arş\.?', r'Gör\.?', r'Öğr\.?', r'Üyesi\.?', r'Yrd\.?']
    clean_name = raw_name
    for t in titles:
        clean_name = re.sub(t, '', clean_name, flags=re.IGNORECASE)
    
    user_name = clean_name.strip()
    print(f"🧹 İsim Temizlendi: '{raw_name}' -> '{user_name}'")

    # Kullanıcı talebi üzerine manuel ID denemesi kaldırıldı. Tamamen isme dayalı çözümleme.
    target_id = None 
    print(f"🚀 YÖK Otomatik Bağlama Başlatıldı: Kullanıcı='{user_name}' (Akıllı ID Çözümleme)")

    try:
        # 2. Tek Seferde Tüm Veriyi Çek (Optimize Edildi)
        from modules.career_engine.yok_bot import scrape_yok_profile
        
        print(f"🔄 YÖK Verileri Çekiliyor: {user_name}...")
        
        # target_id varsa kullan, yoksa isimle ara
        yok_data = scrape_yok_profile(target_id if target_id else "00000", name=user_name)
        
        # Sonuçları Ayrıştır
        publications = yok_data.get('publications', [])
        projects = yok_data.get('projects', [])
        resolved_id = yok_data.get('resolved_id')
        
        paper_count = len(publications)
        
        # Eğer sistem bir ID bulduysa (veya güncellediyse)
        current_id = None
        if resolved_id:
            print(f"✅ ID TESPİT EDİLDİ/GÜNCELLENDİ: {resolved_id}")
            update_yok_id(user_id, resolved_id)
            current_id = resolved_id
        elif target_id:
            current_id = target_id
            
        if current_id or paper_count > 0:
            # ID bulunamasa bile isimle veri geldiyse kaydet (ID kısmı boş kalabilir veya eski ID korunur)
            if not current_id:
                # Mevcut kullanıcının ID'si var mı veritabanından bakılabilir ama şimdilik pas geçiyoruz
                pass
                
            update_yok_stats(user_id, current_id if current_id else "Bilinmiyor", paper_count)
            print(f"✅ YÖK Verileri Güncellendi. Yayın Sayısı: {paper_count}")
            
            # 3. Projeleri Kaydet
            for p in projects:
                add_project(
                    user_id=user_id,
                    title=p[:150], # Basit string listesi dönüyor artık
                    source='YÖK',
                    role='Araştırmacı/Yürütücü',
                    year='xxxx',
                    status='Tamamlandı'
                )
            print(f"✅ Projeler Çekildi: {len(projects)} adet")
            
        else:
            print("❌ YÖK Profil Bulunamadı.")

    except Exception as e:
        print(f"⚠️ YÖK Bağlama Hatası: {e}")

    # 4. Kapsamlı Analiz Başlat (Rapor Oluşturma)
    try:
        from modules.career_engine.career_manager import analyze_single_user
        print(f"🔄 Detaylı Analiz Tetikleniyor: User {user_id}")
        analyze_single_user(user_id)
    except Exception as e:
        print(f"⚠️ Analiz Hatası: {e}")

    return redirect(url_for('dashboard'))


# --- MENDELEY ---
@app.route('/connect_mendeley')
def connect_mendeley():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    auth_url = get_mendeley_auth_url()
    return redirect(auth_url)


@app.route('/mendeley_callback')
def mendeley_callback():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    try:
        token = get_token_from_code(request.url)
        update_user_mendeley_token(session['user_id'], token)
        return "<h1>✅ Mendeley Bağlandı!</h1><p>Pencereyi kapatıp panele dönebilirsiniz.</p><a href='/dashboard'>Panele Dön</a>"
    except Exception as e:
        return f"<h1>❌ Hata Oluştu</h1><p>{e}</p>"


@app.route('/mismatched_articles')
def mismatched_articles():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    stats = get_user_profile_stats(user_id)
    
    # Rapor yoksa boş liste gönder
    report = stats.get('analysis_report', {}) or {}
    missing_yok_articles = report.get('missing_yok_articles', [])
    missing_yok_conferences = report.get('missing_yok_conferences', [])
    
    # --- YAYINCI GRUPLAMA MANTIĞI ---
    # Yayınları kaynaklarına (Publisher) göre kutulara dağıtıyoruz
    
    publisher_keywords = {
        'IEEE': ['IEEE', 'Institute of Electrical-Electronics'],
        'Springer': ['Springer', 'Nature'], # Nature genelde Springer ile anılır veya ayrı tutulabilir
        'Wiley': ['Wiley'],
        'Elsevier': ['Elsevier', 'ScienceDirect'],
        'ACM': ['ACM', 'Association for Computing Machinery'],
        'Taylor & Francis': ['Taylor', 'Francis'],
        'Sage': ['Sage'],
        'IOP': ['IOP', 'Institute of Physics'],
        'AIP': ['AIP', 'American Institute of Physics'],
        'MDPI': ['MDPI'],
        'Frontiers': ['Frontiers'],
        'PLOS': ['PLOS', 'Public Library of Science'],
        'Oxford': ['Oxford'],
        'Cambridge': ['Cambridge']
    }
    
    def group_by_publisher(publications):
        """Helper function to group publications by publisher"""
        grouped = {}
        for pub in publications:
            venue = pub.get('venue', '').strip()
            found_group = 'Diğer Dergiler & Kaynaklar'
            
            # Keyword Search
            for main_pub, keywords in publisher_keywords.items():
                for kw in keywords:
                    if kw.lower() in venue.lower():
                        found_group = main_pub
                        break
                if found_group != 'Diğer Dergiler & Kaynaklar':
                    break
            
            if found_group not in grouped:
                grouped[found_group] = []
            grouped[found_group].append(pub)
        return grouped
    
    # Gruplama - Articles
    grouped_articles = group_by_publisher(missing_yok_articles)
    
    # Gruplama - Conferences
    grouped_conferences = group_by_publisher(missing_yok_conferences)

    return render_template('mismatched_articles.html', 
                           grouped_articles=grouped_articles,
                           grouped_conferences=grouped_conferences,
                           total_articles=len(missing_yok_articles),
                           total_conferences=len(missing_yok_conferences))


# --- ADMIN PANEL ROUTES ---
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin paneli ana sayfası"""
    user_id = session['user_id']
    user = get_user_by_id(user_id)
    
    # Sistem istatistikleri
    from database import get_all_users, get_all_admin_users
    all_users = get_all_users()
    all_admins = get_all_admin_users()
    
    return render_template('admin_dashboard.html',
                           user_name=user['name'],
                           total_users=len(all_users),
                           total_admins=len(all_admins))


@app.route('/admin/metu_eee_report', methods=['GET', 'POST'])
@admin_required
def admin_metu_eee_report():
    """ODTÜ EEE Scopus raporu"""
    return render_template('admin_metu_eee_report.html')


@app.route('/admin/metu_eee_data', methods=['POST'])
@admin_required
def admin_metu_eee_data():
    """AJAX endpoint - ODTÜ EEE verilerini çeker"""
    import json
    from modules.career_engine.scopus_bot import get_department_report
    
    # Form'dan gelen parametreler
    year = request.form.get('year', '2025')
    mode = request.form.get('mode', 'auto')  # 'auto' veya 'manual'
    faculty_list_raw = request.form.get('faculty_list', '')
    
    faculty_list = []
    if mode == 'manual' and faculty_list_raw:
        # Her satıra bir isim
        faculty_list = [name.strip() for name in faculty_list_raw.split('\n') if name.strip()]
    
    try:
        # Scopus'tan veriyi çek
        report_data = get_department_report(
            faculty_list=faculty_list if mode == 'manual' else None,
            year=int(year),
            department='Middle East Technical University',
            affiliation_id='60105072'
        )
        
        return json.dumps(report_data, ensure_ascii=False), 200, {'Content-Type': 'application/json; charset=utf-8'}
    
    except Exception as e:
        return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json; charset=utf-8'}


# --- WHATSAPP WEBHOOK ---
@app.route('/whatsapp/webhook', methods=['GET', 'POST'])
def whatsapp_webhook():
    """
    WhatsApp Cloud API Webhook Endpoint
    
    GET: Meta doğrulama endpoint'i
    POST: Kullanıcıdan gelen mesajları işler
    """
    import os # Added import for os.getenv
    if request.method == 'GET':
        # Meta doğrulama (Setup sırasında)
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', 'academic_eye_webhook_2024')
        
        if mode == 'subscribe' and token == verify_token:
            print(f"✅ Webhook doğrulandı!")
            return challenge, 200
        else:
            print(f"❌ Webhook doğrulama başarısız!")
            return 'Unauthorized', 403
    
    if request.method == 'POST':
        try:
            data = request.json
            
            # Mesaj var mı kontrol et
            if not data.get('entry'):
                return 'OK', 200
            
            entry = data['entry'][0]
            changes = entry.get('changes', [])
            
            if not changes:
                return 'OK', 200
            
            value = changes[0].get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                return 'OK', 200
            
            # İlk mesajı işle
            message = messages[0]
            phone = message.get('from')  # Gönderen numara
            message_type = message.get('type')
            
            print(f"📩 WhatsApp Mesajı Alındı: {phone} - Type: {message_type}")
            
            # Kullanıcıyı bul
            from database import get_user_by_whatsapp_phone, get_pending_paper, log_sent_paper
            user = get_user_by_whatsapp_phone(phone)
            
            if not user:
                print(f"⚠️ Kullanıcı bulunamadı: {phone}")
                return 'OK', 200
            
            # Pending makaleyi bul
            pending = get_pending_paper(user['id'])
            
            if not pending:
                print(f"⚠️ Pending makale yok: {user['name']}")
                # Kullanıcıya bilgi mesajı gönder
                from modules.feed_engine.whatsapp_notifier import send_whatsapp_message
                send_whatsapp_message(phone, "Şu an size uygun bir makale önerisi yok. Yeni makaleler tarandığında bilgilendirileceksiniz.")
                return 'OK', 200
            
            print(f"✅ Pending Makale Bulundu: {pending['paper_title']}")
            
            # Tam özeti gönder
            from modules.feed_engine.whatsapp_notifier import send_whatsapp_message, send_whatsapp_audio
            from modules.feed_engine.audio import text_to_speech
            
            # Telegram gibi tam mesaj
            full_message = f"""👋 Sayın {user['name']},

🚨 **Özel Seçki**

{pending['paper_summary']}

🔗 Link: {pending['paper_url']}"""
            
            # Mesajı gönder
            print(f"📤 Tam özet gönderiliyor...")
            msg_id = send_whatsapp_message(phone, full_message)
            
            if msg_id:
                # Ses dosyası oluştur ve gönder
                print(f"🎙️ Ses oluşturuluyor...")
                audio_file = text_to_speech(pending['paper_summary'], style=user.get('style', 'samimi'))
                
                if audio_file:
                    print(f"📤 Ses gönderiliyor...")
                    send_whatsapp_audio(phone, audio_file)
                
                # Bilgi mesajı
                info_msg = "📣 30 dakika içinde bu makaleyle ilgili sorularınızı yanıtlayabilirim!"
                send_whatsapp_message(phone, info_msg)
                
                # Veritabanına kaydet
                log_sent_paper(
                    user_id=user['id'],
                    title=pending['paper_title'],
                    url=pending['paper_url'],
                    summary=pending['paper_summary'],
                    full_text=pending['full_text'],
                    telegram_message_id=msg_id
                )
                
                # Pending'i sil
                from database import delete_pending_paper
                delete_pending_paper(pending['id'])
                
                print(f"✅ Özet ve ses gönderildi, pending silindi.")
            
            return 'OK', 200
            
        except Exception as e:
            print(f"❌ Webhook Hatası: {e}")
            import traceback
            traceback.print_exc()
            return 'OK', 200  # Meta'ya hata döndürme, 200 dön


if __name__ == '__main__':
    init_db()
    print("🌍 Web Sunucusu Başlatılıyor...")
    print("👉 http://127.0.0.1:5000")
    app.run(debug=True, port=5000)