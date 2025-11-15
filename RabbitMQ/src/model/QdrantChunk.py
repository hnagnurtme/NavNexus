from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
import uuid

@dataclass
class QdrantChunk:
    chunk_id: str
    paper_id: str
    page: int
    text: str
    summary: str
    concepts: List[str]
    topic: str
    workspace_id: str
    language: str
    source_language: str
    created_at: str
    hierarchy_path: str
    chunk_index: int
    prev_chunk_id: str = ""
    next_chunk_id: str = ""
    semantic_similarity_prev: float = 0.0
    overlap_with_prev: str = ""
    key_claims: List[str] = field(default_factory=list)
    questions_raised: List[str] = field(default_factory=list)
    evidence_strength: float = 0.8
