import requests
import fitz  # PyMuPDF kütüphanesi
import os


def download_and_extract_text(arxiv_url):
    """
    ArXiv linkinden PDF'i indirir ve içindeki metni çıkarır.
    """
    print("📥 PDF İndiriliyor ve Okunuyor...")

    # 1. URL Dönüşümü (Abstract linkini PDF linkine çevir)
    # Örn: http://arxiv.org/abs/2301.12345 -> http://arxiv.org/pdf/2301.12345.pdf
    pdf_url = arxiv_url.replace("abs", "pdf") + ".pdf"

    try:
        # 2. PDF'i İndir
        response = requests.get(pdf_url)
        if response.status_code != 200:
            print("❌ PDF indirilemedi.")
            return None

        # 3. PDF'i Bellekte Aç (Diske kaydetmeye gerek yok)
        pdf_document = fitz.open(stream=response.content, filetype="pdf")

        text_content = ""

        # 4. Sayfaları Oku
        # Gemini kotasını korumak için genelde ilk 10-15 sayfa (Intro, Method, Results) yeterlidir.
        page_count = len(pdf_document)
        read_limit = min(page_count, 15)

        for i in range(read_limit):
            page = pdf_document.load_page(i)
            text_content += page.get_text()

        print(f"✅ PDF Okundu ({len(text_content)} karakter).")
        return text_content

    except Exception as e:
        print(f"❌ PDF Hatası: {e}")
        return None