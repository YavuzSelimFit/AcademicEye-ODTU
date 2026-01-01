import requests
import urllib.parse
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key from environment
API_KEY = os.getenv('SCOPUS_API_KEY')
if not API_KEY:
    raise ValueError("SCOPUS_API_KEY not found in environment variables. Please set it in .env file")

HEADERS = {
    "X-ELS-APIKey": API_KEY,
    "Accept": "application/json"
}

def search_scopus_author_via_google(name):
    """
    Search author using Scopus API (Direct HTTP).
    (Function name kept for compatibility with existing imports)
    """
    print(f"🔎 Scopus API Searching for: {name}")
    try:
        parts = name.strip().split()
        if len(parts) >= 2:
            last_name = parts[-1]
            first_name = parts[0]
            # Handle potential middle names or suffixes if needed
            # Query: AUTHFIRST(First) and AUTHLASTNAME(Last)
            query = f"AUTHLASTNAME({last_name}) and AUTHFIRST({first_name})"
        else:
            query = f"AUTHLASTNAME({name})"
            
        print(f"   API Query: {query}")
        
        url = "https://api.elsevier.com/content/search/author"
        params = {
            "query": query,
            "count": 10 # Get top matches
        }
        
        resp = requests.get(url, headers=HEADERS, params=params)
        
        if resp.status_code != 200:
            print(f"❌ API Error {resp.status_code}: {resp.text}")
            return None
            
        data = resp.json()
        
        # Parse search-results
        if 'search-results' in data and 'entry' in data['search-results']:
            entries = data['search-results']['entry']
            
            # Handle single result (dict) vs multiple (list)
            if isinstance(entries, dict):
                entries = [entries]
                
            if not entries:
                 print("   ⚠️ No authors found.")
                 return None

            print(f"   Found {len(entries)} candidates.")
            
            # Filter for Affiliation to improve accuracy
            for entry in entries:
                # author-id format: "author_id:700xxxx"
                raw_id = entry.get('dc:identifier', '')
                auth_id = raw_id.replace('AUTHOR_ID:', '')
                
                # Name parts
                given_name = entry.get('preferred-name', {}).get('ce:given-name', '')
                surname = entry.get('preferred-name', {}).get('ce:surname', '')
                
                # Affiliation
                affil_list = entry.get('affiliation-current', [])
                if isinstance(affil_list, dict): affil_list = [affil_list]
                
                affil_name = ""
                if affil_list:
                    affil_name = affil_list[0].get('affiliation-name', '')
                
                print(f"   Candidate: {given_name} {surname} (ID: {auth_id}) - {affil_name}")
                
                # Match "Middle East Technical University" matches
                if 'Middle East' in affil_name or 'ODTU' in affil_name or 'Ankara' in affil_name:
                    print(f"✅ Exact Scopus Match Found: {auth_id}")
                    return auth_id
            
            # If no affiliation match, return the first one
            first_id = entries[0].get('dc:identifier', '').replace('AUTHOR_ID:', '')
            print(f"✅ Scopus Match Found (First): {first_id}")
            return first_id
            
        else:
            print("❌ API: No 'search-results' in response.")
            return None

    except Exception as e:
        print(f"❌ Scopus API Search Error: {e}")
        return None

def get_scopus_publications(scopus_id):
    """
    Fetch publications using Scopus Search API (AU-ID).
    """
    print(f"📚 Fetching Scopus Data via API (ID: {scopus_id})...")
    data = {'publications': [], 'stats': {}}
    
    try:
        url = "https://api.elsevier.com/content/search/scopus"
        # Search query: AU-ID(id)
        params = {
            "query": f"AU-ID({scopus_id})",
            "count": 25, # Limit to 25 (default), usually Scopus requires pagination for more.
            # For now, let's fetch 100 to cover most users. Max count per page is often 25 or 200 depending on key level.
            # Start with 25 to be safe (User can page if needed, but we'll keep it simple first)
            "count": 100, 
            "view": "STANDARD" # Title, source etc.
        }
        
        resp = requests.get(url, headers=HEADERS, params=params)
        
        if resp.status_code != 200:
            print(f"❌ API Error {resp.status_code}: {resp.text}")
            return data
            
        rdata = resp.json()
        
        if 'search-results' in rdata and 'entry' in rdata['search-results']:
            entries = rdata['search-results']['entry']
            if isinstance(entries, dict): entries = [entries]
            
            for entry in entries:
                # Extract fields
                title = entry.get('dc:title', 'No Title')
                date = entry.get('prism:coverDate', '') # YYYY-MM-DD
                year = date.split('-')[0] if date else '????'
                venue = entry.get('prism:publicationName', '')
                publisher = entry.get('prism:publisher', '')
                
                # Combine if available
                if publisher and publisher not in venue:
                    venue = f"{venue} ({publisher})"
                doc_type_raw = entry.get('prism:aggregationType', '').lower()
                
                # Normalize Type
                pub_type = 'Unknown'
                if 'journal' in doc_type_raw:
                    pub_type = 'Journal'
                elif 'conference' in doc_type_raw or 'proceeding' in doc_type_raw:
                    pub_type = 'Conference'
                elif 'book' in doc_type_raw:
                    pub_type = 'Book'
                
                data['publications'].append({
                    'title': title,
                    'year': year,
                    'type': pub_type,
                    'venue': venue,
                    'publisher': publisher # Raw publisher for grouping
                })
                
            print(f"📊 Extracted {len(data['publications'])} publications via API.")
            
        else:
            print("   ⚠️ No publications found or empty response.")

    except Exception as e:
        print(f"❌ Scopus API Data Error: {e}")
        
    return data

