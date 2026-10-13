import json
import os
import sys
from pymongo import UpdateOne
from database import edge5_col, corner5_col, init_indexes

EDGE_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "blind", "src", "app", "shared", "edge5.json"))
CORNER_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "blind", "src", "app", "shared", "corner5.json"))

def seed_collection(json_path: str, collection, name: str, batch_size: int = 2500):
    if not os.path.exists(json_path):
        print(f"[ERROR] File not found: {json_path}")
        return

    existing_count = collection.count_documents({})
    print(f"\nTarget: {name} | Existing documents in Atlas: {existing_count:,}")

    print(f"Reading JSON from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    print(f"Total entries in source: {total:,}")

    if existing_count >= total:
        print(f"[INFO] {name} is already fully seeded ({existing_count:,} docs). Skipping.")
        return

    # If collection is empty, insert_many is much faster over Atlas network
    is_empty = (existing_count == 0)
    batch = []
    processed = 0

    for seq, item in data.items():
        doc = {
            "sequence": seq,
            "commutator": item.get("commutator", item.get("short", "")),
            "algorithm": item.get("algorithm", ""),
            "moves": item.get("moves", item.get("htm", 0)),
            "basealgo": item.get("basealgo", ""),
            "setupmove": item.get("setupmove", ""),
            "inverse": item.get("inverse", ""),
            "letters": list(seq)
        }

        if is_empty:
            batch.append(doc)
            if len(batch) >= batch_size:
                collection.insert_many(batch, ordered=False)
                processed += len(batch)
                print(f"  Uploaded {processed:,} / {total:,} ({processed*100//total}%)", flush=True)
                batch = []
        else:
            batch.append(UpdateOne({"sequence": seq}, {"$set": doc}, upsert=True))
            if len(batch) >= batch_size:
                collection.bulk_write(batch, ordered=False)
                processed += len(batch)
                print(f"  Upserted {processed:,} / {total:,} ({processed*100//total}%)", flush=True)
                batch = []

    if batch:
        if is_empty:
            collection.insert_many(batch, ordered=False)
        else:
            collection.bulk_write(batch, ordered=False)
        processed += len(batch)
        print(f"  Uploaded {processed:,} / {total:,} (100%)", flush=True)

    final_count = collection.count_documents({})
    print(f"[SUCCESS] {name} collection populated. Count in Atlas DB: {final_count:,}")

def main():
    print("=== Starting 5-Style MongoDB Atlas Seed ===")
    init_indexes()
    seed_collection(CORNER_JSON_PATH, corner5_col, "Corners (corner5)")
    seed_collection(EDGE_JSON_PATH, edge5_col, "Edges (edge5)")
    print("\n=== All 5-style data successfully seeded into MongoDB Atlas! ===")

if __name__ == "__main__":
    main()
