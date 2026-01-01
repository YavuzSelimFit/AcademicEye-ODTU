import sqlite3
from database import DB_NAME

def reset_yok_id(name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Find user
    cursor.execute("SELECT id FROM users WHERE name LIKE ?", (f"%{name}%",))
    user = cursor.fetchone()
    if user:
        user_id = user[0]
        print(f"Resetting YÖK ID for user {user_id} ({name})...")
        cursor.execute("UPDATE user_profiles SET yok_id = NULL WHERE user_id = ?", (user_id,))
        conn.commit()
        print("Done.")
    else:
        print(f"User {name} not found.")
    conn.close()

if __name__ == "__main__":
    reset_yok_id("Cengiz Beşikçi")
