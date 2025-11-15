from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
import uuid
from .Evidence import Evidence
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
    CreatedAt: datetime = field(default_factory=datetime.utcnow)
    UpdatedAt: datetime = field(default_factory=datetime.utcnow)
    Children: List[KnowledgeNode] = field(default_factory=list)
    Evidences: List[Evidence] = field(default_factory=list)
    GapSuggestions: List[str] = field(default_factory=list)  # tạm thời string nếu chưa có class GapSuggestion

    def is_leaf_node(self) -> bool:
        return len(self.Children) == 0