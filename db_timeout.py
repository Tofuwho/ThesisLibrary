
import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

# Set a short timeout
try:
    print("Connecting with timeout...")
    db = MySQLdb.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", ""),
        db=os.getenv("DB_NAME", "thesis_library"),
        port=int(os.getenv("DB_PORT", 3306)),
        connect_timeout=5
    )
    print("Connected!")
    db.close()
except Exception as e:
    print(f"Connection failed: {e}")
