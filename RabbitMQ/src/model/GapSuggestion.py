from dataclasses import dataclass, field
import uuid

@dataclass
class GapSuggestion:
    Id: str = field(default_factory=lambda: str(uuid.uuid4()))
    SuggestionText: str = ""
    TargetNodeId: str = ""
    TargetFileId: str = ""
    SimilarityScore: float = 0.0
