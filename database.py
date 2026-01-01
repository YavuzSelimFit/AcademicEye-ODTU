# FILE: database.py (TAM HALİ)
import sqlite3
import json

DB_NAME = "academic_memory.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()

    # 1. KULLANICILAR TABLOSU
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            chat_id TEXT,
            email TEXT UNIQUE,
            password TEXT,
            university TEXT,
            interests TEXT,
            keywords TEXT,
            mendeley_token TEXT,
            style TEXT DEFAULT 'samimi',
            detail_level TEXT DEFAULT 'orta',
            is_admin INTEGER DEFAULT 0
        )
    ''')

    # 2. MAKALELER GEÇMİŞİ TABLOSU
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            url TEXT,
            summary TEXT,
            full_text TEXT,               -- YENİ: Sohbet için tam metin
            telegram_message_id INTEGER,  -- YENİ: Reply takibi için
            date_sent TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Migration: user_history tablosuna yeni kolonları ekle
    try:
        cursor.execute("ALTER TABLE user_history ADD COLUMN full_text TEXT")
    except sqlite3.OperationalError:
        pass 

    try:
        cursor.execute("ALTER TABLE user_history ADD COLUMN telegram_message_id INTEGER")
    except sqlite3.OperationalError:
        pass

    # 3. AKADEMİK KİMLİK KARTI (GÜNCELLENDİ)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id INTEGER PRIMARY KEY,
            scholar_id TEXT,
            yok_id TEXT,
            orcid_id TEXT,
            linkedin_url TEXT,
            total_citations INTEGER DEFAULT 0,
            h_index INTEGER DEFAULT 0,
            scholar_paper_count INTEGER DEFAULT 0,  -- Scholar Yayın Sayısı
            yok_paper_count INTEGER DEFAULT 0,      -- YÖK Yayın Sayısı
            ieee_id TEXT,                           -- IEEE Author ID (YENI)
            analysis_report TEXT,                   -- Kariyer Analiz Raporu (JSON)
            last_scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Mevcut veritabanları için kolon ekleme (Migration)
    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN analysis_report TEXT")
    except sqlite3.OperationalError:
        pass # Kolon zaten varsa hata verir, geç.

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN ieee_id TEXT")
    except sqlite3.OperationalError:
        pass # ieee_id zaten varsa geç.

    try:
        cursor.execute("ALTER TABLE user_profiles ADD COLUMN scopus_id TEXT")
    except sqlite3.OperationalError:
        pass # scopus_id zaten varsa geç.

    # Migration: users tablosuna is_admin ekle
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass # is_admin zaten varsa geç.
    
    # Migration: users tablosuna whatsapp_phone ekle
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN whatsapp_phone TEXT")
    except sqlite3.OperationalError:
        pass # whatsapp_phone zaten varsa geç.
    
    # 5. BEKLEYEN WHATSAPP MAKALELERİ (Webhook Akışı İçin)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pending_papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            paper_title TEXT,
            paper_url TEXT,
            paper_summary TEXT,
            full_text TEXT,
            paper_keywords TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 4. PROJELER TABLOSU
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            source TEXT,
            role TEXT,
            year TEXT,
            status TEXT,
            UNIQUE(user_id, title)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- KULLANICI İŞLEMLERİ ---
def add_user(name, chat_id, email, password, university, interests, keywords):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, chat_id, email, password, university, interests, keywords, style, detail_level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, chat_id, email, password, university, interests, keywords, 'samimi', 'orta'))
        conn.commit()
        new_id = cursor.lastrowid
        return new_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def check_user_login(email, password):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_preferences(user_id, style, detail_level, keywords, interests):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET style = ?, detail_level = ?, keywords = ?, interests = ? 
        WHERE id = ?
    """, (style, detail_level, keywords, interests, user_id))
    conn.commit()
    conn.close()
    print(f"✅ Kullanıcı {user_id} tercihleri güncellendi.")

def get_user_by_id(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user_mendeley_token(user_id, token_dict):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    token_str = json.dumps(token_dict)
    cursor.execute("UPDATE users SET mendeley_token = ? WHERE id = ?", (token_str, user_id))
    conn.commit()
    conn.close()

def get_user_mendeley_token(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT mendeley_token FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    if result and result[0]:
        return json.loads(result[0])
    return None

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def get_user_id_by_chat_id(chat_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE chat_id = ?", (str(chat_id),))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# --- GEÇMİŞ / ARŞİV İŞLEMLERİ ---
def log_sent_paper(user_id, title, url, summary, full_text=None, telegram_message_id=None):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM user_history WHERE user_id = ? AND url = ?", (user_id, url))
    if cursor.fetchone():
        conn.close()
        return

    cursor.execute("INSERT INTO user_history (user_id, title, url, summary, full_text, telegram_message_id) VALUES (?, ?, ?, ?, ?, ?)",
                   (user_id, title, url, summary, full_text, telegram_message_id))
    conn.commit()
    conn.close()

def get_user_history(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_history WHERE user_id = ? ORDER BY date_sent DESC", (user_id,))
    papers = cursor.fetchall()
    conn.close()
    return papers

def is_paper_processed_globally(url):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM user_history WHERE url = ?", (url,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_paper_context(user_id, message_id=None):
    """
    Belirli bir mesajın yanıtı mı diye bakar, yoksa son makaleyi getirir.
    Dönen: (title, summary, full_text) veya None
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 1. Mesaj ID'si ile arama (REPLY durumu)
    if message_id:
        cursor.execute("SELECT * FROM user_history WHERE telegram_message_id = ?", (message_id,))
        paper = cursor.fetchone()
        if paper:
            conn.close()
            print(f"📎 Mesaj ID {message_id} ile makale bulundu: {paper['title']}")
            return dict(paper)
    
    # 2. Bulunamadıysa veya ID yoksa -> Kullanıcının SON makalesini getir
    cursor.execute("SELECT * FROM user_history WHERE user_id = ? ORDER BY date_sent DESC LIMIT 1", (user_id,))
    paper = cursor.fetchone()
    conn.close()
    
    if paper:
        print(f"📎 Son gönderilen makale seçildi: {paper['title']}")
        return dict(paper)
    
    return None

# --- KARİYER MOTORU İŞLEMLERİ (GÜNCELLENDİ) ---

def get_user_profile_stats(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
    data = cursor.fetchone()
    conn.close()
    
    if not data:
        return {
            'total_citations': 0, 'h_index': 0, 'scholar_id': None,
            'yok_id': None, 'scholar_paper_count': 0, 'yok_paper_count': 0,
            'last_scan_date': None, 'analysis_report': None
        }
    
    # Row nesnesini dict'e çevir ve JSON'ı parse et
    result = dict(data)
    if result.get('analysis_report'):
        try:
            result['analysis_report'] = json.loads(result['analysis_report'])
        except:
            result['analysis_report'] = None
            
    return result

def save_career_analysis(user_id, report_data):
    """
    Kariyer analiz raporunu (sözlük) JSON olarak kaydeder.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    report_json = json.dumps(report_data, ensure_ascii=False)
    
    cursor.execute("""
        INSERT INTO user_profiles (user_id, analysis_report) 
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            analysis_report=excluded.analysis_report
    """, (user_id, report_json))
    
    conn.commit()
    conn.close()

def update_scholar_stats(user_id, scholar_id, citations, h_index, paper_count=0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # UPSERT: Varsa güncelle, yoksa ekle
    cursor.execute("""
        INSERT INTO user_profiles (user_id, scholar_id, total_citations, h_index, scholar_paper_count) 
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            scholar_id=excluded.scholar_id,
            total_citations=excluded.total_citations,
            h_index=excluded.h_index,
            scholar_paper_count=excluded.scholar_paper_count
    """, (user_id, scholar_id, citations, h_index, paper_count))
    conn.commit()
    conn.close()

def update_yok_id(user_id, yok_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_profiles (user_id, yok_id) 
        VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET yok_id=excluded.yok_id
    """, (user_id, yok_id))
    conn.commit()
    conn.close()

def update_yok_stats(user_id, yok_id, paper_count):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_profiles 
        SET yok_paper_count = ? 
        WHERE user_id = ?
    """, (paper_count, user_id))
    conn.commit()
    conn.close()

def add_project(user_id, title, source, role, year, status):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO user_projects (user_id, title, source, role, year, status) VALUES (?, ?, ?, ?, ?, ?)",
                       (user_id, title, source, role, year, status))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Zaten varsa ekleme
    finally:
        conn.close()

def update_ieee_id(user_id, ieee_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)", (user_id,))
    cursor.execute("UPDATE user_profiles SET ieee_id = ? WHERE user_id = ?", (ieee_id, user_id))
    conn.commit()
    conn.close()

def update_scopus_id(user_id, scopus_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_profiles (user_id) VALUES (?)", (user_id,))
    cursor.execute("UPDATE user_profiles SET scopus_id = ? WHERE user_id = ?", (scopus_id, user_id))
    conn.commit()
    conn.close()

# --- ADMIN İŞLEMLERİ ---
def create_admin_user(name, email, password):
    """
    Admin kullanıcı oluşturur.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (name, chat_id, email, password, university, interests, keywords, style, detail_level, is_admin) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (name, '', email, password, 'Admin', '', '', 'samimi', 'orta', 1))
        conn.commit()
        new_id = cursor.lastrowid
        print(f"✅ Admin kullanıcı oluşturuldu: {name} (ID: {new_id})")
        return new_id
    except sqlite3.IntegrityError:
        print(f"❌ Bu email zaten kayıtlı: {email}")
        return None
    finally:
        conn.close()

def is_user_admin(user_id):
    """
    Kullanıcının admin olup olmadığını kontrol eder.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT is_admin FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] == 1 if result else False

def set_user_admin_status(user_id, is_admin):
    """
    Kullanıcının adminlik durumunu günceller.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_admin = ? WHERE id = ?", (is_admin, user_id))
    conn.commit()
    conn.close()

def get_all_admin_users():
    """
    Tüm admin kullanıcıları listeler.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email FROM users WHERE is_admin = 1")
    admins = cursor.fetchall()
    conn.close()
    return admins


# --- WHATSAPP İŞLEMLERİ ---
def add_pending_paper(user_id, paper_title, paper_url, paper_summary, full_text, paper_keywords):
    """WhatsApp webhook için pending makale ekler"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO pending_papers 
        (user_id, paper_title, paper_url, paper_summary, full_text, paper_keywords)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, paper_title, paper_url, paper_summary, full_text, paper_keywords))
    conn.commit()
    conn.close()
    print(f"✅ Pending paper eklendi: {paper_title}")


def get_pending_paper(user_id):
    """Kullanıcının bekleyen makalesini getirir"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM pending_papers 
        WHERE user_id = ? 
        ORDER BY created_at DESC 
        LIMIT 1
    """, (user_id,))
    paper = cursor.fetchone()
    conn.close()
    return dict(paper) if paper else None


def delete_pending_paper(paper_id):
    """İşlenen pending makaleyi siler"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM pending_papers WHERE id = ?", (paper_id,))
    conn.commit()
    conn.close()


def get_user_by_whatsapp_phone(phone):
    """WhatsApp numarasına göre kullanıcı bulur"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE whatsapp_phone = ?", (phone,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def update_user_whatsapp_phone(user_id, whatsapp_phone):
    """Kullanıcının WhatsApp numarasını günceller"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET whatsapp_phone = ? WHERE id = ?", (whatsapp_phone, user_id))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    init_db()
