from scholarly import scholarly


def normalize_turkish_chars(text):
    """
    Türkçe karakterleri İngilizce karşılıklarına çevirir.
    Örn: "Cengiz Beşikçi" -> "Cengiz Besikci"
    """
    if not text: return ""
    translation_table = str.maketrans("ğĞüÜşŞıİöÖçÇ", "gGuUsSiIoOcC")
    return text.translate(translation_table)


def is_same_university(found_aff, target_aff):
    """
    Bulunan kurum ile hedeflenen kurum aynı mı?
    """
    if not found_aff: return False

    # Hedef üniversite girilmediyse (None ise) her şeyi kabul et
    if not target_aff: return True

    print(f"      🕵️ Karşılaştırılıyor: '{found_aff}' vs '{target_aff}'")

    found_lower = found_aff.lower()
    target_lower = target_aff.lower()

    # Basit anahtar kelime kontrolü
    if target_lower in found_lower: return True

    # ODTÜ Özel Kontrolleri
    keywords = ["middle east", "metu", "odtu", "ankara"]
    for kw in keywords:
        if kw in found_lower and kw in target_lower:
            return True

    return False


def search_scholar_by_id(scholar_id):
    """
    Doğrudan ID ile profil çeker. (En güvenli yöntem)
    """
    print(f"🆔 ID ile bağlanılıyor: {scholar_id}...")
    try:
        author = scholarly.search_author_id(scholar_id)
        # fill() fonksiyonu tüm yayınları çeker, biraz zaman alabilir ama sayı için şart.
        print("⏳ Profil detayları ve yayınlar çekiliyor (biraz sürebilir)...")
        return scholarly.fill(author)
    except Exception as e:
        print(f"❌ ID ile bulunamadı: {e}")
        return None


def search_scholar_profile(name, target_university=None):
    """
    İsimden arama yapar, üniversite eşleşirse detayları çeker.
    """
    print(f"🔍 Akıllı Arama: '{name}' @ '{target_university}'...")

    # İsim varyasyonlarını hazırla
    search_queries = [name]
    english_name = normalize_turkish_chars(name)
    if english_name != name:
        search_queries.append(english_name)

    for query in search_queries:
        print(f"   👉 Sorgu gönderiliyor: '{query}'")
        try:
            search_query = scholarly.search_author(query)

            # İlk 5 sonuca bak
            count = 0
            for author in search_query:
                count += 1
                institution = author.get('affiliation', 'Bilinmiyor')
                found_name = author.get('name', 'Bilinmiyor')

                print(f"      🔎 [Sonuç {count}] Bulundu: {found_name} | Kurum: {institution}")

                if is_same_university(institution, target_university):
                    print(f"      ✅ EŞLEŞME DOĞRULANDI!")
                    print("      ⏳ Detaylar ve yayınlar çekiliyor...")
                    return scholarly.fill(author)

                if count >= 5: break

        except Exception as e:
            print(f"      ⚠️ Arama hatası: {e}")
            continue

    print("❌ Eşleşme bulunamadı.")
    return None


def analyze_career_stats(author_data):
    """
    Profilden istatistikleri ve YAYIN SAYISINI çeker.
    """
    if not author_data: return None

    stats = {
        'scholar_id': author_data['scholar_id'],
        'citations': author_data.get('citedby', 0),
        'h_index': author_data.get('hindex', 0),
        'i10_index': author_data.get('i10index', 0),
        'paper_count': 0,  # Varsayılan
        'interests': author_data.get('interests', []),
        'last_paper_date': 'Bilinmiyor',
        'last_paper_title': ''
    }

    # Yayınları Analiz Et
    if 'publications' in author_data:
        # 1. Yayın Sayısını Al (En kritik kısım burası)
        stats['paper_count'] = len(author_data['publications'])

        # 2. Son Yayın Tarihini Bul
        try:
            pubs = [p for p in author_data['publications'] if 'pub_year' in p['bib']]
            if pubs:
                pubs.sort(key=lambda x: int(x['bib']['pub_year']), reverse=True)
                stats['last_paper_date'] = pubs[0]['bib'].get('pub_year', '????')
                stats['last_paper_title'] = pubs[0]['bib'].get('title', '')
        except:
            pass

    return stats


# Test Bloğu (Dosyayı tek başına çalıştırırsan burası çalışır)
def get_scholar_publications(author_data):
    """
    Scholar profilinden yayın başlıklarını VE TİPLERİNİ döndürür.
    Return: [{'title': '...', 'type': 'Journal', 'venue': 'IEEE...', 'year': 2020}, ...]
    """
    if not author_data or 'publications' not in author_data:
        return []

    results = []
    
    journal_keywords = [
        "Journal", "Transactions", "Letters", "Review", "Magazine", 
        "Nature", "Science", "Applied Physics", "Optics", "Photonics",
        "Semiconductor", "Solid-State", "Physics", "Chemistry", "Engineering",
        "Infrared", "Technology", "Electronics" 
    ]
    # Konferanslar genellikle "Proceedings", "Symposium" vb. içerir
    conf_keywords = ["Conference", "Proceedings", "Symposium", "Workshop", "Congress", "Meeting", "Digest", "Abstracts"]

    for pub in author_data['publications']:
        if 'bib' in pub and 'title' in pub['bib']:
            title = pub['bib']['title']
            venue = pub['bib'].get('citation', '')
            year = pub['bib'].get('pub_year', '????')
            
            # Heuristic Classification
            ptype = "Bilinmiyor"
            if any(k in venue for k in journal_keywords):
                ptype = "Makale" # Journal Article
            elif any(k in venue for k in conf_keywords):
                ptype = "Bildiri" # Conference Paper
            elif "Thesis" in venue or "Tez" in venue:
                ptype = "Tez"
            
            results.append({
                'title': title,
                'venue': venue,
                'year': year,
                'type': ptype
            })
    
    return results


if __name__ == "__main__":
    # Test ID (Cengiz Hoca)
    test_id = "Jk98_FsAAAAJ"
    print("--- ID TESTİ ---")
    profil = search_scholar_by_id(test_id)

    if profil:
        analiz = analyze_career_stats(profil)
        print("\n📊 SONUÇLAR:")
        print(f"İsim: {profil['name']}")
        print(f"Toplam Atıf: {analiz['citations']}")
        print(f"H-Index: {analiz['h_index']}")
        print(f"Toplam Yayın Sayısı: {analiz['paper_count']} 📄")
        
        pubs = get_scholar_publications(profil)
        print(f"Çekilen Yayın Başlığı Sayısı: {len(pubs)}")
        if pubs:
            print(f"İlk Yayın: {pubs[0]}")