# --- DEPARTMENT REPORTING FUNCTIONS ---

def search_authors_by_affiliation(institution_name, affiliation_id=None, department_keyword=None):
    """
    Affiliation bazlı yazar araması yapar.
    NOT: Bu fonksiyon Author Search API kullanır, eğer 401 hatası alırsanız
    manuel mod kullanın.
    """
    print(f"🔎 Affiliation Search: {institution_name}")
    authors = []
    
    try:
        url = "https://api.elsevier.com/content/search/author"
        
        # Query oluştur
        if affiliation_id:
            query = f"AF-ID({affiliation_id})"
        else:
            query = f'AFFIL("{institution_name}")'
        
        # Departman filtresi ekle (opsiyonel)
        if department_keyword:
            query += f' AND AFFIL("{department_keyword}")'
        
        params = {
            "query": query,
            "count": 25,  # Max per page
            "start": 0
        }
        
        resp = requests.get(url, headers=HEADERS, params=params)
        
        if resp.status_code != 200:
            print(f"❌ API Error {resp.status_code}: {resp.text}")
            return authors
        
        data = resp.json()
        
        if 'search-results' in data and 'entry' in data['search-results']:
            entries = data['search-results']['entry']
            if isinstance(entries, dict):
                entries = [entries]
            
            for entry in entries:
                # Hata girişlerini atla
                if 'error' in entry:
                    continue
                
                auth_id = entry.get('dc:identifier', '').replace('AUTHOR_ID:', '')
                given_name = entry.get('preferred-name', {}).get('ce:given-name', '')
                surname = entry.get('preferred-name', {}).get('ce:surname', '')
                full_name = f"{given_name} {surname}".strip()
                
                # Affiliation bilgisi
                affil_list = entry.get('affiliation-current', [])
                if isinstance(affil_list, dict):
                    affil_list = [affil_list]
                
                affil_name = affil_list[0].get('affiliation-name', '') if affil_list else ''
                
                authors.append({
                    'id': auth_id,
                    'name': full_name,
                    'affiliation': affil_name
                })
            
            print(f"✅ Found {len(authors)} authors")
        else:
            print("⚠️ No authors found")
    
    except Exception as e:
        print(f"❌ Affiliation Search Error: {e}")
    
    return authors


def get_publications_by_year(author_id, year):
    """
    Belirli bir yazarın belirli yıldaki yayınlarını getirir.
    Ulusal (Türkiye) ve Uluslararası olarak ayırır.
    """
    print(f"📅 Fetching {year} publications for author {author_id}...")
    result = {
        'articles_international': [],
        'articles_national': [],
        'conferences_international': [],
        'conferences_national': []
    }
    
    try:
        url = "https://api.elsevier.com/content/search/scopus"
        params = {
            "query": f"AU-ID({author_id}) AND PUBYEAR IS {year}",
            "count": 100,
            "view": "STANDARD"  # STANDARD view (COMPLETE requires higher API permissions)
        }
        
        resp = requests.get(url, headers=HEADERS, params=params)
        
        if resp.status_code != 200:
            print(f"❌ API Error {resp.status_code}: {resp.text[:200]}")
            return result
        
        data = resp.json()
        
        if 'search-results' in data and 'entry' in data['search-results']:
            entries = data['search-results']['entry']
            if isinstance(entries, dict):
                entries = [entries]
            
            for entry in entries:
                # Hata girişlerini atla
                if 'error' in entry:
                    continue
                
                title = entry.get('dc:title', 'No Title')
                date = entry.get('prism:coverDate', '')
                venue = entry.get('prism:publicationName', '')
                publisher = entry.get('prism:publisher', '')
                doc_type = entry.get('prism:aggregationType', '').lower()
                
                # Ulusal/Uluslararası tespiti (sadece venue/publisher ismine göre)
                is_national = False
                
                venue_lower = venue.lower()
                publisher_lower = publisher.lower()
                
                # Türkiye ipuçları
                turkish_keywords = ['turkey', 'turkish', 'türk', 'ankara', 'istanbul', 
                                   'izmir', 'ulusal', 'national', 'türkiye']
                
                for keyword in turkish_keywords:
                    if keyword in venue_lower or keyword in publisher_lower:
                        is_national = True
                        break
                
                pub_info = {
                    'title': title,
                    'venue': venue,
                    'publisher': publisher,
                    'date': date,
                    'country_type': 'Ulusal' if is_national else 'Uluslararası'
                }
                
                # Tip ve ülke ayrımı
                if 'journal' in doc_type:
                    if is_national:
                        result['articles_national'].append(pub_info)
                    else:
                        result['articles_international'].append(pub_info)
                elif 'conference' in doc_type or 'proceeding' in doc_type:
                    if is_national:
                        result['conferences_national'].append(pub_info)
                    else:
                        result['conferences_international'].append(pub_info)
                else:
                    # Belirsiz olanları uluslararası makale kategorisine koy
                    if is_national:
                        result['articles_national'].append(pub_info)
                    else:
                        result['articles_international'].append(pub_info)
        
        total_articles = len(result['articles_national']) + len(result['articles_international'])
        total_conferences = len(result['conferences_national']) + len(result['conferences_international'])
        
        print(f"   Articles: {total_articles} (Ulusal: {len(result['articles_national'])}, Uluslararası: {len(result['articles_international'])})")
        print(f"   Conferences: {total_conferences} (Ulusal: {len(result['conferences_national'])}, Uluslararası: {len(result['conferences_international'])})")
    
    except Exception as e:
        print(f"❌ Year Filter Error: {e}")
    
    return result


