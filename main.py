import os
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Load local .env file if running locally
load_dotenv()

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from database import edge5_col, corner5_col, init_indexes, client
from models import (
    FiveStyleAlgItem, 
    FiveStyleAlgUpdate, 
    SearchResponse,
    PairItem, 
    PairsResponse, 
    AlgListResponse
)

app = FastAPI(
    title="Rubik Blind 5-Style Backend",
    description="High-performance backend for 194,760+ 5-Style Blindfold Commutators powered by MongoDB Atlas",
    version="1.0.0"
)

# Enable CORS for Angular frontend / clients
default_origins = "http://localhost:4200,http://127.0.0.1:4200,https://rubik-blind-helper.vercel.app"
raw_origins = os.getenv("CORS_ORIGINS", default_origins)
if raw_origins.strip() == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip().rstrip("/") for origin in raw_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_origin_regex=r"https://rubik-blind-helper.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for ultra-fast pair queries
# Format: { "piece_type:letter": [ {"pair": "AB", "total": 180, "moves_breakdown": {17: 79, ...}}, ... ] }
_pairs_cache: Dict[str, List[dict]] = {}

CORNER_STARTING_LETTERS = ['A', 'B', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']
EDGE_STARTING_LETTERS = ['A', 'B', 'D', 'E', 'F', 'G', 'H', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X']

@app.on_event("startup")
def startup_db():
    init_indexes()

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "Rubik Blind 5-Style Backend",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    try:
        client.admin.command('ping')
        edges_count = edge5_col.count_documents({})
        corners_count = corner5_col.count_documents({})
        return {
            "status": "healthy",
            "database": "connected",
            "counts": {
                "edges": edges_count,
                "corners": corners_count,
                "total": edges_count + corners_count
            }
        }
    except Exception as e:
        return {
            "status": "degraded",
            "database": "disconnected",
            "error": str(e)
        }

def _get_collection(piece_type: str):
    t = piece_type.lower()
    if t in ("edge", "edges"):
        return edge5_col
    elif t in ("corner", "corners"):
        return corner5_col
    raise HTTPException(status_code=400, detail=f"Invalid piece_type '{piece_type}'. Must be 'edges' or 'corners'.")

@app.get("/api/5style/{piece_type}/letters")
def get_letters(piece_type: str):
    t = piece_type.lower()
    if t in ("corner", "corners"):
        return {"piece_type": "corners", "letters": CORNER_STARTING_LETTERS}
    elif t in ("edge", "edges"):
        return {"piece_type": "edges", "letters": EDGE_STARTING_LETTERS}
    raise HTTPException(status_code=400, detail="Invalid piece_type")

@app.get("/api/5style/{piece_type}/pairs", response_model=PairsResponse)
def get_pairs_for_letter(
    piece_type: str,
    letter: str = Query(..., min_length=1, max_length=1, description="Single letter, e.g. 'A'"),
    moves: Optional[str] = Query(None, description="Comma-separated moves e.g. '4', '4,5', '8', '8,9'")
):
    col = _get_collection(piece_type)
    let = letter.strip().upper()
    cache_key = f"{piece_type.lower()}:{let}"

    if cache_key not in _pairs_cache:
        # Load from Atlas and cache breakdown
        cursor = col.find({"sequence": {"$regex": f"^{let}"}}, {"sequence": 1, "moves": 1, "_id": 0})
        pairs_dict: Dict[str, dict] = {}
        for d in cursor:
            p = d["sequence"][:2]
            m = d.get("moves", 0)
            if p not in pairs_dict:
                pairs_dict[p] = {"pair": p, "total": 0, "moves_breakdown": {}}
            pairs_dict[p]["total"] += 1
            pairs_dict[p]["moves_breakdown"][m] = pairs_dict[p]["moves_breakdown"].get(m, 0) + 1
        
        # Sort by pair alphabetical
        _pairs_cache[cache_key] = [pairs_dict[k] for k in sorted(pairs_dict.keys())]

    cached_list = _pairs_cache[cache_key]

    # Filter by moves if specified
    filtered_pairs: List[PairItem] = []
    move_list = []
    if moves and moves.lower() != "all":
        try:
            move_list = [int(m.strip()) for m in moves.split(",") if m.strip()]
        except ValueError:
            move_list = []

    for item in cached_list:
        if move_list:
            count = sum(item["moves_breakdown"].get(m, 0) for m in move_list)
            if count > 0:
                filtered_pairs.append(PairItem(pair=item["pair"], count=count))
        else:
            filtered_pairs.append(PairItem(pair=item["pair"], count=item["total"]))

    return PairsResponse(
        piece_type=piece_type,
        letter=let,
        total_pairs=len(filtered_pairs),
        pairs=filtered_pairs
    )

@app.get("/api/5style/{piece_type}/by-pair", response_model=AlgListResponse)
def get_algorithms_by_pair(
    piece_type: str,
    pair: str = Query(..., min_length=2, max_length=2, description="2-letter pair prefix, e.g. 'AB'"),
    moves: Optional[str] = Query(None, description="Comma-separated moves e.g. '4', '4,5', '8', '8,9'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500)
):
    col = _get_collection(piece_type)
    prefix = pair.strip().upper()
    query: dict = {"sequence": {"$regex": f"^{prefix}"}}

    if moves and moves.lower() != "all":
        try:
            move_list = [int(m.strip()) for m in moves.split(",") if m.strip()]
            if move_list:
                query["moves"] = {"$in": move_list}
        except ValueError:
            pass

    total = col.count_documents(query)
    skip = (page - 1) * page_size
    cursor = col.find(query, {"_id": 0}).sort("moves", 1).skip(skip).limit(page_size)
    items = list(cursor)

    return AlgListResponse(
        piece_type=piece_type,
        pair=prefix,
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )

@app.get("/api/5style/{piece_type}/{sequence}", response_model=FiveStyleAlgItem)
def get_algorithm(piece_type: str, sequence: str):
    col = _get_collection(piece_type)
    seq = sequence.strip().upper()
    doc = col.find_one({"sequence": seq}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Algorithm not found for sequence '{seq}' in {piece_type}")
    return doc

@app.get("/api/5style/search", response_model=SearchResponse)
def search_algorithms(
    piece_type: str = Query("corners", description="'edges' or 'corners'"),
    query: Optional[str] = Query(None, description="Search sequence e.g. 'AB', 'ABDG'"),
    letter: Optional[str] = Query(None, description="Filter sequences containing this letter"),
    moves: Optional[str] = Query(None, description="Comma-separated moves e.g. '4', '4,5', '8', '8,9'"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500)
):
    col = _get_collection(piece_type)
    db_query: dict = {}

    if query:
        q = query.strip().upper()
        if len(q) == 4:
            db_query["sequence"] = q
        else:
            db_query["sequence"] = {"$regex": f"^{q}"}
    elif letter:
        db_query["letters"] = letter.strip().upper()

    if moves and moves.lower() != "all":
        try:
            move_list = [int(m.strip()) for m in moves.split(",") if m.strip()]
            if move_list:
                db_query["moves"] = {"$in": move_list}
        except ValueError:
            pass

    total = col.count_documents(db_query)
    skip = (page - 1) * page_size
    cursor = col.find(db_query, {"_id": 0}).sort("moves", 1).skip(skip).limit(page_size)
    items = list(cursor)

    return SearchResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )

@app.put("/api/5style/{piece_type}/{sequence}")
def update_algorithm(piece_type: str, sequence: str, update_data: FiveStyleAlgUpdate):
    col = _get_collection(piece_type)
    seq = sequence.strip().upper()

    update_fields = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update.")

    result = col.update_one({"sequence": seq}, {"$set": update_fields})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Sequence '{seq}' not found.")

    return {"message": f"Sequence '{seq}' updated successfully."}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)

