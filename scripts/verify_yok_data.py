import sys
import json
from modules.career_engine.yok_bot import scrape_yok_profile, find_yok_id_by_name

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_yok_data.py <name_or_id>")
        return

    target = sys.argv[1]
    
    print(f"🔍 Verifying YÖK Data for: {target}")
    
    # Check if input is ID or Name
    if target.isdigit():
        yok_id = target
        name = "Unknown"
    else:
        name = target
        yok_id = find_yok_id_by_name(name)
        if not yok_id:
            print("⚠️ ID lookup via Google failed. Attempting internal search via `scrape_yok_profile` fallback...")
            yok_id = None # Let the scraper try to find it internaly

    print(f"🆔 Target YÖK ID: {yok_id if yok_id else 'None (Will search internally)'}")
    
    data = scrape_yok_profile(yok_id, name=name)
    
    print("\n" + "="*40)
    print("📊 SCRAPED DATA SUMMARY")
    print("="*40)
    print(f"Publications: {len(data.get('publications', []))}")
    print(f"Projects:     {len(data.get('projects', []))}")
    print(f"Awards:       {len(data.get('awards', []))}")
    print(f"Theses:       {len(data.get('theses', []))}")
    
    print("\n📝 Sample Publications (First 5):")
    for pub in data.get('publications', [])[:5]:
        print(f" - {pub}")

    print("\n📝 Sample Projects (First 3):")
    for proj in data.get('projects', [])[:3]:
        print(f" - {proj}")

    # Save to file for inspection
    with open("yok_verification_dump.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        
    print("\n✅ Full dump saved to 'yok_verification_dump.json'")

if __name__ == "__main__":
    main()
