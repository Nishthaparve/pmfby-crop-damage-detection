"""DB bootstrap: users, password_reset_tokens, legacy claims.user_id column (.py so SoftWrap adds no newlines)."""
from pathlib import Path

BASE_DIR = Path(r"c:\Users\user\OneDrive\Documents\Desktop\PMFBY")
DB_PATH = BASE_DIR / "backend" / "claims.db"

sql_path = BASE_DIR / "backend" / "db_scripts.sql"
sql = sql_path.read_text(encoding="utf-8")

import sqlite3
con = sqlite3.connect(str(DB_PATH))
con.executescript(sql)
con.commit()
print("DB ready. Tables:", [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")])
cols = [r[1] for r in con.execute("PRAGMA table_info(claims)")]
print("claims cols:", cols)
con.close()
