import sqlite3

DB_NAME = 'academic_memory.db'

def check_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM users")
    users = cursor.fetchall()
    print("📋 DB'deki Kullanıcılar:")
    for u in users:
        print(f"   ID: {u[0]} | Name: {u[1]} | Repr: {repr(u[1])}")
    conn.close()

if __name__ == "__main__":
    check_users()
