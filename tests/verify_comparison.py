
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.career_engine.career_manager import is_similar_title

def test_comparison_logic():
    print("🧪 Testing IEEE vs YÖK Comparison Logic...")

    # Mock Data
    ieee_pubs = [
        {'title': 'Advanced Radar Systems', 'type': 'Journal', 'year': '2023'},       # Should be compared
        {'title': 'Conference on Deep Learning', 'type': 'Conference', 'year': '2023'}, # Should be IGNORED
        {'title': 'Missing Journal Paper', 'type': 'Journal', 'year': '2022'}         # Should be flagged as missing
    ]

    yok_titles = [
        'Advanced Radar Systems (2023)' # Match
    ]

    print("\n--- Step 1: Filtering IEEE Journals ---")
    scholar_pubs_data = [p for p in ieee_pubs if p.get('type') == 'Journal']
    print(f"Original IEEE Count: {len(ieee_pubs)}")
    print(f"Filtered (Journals Only): {len(scholar_pubs_data)}")
    
    assert len(scholar_pubs_data) == 2, "Filtering failed! Should have 2 journals."
    assert all(p['type'] == 'Journal' for p in scholar_pubs_data), "Non-Journal found in filtered list!"
    print("✅ Filtering Logic Passed")

    print("\n--- Step 2: Comparison (Finding Missing in YÖK) ---")
    missing_yok = []
    
    scholar_pub_titles = [p['title'] for p in scholar_pubs_data]
    
    for s_pub_obj in scholar_pubs_data:
        s_title = s_pub_obj['title']
        found = False
        for y_title in yok_titles:
            if is_similar_title(s_title, y_title):
                found = True
                print(f"   Match Found: '{s_title}' == '{y_title}'")
                break
        
        if not found:
            missing_yok.append(s_pub_obj)
            print(f"   ❌ Missing in YÖK: '{s_title}'")

    print(f"\nMissing Count: {len(missing_yok)}")
    
    assert len(missing_yok) == 1, "Comparison logic failed! Should find exactly 1 missing paper."
    assert missing_yok[0]['title'] == 'Missing Journal Paper', "Wrong paper identified as missing"
    
    print("✅ Comparison Logic Passed")

if __name__ == "__main__":
    test_comparison_logic()
