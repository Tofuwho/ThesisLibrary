import sys
import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

# Set a short timeout
try:
    db = MySQLdb.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        passwd=os.getenv("DB_PASSWORD", ""),
        db=os.getenv("DB_NAME", "thesis_library"),
        port=int(os.getenv("DB_PORT", 3306)),
        connect_timeout=3
    )
    db.close()
    sys.exit(0)
except Exception as e:
    print(f"Database connection failed: {e}", file=sys.stderr)
    sys.exit(1)
