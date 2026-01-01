import edge_tts
import asyncio
import os
import re
import google.generativeai as genai
import wave
from dotenv import load_dotenv

# FFmpeg ve Pydub
try:
    import static_ffmpeg
    static_ffmpeg.add_paths()  # FFmpeg binary'lerini path'e ekle
    from pydub import AudioSegment
    FFMPEG_AVAILABLE = True
    print("✅ FFmpeg yüklendi ve hazır.")
except ImportError as e:
    print(f"⚠️ FFmpeg/Pydub hatası: {e}")
    FFMPEG_AVAILABLE = False
except Exception as e:
    print(f"⚠️ FFmpeg başlatma hatası: {e}")
    FFMPEG_AVAILABLE = False

load_dotenv()

# Emojileri ve Markdown işaretlerini temizleme fonksiyonu
def clean_text_for_audio(text):
    # 1. Markdown kalınlaştırmaları sil (**text** -> text)
    text = text.replace("**", "").replace("__", "").replace("#", "")

    # 2. Linkleri sil (http... ile başlayanları okumasın)
    text = re.sub(r'http\S+', 'makale linki mesajdadır.', text)

    # 3. Köşeli parantezleri sil ([1], [Link] vb.)
    text = re.sub(r'\[.*?\]', '', text)

    return text


async def generate_audio_file(text, filename):
    """ EdgeTTS ile ses oluşturur (MP3) """
    voice = 'tr-TR-AhmetNeural'
    clean_text = clean_text_for_audio(text)
    communicate = edge_tts.Communicate(clean_text, voice)
    await communicate.save(filename)


def save_pcm_as_wav(pcm_data, filename):
    try:
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit PCM
            wav_file.setframerate(24000) 
            wav_file.writeframes(pcm_data)
        return True
    except Exception as e:
        print(f"❌ WAV Kayıt Hatası: {e}")
        return False


def convert_wav_to_mp3(wav_filename, mp3_filename):
    """WAV dosyasını MP3'e çevirir (WhatsApp uyumluluğu için)"""
    if not FFMPEG_AVAILABLE:
        print("❌ Dönüşüm yapılamıyor: FFmpeg yok.")
        return False
        
    try:
        audio = AudioSegment.from_wav(wav_filename)
        audio.export(mp3_filename, format="mp3")
        print(f"✅ Dönüşüm Başarılı: {mp3_filename}")
        
        # WAV dosyasını sil (isteğe bağlı)
        try:
            os.remove(wav_filename)
        except:
            pass
            
        return True
    except Exception as e:
        print(f"❌ MP3 Dönüşüm Hatası: {e}")
        return False


def generate_gemini_audio(text, filename, style="samimi"):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ API Key eksik.")
        return None

    try:
        genai.configure(api_key=api_key)
        model_name = 'gemini-2.0-flash-exp'  # Model güncellendi (deprecated uyarısı için)
        
        # Eğer flash-exp yoksa standart modeli deneriz, ama şimdilik kodda kalsın
        # Alternatif: gemini-1.5-flash
        
        voice_map = {
            "samimi": "Puck",
            "resmi": "Fenrir",
            "orta": "Kore",
            "dogal": "Aoede"
        }
        selected_voice = voice_map.get(style, "Puck")
        
        model = genai.GenerativeModel(model_name)
        
        # Kullanıcı promptu ile ses isteyelim (yeni API yapısı gerekebilir, 
        # ancak eski kodda generate_content ile speech_config kullanılmış. 
        # deprecated uyarısı aldık ama hala çalışıyorsa devam.)
        
        response = model.generate_content(
            text, 
            generation_config={
                "response_modalities": ["AUDIO"],
                "speech_config": {
                    "voice_config": {
                        "prebuilt_voice_config": {
                            "voice_name": selected_voice
                        }
                    }
                }
            }
        )
        
        for part in response.parts:
            if hasattr(part, 'inline_data'):
                # Önce WAV olarak kaydet
                wav_filename = filename.replace(".mp3", ".wav")
                if save_pcm_as_wav(part.inline_data.data, wav_filename):
                    print(f"🎙️ Gemini Sesi (WAV) Kaydedildi: {wav_filename}")
                    
                    # Sonra MP3'e çevir
                    if convert_wav_to_mp3(wav_filename, filename):
                        return filename
                    else:
                        return wav_filename # Çevrilemezse WAV döndür
                        
        return None
    except Exception as e:
        print(f"❌ Gemini Ses Hatası ({style}): {e}")
        return None


def text_to_speech(text, style="samimi"):
    print(f"🎙️ Ses Motoru Başlatılıyor ({style})...")
    
    filename = "ozet_sesi.mp3"
    clean_text = clean_text_for_audio(text)
    
    # 1. Önce Gemini Dene (Yüksek Kalite)
    result_file = generate_gemini_audio(clean_text, filename, style)
    
    if result_file and result_file.endswith(".mp3"):
        return result_file
    
    print("⚠️ Gemini başarısız oldu veya WAV döndü, EdgeTTS yedeğine geçiliyor...")
    
    # 2. Yedek: EdgeTTS (Zaten MP3 verir)
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(generate_audio_file(text, filename))
        print(f"💾 EdgeTTS (Yedek) ses kaydedildi: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Yedek Ses Hatası: {e}")
        return None

if __name__ == "__main__":
    text_to_speech("Bu bir ses testidir.")