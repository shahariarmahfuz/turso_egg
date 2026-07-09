import sqlite3

def add_columns():
    conn = sqlite3.connect('instance/database.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE customer_collections ADD COLUMN updated_by INTEGER;")
        print("Added updated_by")
    except sqlite3.OperationalError as e:
        print(f"Skipped updated_by: {e}")
        
    try:
        cursor.execute("ALTER TABLE customer_collections ADD COLUMN updated_at DATETIME;")
        print("Added updated_at")
    except sqlite3.OperationalError as e:
        print(f"Skipped updated_at: {e}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_columns()
