from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from datetime import datetime, timezone
import uuid
from .Evidence import Evidence
from .GapSuggestion import GapSuggestion

@dataclass
class KnowledgeNode:
    Id: str = field(default_factory=lambda: str(uuid.uuid4()))
    Type: str = ""
    Name: str = ""
    Synthesis: str = ""
    WorkspaceId: str = ""
    Level: int = 0
    SourceCount: int = 0
    TotalConfidence: float = 0.0
    CreatedAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    UpdatedAt: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    Children: List[KnowledgeNode] = field(default_factory=list)
    Evidences: List[Evidence] = field(default_factory=list)
    GapSuggestions: List[GapSuggestion] = field(default_factory=list)  

    def is_leaf_node(self) -> bool:
        return len(self.Children) == 0