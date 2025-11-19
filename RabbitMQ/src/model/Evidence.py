from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timezone
import uuid

@dataclass
class Evidence:
    Id: str = field(default_factory=lambda: str(uuid.uuid4()))
    SourceId: str = ""
    SourceName: str = ""
    ChunkId: str = ""
    Text: str = ""
    Page: int = 0
    Confidence: float = 0.0
    CreatedAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    Language: str = "ENG"
    SourceLanguage: str = "ENG"
    HierarchyPath: str = ""
    Concepts: List[str] = field(default_factory=list)
    KeyClaims: List[str] = field(default_factory=list)
    QuestionsRaised: List[str] = field(default_factory=list)
    EvidenceStrength: float = 0.0

    # Position tracking fields
    StartPos: int = 0  # Character position where text starts in original document
    EndPos: int = 0    # Character position where text ends in original document
    ChunkIndex: int = 0  # Sequential chunk number
    HasMore: bool = False  # Whether there are more chunks after this one
    OverlapLength: int = 0  # Length of overlap with previous chunk
