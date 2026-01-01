# ODTÜ EEE Öğretim Üyeleri - Scopus Author ID Listesi

Bu dosya, Scopus API'nin yetkilendirme sorunu nedeniyle manuel olarak girilmiş author ID'lerini içermektedir.

## Nasıl Kullanılır?

1. Scopus'ta hocayı manuel olarak arayın: https://www.scopus.com/search/form.uri?display=author
2. Hocanın Scopus profilini bulun
3. URL'deki Author ID'yi kopyalayın (örn: `authorId=57211427815`)
4. Aşağıdaki listeye ekleyin

## Format
```python
METU_EEE_AUTHORS = {
    "Hoca Adı": "Scopus Author ID",
}
```

## ODTÜ EEE Hocaları

```python
METU_EEE_AUTHORS = {
    # Örnek (Gerçek ID'leri ekleyin):
    # "Gözde Bozdağı Akar": "7004446862",
    # "Nevzat Güneri Gençer": "7004285807",
    
    # Buraya manuel olarak ekleyin
}
```

## Nasıl Eklerim?

### Adım 1: Scopus'ta Ara
https://www.scopus.com/search/form.uri?display=author

### Adım 2: Affiliation Filtrele
"Middle East Technical University" + "Electrical and Electronics Engineering"

### Adım 3: Author ID'yi Kopyala
Hoca profilinin URL'sinden:
```
https://www.scopus.com/authid/detail.uri?authorId=7004446862
                                                  ^^^^^^^^^^
```

### Adım 4: Listeye Ekle
```python
"Öğretim Üyesinin Adı": "7004446862",
```

---

## Alternatif: API Key Güncelleme

Eğer Scopus API key'inizi upgrade ederseniz (Author Search yetkisi ile), bu manuel process'e gerek kalmaz.

Elsevier Developer Portal: https://dev.elsevier.com/
