import arxiv
import requests
import datetime


def search_arxiv_by_code(category_code, limit=25):
    """
    ArXiv'i kendi "Kategori Diliyle" tarar. (En taze sonuçlar buradadır)
    """
    print(f"   📡 ArXiv (Native) Taranıyor: {category_code}...")
    client = arxiv.Client()

    # Kategorileri temizle (virgülleri ayır)
    cats = [c.strip() for c in category_code.split(",")]
    # Sorguyu oluştur: (cat:cs.AI OR cat:eess.SP)
    query = " OR ".join([f"cat:{c}" for c in cats])

    search = arxiv.Search(
        query=query,
        max_results=limit,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )

    results = []
    try:
        for paper in client.results(search):
            results.append({
                "title": paper.title,
                "authors": ", ".join([a.name for a in paper.authors]),
                "abstract": paper.summary,
                "url": paper.entry_id,  # ArXiv PDF linki
                "published": paper.published.strftime("%Y-%m-%d"),
                "source": "ArXiv"
            })
    except Exception as e:
        print(f"   ⚠️ ArXiv Hatası: {e}")

    return results


def search_semantic_scholar_by_keyword(keywords, limit=25):
    """
    Diğer kaynakları (IEEE, Springer) "Anahtar Kelime" ile tarar.
    """
    print(f"   📡 Semantic Scholar Taranıyor: '{keywords}'...")

    current_year = datetime.datetime.now().year
    url = "https://api.semanticscholar.org/graph/v1/paper/search"

    params = {
        "query": keywords,
        "limit": limit,
        "year": f"{current_year - 1}-{current_year}",
        "fields": "title,authors,abstract,url,publicationDate,isOpenAccess,openAccessPdf,venue"
    }

    results = []
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "data" in data:
                for item in data["data"]:
                    # PDF linki var mı?
                    pdf_link = item['url']
                    if item.get('openAccessPdf') and item['openAccessPdf']:
                        pdf_link = item['openAccessPdf']['url']

                    # ArXiv kaynaklarını buradan elemeye gerek yok,
                    # ana fonksiyonda ID kontrolü yapacağız.

                    results.append({
                        "title": item.get('title', 'Başlıksız'),
                        "authors": ", ".join([a['name'] for a in item.get('authors', [])]),
                        "abstract": item.get('abstract', ''),
                        "url": pdf_link,
                        "published": item.get('publicationDate', 'Tarih Yok'),
                        "source": item.get('venue', 'Semantic Scholar')
                    })
    except Exception as e:
        print(f"   ⚠️ Semantic Scholar Hatası: {e}")

    return results


def get_latest_papers(interests_code, keywords_text, limit=50):
    """
    ANA FONKSİYON: İki kaynağı birleştirir ve çakışmaları temizler.
    """
    # 1. ArXiv Taraması (Kod ile)
    arxiv_papers = search_arxiv_by_code(interests_code, limit=limit // 2)

    # 2. Semantic Scholar Taraması (Kelime ile)
    semantic_papers = search_semantic_scholar_by_keyword(keywords_text, limit=limit // 2)

    # 3. Birleştirme ve Tekilleştirme (Deduplication)
    all_papers = arxiv_papers + semantic_papers
    unique_papers = []
    seen_titles = set()

    for paper in all_papers:
        # Başlıkları temizleyip kıyasla (küçük harf, boşluksuz)
        clean_title = "".join(paper['title'].lower().split())

        if clean_title not in seen_titles:
            seen_titles.add(clean_title)
            unique_papers.append(paper)

    print(f"   ✅ Toplam {len(unique_papers)} eşsiz makale toplandı.")
    return unique_papers