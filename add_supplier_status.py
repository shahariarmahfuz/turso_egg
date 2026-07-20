import sqlite3

def add_column():
    conn = sqlite3.connect('/workspaces/turso_egg/instance/database.db')
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE suppliers ADD COLUMN status VARCHAR(20) DEFAULT 'Active'")
        print("Column 'status' added successfully.")
    except sqlite3.OperationalError as e:
        print(f"OperationalError: {e}")
    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_column()
