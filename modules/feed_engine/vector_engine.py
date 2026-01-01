import chromadb
from sentence_transformers import SentenceTransformer
import os

# Modeli yükle
print("🧠 Vektör modeli hazırlanıyor...")
model = SentenceTransformer('all-MiniLM-L6-v2')

# HATALI OLAN: DB_PATH = "../../academic_vector_db"
# DOĞRUSU (Eski hali):
DB_PATH = "./academic_vector_db"

client = chromadb.PersistentClient(path=DB_PATH)
collection = client.get_or_create_collection(name="academic_interests")


def vectorize_text(text):
    return model.encode(text).tolist()


def add_user_interest_vector(user_id, keywords):
    vector = vectorize_text(keywords)
    collection.upsert(
        ids=[str(user_id)],
        embeddings=[vector],
        metadatas=[{"keywords": keywords}],
        documents=[keywords]
    )
    print(f"📐 Hoca ID {user_id} vektörlendi.")


def search_relevant_users(paper_abstract, threshold=1.5):
    """
    threshold: Eşik değer.
    """
    # --- BU KISIM HATAYI BULACAK ---
    print(f"   🔎 DEBUG: Fonksiyona gelen threshold değeri: {threshold}")
    # -------------------------------

    paper_vector = vectorize_text(paper_abstract)

    results = collection.query(
        query_embeddings=[paper_vector],
        n_results=5,
    )

    matched_users = []

    if not results['ids'] or not results['ids'][0]:
        return []

    ids = results['ids'][0]
    distances = results['distances'][0]

    for i in range(len(ids)):
        dist = distances[i]
        user_id = ids[i]

        # Karşılaştırma Mantığı
        # Mesafe (dist) ne kadar KÜÇÜKSE, benzerlik o kadar fazladır.
        # Eğer mesafe, eşikten küçükse -> Eşleşme Var.

        if dist < threshold:
            print(f"      📏 Mesafe: {dist:.4f} < {threshold} -> ✅ UYGUN (ID: {user_id})")
            matched_users.append(int(user_id))
        else:
            print(f"      📏 Mesafe: {dist:.4f} > {threshold} -> ❌ UZAK (ID: {user_id})")

    return matched_users