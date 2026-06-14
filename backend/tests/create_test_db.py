"""Script tạo test database LinguaIELTS_test."""
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    user="postgres",
    password="root",
    dbname="postgres",
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("SELECT 1 FROM pg_database WHERE datname='LinguaIELTS_test'")
exists = cur.fetchone()

if exists:
    print("Database 'LinguaIELTS_test' already exists — skipping CREATE")
else:
    cur.execute('CREATE DATABASE "LinguaIELTS_test"')
    print("Database 'LinguaIELTS_test' created successfully")

conn.close()
print("Done.")