def get_department_report(faculty_list=None, year=2025, department=None, affiliation_id=None):
    """
    Bölüm genelinde hoca verilerini toplar.
    
    Args:
        faculty_list: Manuel hoca isimleri listesi (None ise otomatik arama)
        year: Yayın yılı filtresi
        department: Bölüm adı (affiliation search için)
        affiliation_id: Scopus Affiliation ID
    
    Returns:
        Dict with faculty data
    """
    import time
    
    print(f"📊 Department Report Generation Started (Year: {year})")
    report = {
        'faculty_data': [],
        'total_articles_international': 0,
        'total_articles_national': 0,
        'total_conferences_international': 0,
        'total_conferences_national': 0,
        'year': year
    }
    
    # 1. Hoca listesini belirle
    if faculty_list is None or len(faculty_list) == 0:
        # Otomatik mod: Affiliation'dan çek
        print("🔄 Auto mode: Searching by affiliation...")
        authors = search_authors_by_affiliation(
            department or "Middle East Technical University",
            affiliation_id=affiliation_id,
            department_keyword="Electrical"
        )
        faculty_list = [auth['name'] for auth in authors]
    
    print(f"👥 Processing {len(faculty_list)} faculty members...")
    
    # 2. Her hoca için veri çek
    for idx, name in enumerate(faculty_list, 1):
        print(f"\n[{idx}/{len(faculty_list)}] Processing: {name}")
        
        # Rate limiting (3 request/second max)
        if idx > 1:
            time.sleep(0.4)  # 2.5 req/sec
        
        # Author ID bul
        author_id = search_scopus_author_via_google(name)
        
        if not author_id:
            print(f"   ⚠️ Author ID not found for {name}")
            report['faculty_data'].append({
                'name': name,
                'author_id': None,
                'articles_international': [],
                'articles_national': [],
                'conferences_international': [],
                'conferences_national': [],
                'total_articles_international': 0,
                'total_articles_national': 0,
                'total_conferences_international': 0,
                'total_conferences_national': 0
            })
            continue
        
        # Yıl bazlı yayınları çek
        time.sleep(0.4)  # Rate limit
        pubs = get_publications_by_year(author_id, year)
        
        faculty_info = {
            'name': name,
            'author_id': author_id,
            'articles_international': pubs['articles_international'],
            'articles_national': pubs['articles_national'],
            'conferences_international': pubs['conferences_international'],
            'conferences_national': pubs['conferences_national'],
            'total_articles_international': len(pubs['articles_international']),
            'total_articles_national': len(pubs['articles_national']),
            'total_conferences_international': len(pubs['conferences_international']),
            'total_conferences_national': len(pubs['conferences_national'])
        }
        
        report['faculty_data'].append(faculty_info)
        report['total_articles_international'] += len(pubs['articles_international'])
        report['total_articles_national'] += len(pubs['articles_national'])
        report['total_conferences_international'] += len(pubs['conferences_international'])
        report['total_conferences_national'] += len(pubs['conferences_national'])
    
    print(f"\n✅ Department Report Complete:")
    print(f"   Articles - Uluslararası: {report['total_articles_international']}, Ulusal: {report['total_articles_national']}")
    print(f"   Conferences - Uluslararası: {report['total_conferences_international']}, Ulusal: {report['total_conferences_national']}")
    
    return report


if __name__ == '__main__':
    # Test
    sid = search_scopus_author_via_google("Nevzat Güneri Gençer")
    if sid:
        pubs = get_scopus_publications(sid)
        print(f"Sample: {pubs['publications'][:2]}")

