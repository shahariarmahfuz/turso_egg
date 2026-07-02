import sqlite3

def upgrade():
    conn = sqlite3.connect('instance/database.db')
    c = conn.cursor()
    columns = [
        "ALTER TABLE admin ADD COLUMN email VARCHAR(150)",
        "ALTER TABLE admin ADD COLUMN phone VARCHAR(50)",
        "ALTER TABLE admin ADD COLUMN role VARCHAR(50) DEFAULT 'Admin'",
        "ALTER TABLE admin ADD COLUMN status VARCHAR(50) DEFAULT 'Active'",
        "ALTER TABLE admin ADD COLUMN created_at DATETIME",
        "ALTER TABLE admin ADD COLUMN updated_at DATETIME"
    ]
    for col in columns:
        try:
            c.execute(col)
        except Exception as e:
            print("Error for:", col, e)
    
    try:
        c.execute("UPDATE admin SET role='Admin', status='Active', name='System Admin'")
        conn.commit()
        print("Upgrade successful")
    except Exception as e:
        print("Update Error:", e)
    finally:
        conn.close()

if __name__ == '__main__':
    upgrade()
