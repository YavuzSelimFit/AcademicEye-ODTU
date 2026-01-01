import os
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import TokenExpiredError
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("MENDELEY_CLIENT_ID")
CLIENT_SECRET = os.getenv("MENDELEY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("MENDELEY_REDIRECT_URI")

AUTHORIZATION_BASE_URL = 'https://api.mendeley.com/oauth/authorize'
TOKEN_URL = 'https://api.mendeley.com/oauth/token'


def get_mendeley_auth_url():
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    mendeley = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI, scope=["all"])
    authorization_url, state = mendeley.authorization_url(AUTHORIZATION_BASE_URL)
    return authorization_url


def get_token_from_code(authorization_response):
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    mendeley = OAuth2Session(CLIENT_ID, redirect_uri=REDIRECT_URI)
    token = mendeley.fetch_token(TOKEN_URL, client_secret=CLIENT_SECRET, authorization_response=authorization_response)
    return token


def add_paper_to_library(token_dict, title, url, abstract, user_id=None):
    """
    Makaleyi ekler. Eğer token süresi dolmuşsa, otomatik yenileyip tekrar dener.
    NOT: user_id parametresi eklendi (Yenilenen token'ı veritabanına kaydetmek için).
    """
    # Veritabanı fonksiyonunu içeride import ediyoruz (Döngüsel import hatası olmasın diye)
    from database import update_user_mendeley_token

    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # ArXiv ID temizliği
    arxiv_id = url.split("/")[-1].replace(".pdf", "")

    document = {
        "title": title,
        "type": "journal",
        "abstract": abstract[:1000],
        "identifiers": {"arxiv": arxiv_id},
        "websites": [url]
    }

    headers = {
        'Content-Type': 'application/vnd.mendeley-document.1+json',
        'Accept': 'application/vnd.mendeley-document.1+json'
    }

    client = OAuth2Session(CLIENT_ID, token=token_dict)

    try:
        response = client.post('https://api.mendeley.com/documents', json=document, headers=headers)

        # Eğer Token Süresi Dolmuşsa (401 Hatası)
        if response.status_code == 401:
            print("🔄 Token süresi dolmuş, yenileniyor...")

            # Token Yenileme İşlemi
            try:
                new_token = client.refresh_token(TOKEN_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

                # Yeni token'ı veritabanına kaydet (Ki bir sonraki sefer çalışsın)
                if user_id:
                    update_user_mendeley_token(user_id, new_token)
                    print("💾 Yeni token veritabanına kaydedildi.")

                # İşlemi yeni token ile tekrar dene
                client = OAuth2Session(CLIENT_ID, token=new_token)
                response = client.post('https://api.mendeley.com/documents', json=document, headers=headers)

            except Exception as e:
                print(f"❌ Yenileme Başarısız: {e}")
                return False

        if response.status_code == 201:
            print("✅ Mendeley'e başarıyla eklendi!")
            return True
        else:
            print(f"❌ Mendeley Hatası: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Bağlantı Hatası: {e}")
        return False