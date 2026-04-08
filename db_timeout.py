
import MySQLdb
import os
from dotenv import load_dotenv

load_dotenv()

# Set a short timeout
try:
    print("Connecting with timeout...")
    db = MySQLdb.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWORD"),
        db=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306)),
        connect_timeout=5
    )
    print("Connected!")
    db.close()
except Exception as e:
    print(f"Connection failed: {e}")
