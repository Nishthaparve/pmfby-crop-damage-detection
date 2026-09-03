# File: backend/_verify_db.py
import sqlite3

conn = sqlite3.connect("backend/claims.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
print("Tables:", [r[0] for r in cur.fetchall()])
for table in ("users", "password_reset_tokens", "claims"):
    cur.execute("PRAGMA table_info(%s)" % table)
    cols = [(r[1], r[2]) for r in cur.fetchall()]
    print(table, "->", ", ".join("%s %s" % c for c in cols))
conn.close()
