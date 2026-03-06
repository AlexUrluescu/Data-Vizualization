
import sqlite3, hashlib

new_password = "sibiu2026"
new_hash = hashlib.sha256(new_password.encode()).hexdigest()

conn = sqlite3.connect("air_quality.db")
conn.execute("UPDATE users SET password_hash=? WHERE username='admin'", (new_hash,))
conn.commit()
conn.close()
print("✓ Parola resetată.")