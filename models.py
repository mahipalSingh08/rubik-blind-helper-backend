from typing import Optional, List
from pydantic import BaseModel, Field

class FiveStyleAlgItem(BaseModel):
    sequence: str = Field(..., description="4-letter sequence, e.g. BEWQ")
    commutator: Optional[str] = Field(None, description="Commutator representation, e.g. [M, U]")
    algorithm: str = Field(..., description="Full move algorithm")
    moves: int = Field(..., description="Move count / HTM")
    basealgo: Optional[str] = Field(None, description="Base algorithm ID")
    setupmove: Optional[str] = Field(None, description="Setup moves")
    inverse: Optional[str] = Field(None, description="Inverse sequence")
    letters: Optional[List[str]] = Field(None, description="Individual letters in sequence for filtering")

class FiveStyleAlgUpdate(BaseModel):
    commutator: Optional[str] = None
    algorithm: Optional[str] = None
    moves: Optional[int] = None
    setupmove: Optional[str] = None

class PairItem(BaseModel):
    pair: str
    count: int

class PairsResponse(BaseModel):
    piece_type: str
    letter: str
    total_pairs: int
    pairs: List[PairItem]

class AlgListResponse(BaseModel):
    piece_type: str
    pair: Optional[str] = None
    total: int
    page: int
    page_size: int
    items: List[FiveStyleAlgItem]

class SearchResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[FiveStyleAlgItem]
