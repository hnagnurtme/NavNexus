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
