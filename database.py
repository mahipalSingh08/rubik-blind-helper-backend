import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

import re

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    print("[DB Warning] MONGO_URI environment variable is NOT set! Falling back to mongodb://localhost:27017")
    MONGO_URI = "mongodb://localhost:27017"
else:
    masked_uri = re.sub(r':([^@]+)@', ':****@', MONGO_URI)
    print(f"[DB Info] Using MONGO_URI: {masked_uri}")

DB_NAME = os.getenv("DB_NAME", "algorithem")

# Set 5-second connection timeout and use certifi CA certificates for TLS
client_kwargs = {
    "serverSelectionTimeoutMS": 5000,
}
if "mongodb+srv" in MONGO_URI or "ssl=true" in MONGO_URI.lower() or "tls=true" in MONGO_URI.lower():
    import certifi
    client_kwargs["tlsCAFile"] = certifi.where()

client = MongoClient(MONGO_URI, **client_kwargs)
db = client[DB_NAME]

edge5_col = db["edge5"]
corner5_col = db["corner5"]

def init_indexes():
    """Ensure indexes on sequence, moves, and letters for fast search and O(1) lookups."""
    try:
        print(f"[DB Startup] Verifying connection to MongoDB Atlas...")
        client.admin.command('ping')
        print(f"[DB Startup] Ping successful! Initializing indexes on '{DB_NAME}'...")
        edge5_col.create_index([("sequence", ASCENDING)], unique=True)
        edge5_col.create_index([("moves", ASCENDING)])
        edge5_col.create_index([("letters", ASCENDING)])

        corner5_col.create_index([("sequence", ASCENDING)], unique=True)
        corner5_col.create_index([("moves", ASCENDING)])
        corner5_col.create_index([("letters", ASCENDING)])
        print(f"[DB Startup] All indexes initialized successfully on database: {DB_NAME}")
    except Exception as e:
        print(f"[DB Startup ERROR] Could not connect to MongoDB: {e}")
        print("[DB Startup HINT] Ensure 0.0.0.0/0 is whitelisted in MongoDB Atlas Network Access and MONGO_URI is set in Render Environment.")
