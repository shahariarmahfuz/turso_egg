import os
from sqlalchemy import create_engine, MetaData, insert, select, delete
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load Postgres URI
load_dotenv()
pg_url = os.environ.get('DATABASE_URL')
# For SQLAlchemy, postgresql:// is fine, but sometimes postgresql+psycopg2:// is needed. We will try what is provided.
if pg_url and pg_url.startswith("postgres://"):
    pg_url = pg_url.replace("postgres://", "postgresql://", 1)

# 1. Connect to PostgreSQL and create tables
from app import create_app
from models import db
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = pg_url

# We will init app but NOT run it.
# Wait, app.py has `db.init_app(app)` in `create_app()`.
# And `db.create_all()` inside `app_context()`.
# Let's override app config directly.
with app.app_context():
    app.config['SQLALCHEMY_DATABASE_URI'] = pg_url
    db.create_all()

# 2. Setup engines
sqlite_engine = create_engine('sqlite:///instance/database.db')
pg_engine = create_engine(pg_url)

sqlite_meta = MetaData()
sqlite_meta.reflect(bind=sqlite_engine)

pg_meta = MetaData()
pg_meta.reflect(bind=pg_engine)

# 3. Migrate Data
print("Migrating data...")
for table in sqlite_meta.sorted_tables:
    print(f"Migrating table: {table.name}")
    
    pg_table = pg_meta.tables.get(table.name)
    if pg_table is None:
        print(f"Skipping {table.name}, not found in Postgres.")
        continue

    # Clear table in postgres first
    with pg_engine.begin() as pg_conn:
        pg_conn.execute(delete(pg_table))
    
    # Fetch all from sqlite
    with sqlite_engine.connect() as sqlite_conn:
        records = sqlite_conn.execute(select(table)).fetchall()
        
        if records:
            # Insert into pg
            # convert rows to list of dicts. In SQLAlchemy 2.0, row._mapping is a dict-like object
            records_dicts = [dict(row._mapping) for row in records]
            with pg_engine.begin() as pg_conn:
                pg_conn.execute(insert(pg_table), records_dicts)

print("Migration completed successfully!")
