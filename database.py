import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "algorithem")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

edge5_col = db["edge5"]
corner5_col = db["corner5"]

def init_indexes():
    """Ensure indexes on sequence, moves, and letters for fast search and O(1) lookups."""
    try:
        edge5_col.create_index([("sequence", ASCENDING)], unique=True)
        edge5_col.create_index([("moves", ASCENDING)])
        edge5_col.create_index([("letters", ASCENDING)])

        corner5_col.create_index([("sequence", ASCENDING)], unique=True)
        corner5_col.create_index([("moves", ASCENDING)])
        corner5_col.create_index([("letters", ASCENDING)])
        print(f"[DB] Indexes initialized successfully on database: {DB_NAME}")
    except Exception as e:
        print(f"[DB Warning] Could not initialize indexes: {e}")
