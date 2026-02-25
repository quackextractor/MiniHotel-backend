import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'minihotel.db')
if not os.path.exists(db_path):
    # Try the current directory
    db_path = os.path.join(os.path.dirname(__file__), 'minihotel.db')

print(f"Using DB at: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("ALTER TABLE rooms ADD COLUMN amenities VARCHAR(255) DEFAULT ''")
    conn.commit()
    print("Column 'amenities' added successfully.")
except sqlite3.OperationalError as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
