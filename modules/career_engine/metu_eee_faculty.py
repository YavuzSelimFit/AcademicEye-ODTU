"""
ODTÜ EEE Öğretim Üyeleri - Scopus Author ID Mapping
Manuel olarak girilen Author ID'leri (API key yetkisi olmadığı için)
"""

METU_EEE_FACULTY = {
    # Format: "Ad Soyad": "Scopus_Author_ID"
    
    # Örnekler (Gerçek ID'ler - Scopus'tan bulunacak):
    # "Nevzat Güneri Gençer": "7004285807",  # Örnek ID
    
    # Ekran görüntüsünden gördüklerim:
    # TODO: Aşağıdaki her hoca için Scopus'tan Author ID bulun ve ekleyin
    # Nasıl bulunur: https://www.scopus.com/search/form.uri?display=author
    # 1. Hocanın adını arayın
    # 2. "Middle East Technical University" olan sonucu bulun
    # 3. URL'deki "authorId=XXXXXXX" kısmını kopyalayın
    
    "Gözde Bozdağı Akar": "",  # TODO
    "Elif Tuğçe Ceran Arslan": "",  # TODO
    "Tolga Çiloğlu": "",  # TODO
    "Şimşek Demir": "",  # TODO
    "Gülbin Dural": "",  # TODO
    "Ahmet Cemal Durgun": "",  # TODO
    "Özgür Ergül": "",  # TODO
    "Murat Eyüboğlu": "",  # TODO
    "Murat Gül": "",  # TODO
    "Ece Güran Schmidt": "",  # TODO
    "Gökhan Muzaffer Güvensen": "",  # TODO
    "Fatih Kamışlı": "",  # TODO
    "Ulaş Karaağaç": "",  # TODO
    "Ozan Keysan": "",  # TODO
}

def get_author_id(name):
    """
    Manuel dictionary'den author ID döndürür.
    Yoksa None döner.
    """
    # Normalize name (küçük harf, fazla boşlukları temizle)
    normalized_name = " ".join(name.strip().split())
    
    # Dictionary'de ara
    if normalized_name in METU_EEE_FACULTY:
        author_id = METU_EEE_FACULTY[normalized_name]
        if author_id:  # Boş string değilse
            return author_id
    
    return None
