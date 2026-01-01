# FILE: paper_cache.py
# Makale metinlerini geçici olarak RAM'de tutan modül (30 dakika TTL)

import time
from threading import Lock

# Cache yapısı: { chat_id: { "title": ..., "content": ..., "timestamp": ... } }
_paper_cache = {}
_lock = Lock()

# 30 dakika = 1800 saniye
TTL_SECONDS = 30 * 60


def add_paper(chat_id, title, content):
    """Yeni gönderilen makaleyi cache'e ekler."""
    with _lock:
        _paper_cache[str(chat_id)] = {
            "title": title,
            "content": content,
            "timestamp": time.time()
        }
        print(f"📝 Cache'e eklendi: {title[:40]}... (Chat: {chat_id})")


def get_paper(chat_id):
    """
    Cache'den makale getirir. Süre dolmuşsa None döner ve temizler.
    Dönen: {"title": ..., "content": ...} veya None
    """
    with _lock:
        key = str(chat_id)
        if key not in _paper_cache:
            return None
        
        entry = _paper_cache[key]
        elapsed = time.time() - entry["timestamp"]
        
        if elapsed > TTL_SECONDS:
            # Süre dolmuş, temizle
            del _paper_cache[key]
            print(f"⏰ Süre doldu, cache temizlendi: {key}")
            return None
        
        remaining_mins = int((TTL_SECONDS - elapsed) / 60)
        print(f"✅ Cache'den okundu. Kalan süre: ~{remaining_mins} dk")
        return {"title": entry["title"], "content": entry["content"]}


def get_remaining_time(chat_id):
    """Kalan süreyi dakika olarak döndürür. Yoksa veya süresi dolmuşsa 0."""
    with _lock:
        key = str(chat_id)
        if key not in _paper_cache:
            return 0
        
        entry = _paper_cache[key]
        elapsed = time.time() - entry["timestamp"]
        remaining = TTL_SECONDS - elapsed
        
        return max(0, int(remaining / 60))


def clear_expired():
    """Süresi dolmuş tüm kayıtları temizler (opsiyonel bakım fonksiyonu)."""
    with _lock:
        now = time.time()
        expired_keys = [k for k, v in _paper_cache.items() if now - v["timestamp"] > TTL_SECONDS]
        for k in expired_keys:
            del _paper_cache[k]
        if expired_keys:
            print(f"🧹 {len(expired_keys)} eski kayıt temizlendi.")
