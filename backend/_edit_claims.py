"""Reliable edit: claims INSERT placeholders = 15, add user_id value (no manual typo risk)."""
import re
from pathlib import Path

path = Path(r"c:\Users\user\OneDrive\Documents\Desktop\PMFBY\backend\main.py")
text = path.read_text(encoding="utf-8")

# 1) Rewrite the VALUES placeholder row inside the claims INSERT to exactly 15 placeholders.
pattern = re.compile(r"\) VALUES \([?,\s]*\)\n", re.MULTILINE)
placeholder_row = ") VALUES (" + ", ".join(["?"] * 15) + ")\n"
new_text, count = pattern.subn(placeholder_row, text, count=1)
assert count == 1, f"VALUES row replacements: {count}"
text = new_text

# 2) Insert user["id"], right after claim_id,
old_id = '            claim_id,\n            crop,\n'
new_id = '            claim_id,\n            user["id"],\n            crop,\n'
assert old_id in text, "claim_id anchor not found"
text = text.replace(old_id, new_id, 1)

path.write_text(text, encoding="utf-8")
print("OK: claims INSERT = 15 placeholders + user_id value")
