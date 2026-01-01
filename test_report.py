from modules.career_engine.scopus_bot import get_department_report

# Test: 2 hoca ile 2024 yılı
faculty_list = [
    "Gözde Bozdağı Akar",
    "Tolga Çiloğlu"
]

print("Testing department report with 2024...")
report = get_department_report(
    faculty_list=faculty_list,
    year=2024,
    department='Middle East Technical University',
    affiliation_id='60105072'
)

print("\n" + "="*50)
print("REPORT SUMMARY:")
print("="*50)
print(f"Total Faculty: {len(report['faculty_data'])}")
print(f"Articles (International): {report['total_articles_international']}")
print(f"Articles (National): {report['total_articles_national']}")
print(f"Conferences (International): {report['total_conferences_international']}")
print(f"Conferences (National): {report['total_conferences_national']}")

print("\n" + "="*50)
print("FACULTY DETAILS:")
print("="*50)
for faculty in report['faculty_data']:
    print(f"\n{faculty['name']}:")
    print(f"  Author ID: {faculty['author_id']}")
    print(f"  Articles (Int): {faculty['total_articles_international']}")
    print(f"  Articles (Nat): {faculty['total_articles_national']}")
    print(f"  Conferences (Int): {faculty['total_conferences_international']}")
    print(f"  Conferences (Nat): {faculty['total_conferences_national']}")
