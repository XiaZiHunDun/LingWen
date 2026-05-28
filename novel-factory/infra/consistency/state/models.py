from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field

class LocationState(BaseModel):
    location: str = ""
    inDoor: Optional[bool] = None
    previous_location: Optional[str] = None
    transition_type: Optional[str] = None  # "walked", "teleported", "chased"

class KnowledgeState(BaseModel):
    known_secrets: set[str] = Field(default_factory=set)
    shared_with: dict[str, set[str]] = Field(default_factory=dict)  # {角色: {秘密}}
    forgot_secrets: set[str] = Field(default_factory=set)

class RelationshipState(BaseModel):
    trust_level: float = 0.0       # -1.0 ~ 1.0
    emotional_bond: float = 0.0   # -1.0 ~ 1.0
    status: str = "strangers"     # "strangers", "friends", "enemies", "lovers"
    last_status_change_chapter: int = 0
    status_change_reason: Optional[str] = None

class CapabilityState(BaseModel):
    abilities: set[str] = Field(default_factory=set)
    learning_in_progress: dict[str, str] = Field(default_factory=dict)  # {能力: 进度}
    mastery_level: dict[str, float] = Field(default_factory=dict)  # {能力: 0.0~1.0}

class EntityState(BaseModel):
    entity_id: str
    entity_type: str = "character"  # "character" | "item"
    alive: bool = True

    location: Optional[LocationState] = None
    knowledge: Optional[KnowledgeState] = None

    relationships: dict[str, RelationshipState] = Field(default_factory=dict)
    capabilities: Optional[CapabilityState] = None

    owner: Optional[str] = None
    condition: Optional[str] = None  # "intact", "broken", "destroyed"

    action_history: list[dict] = Field(default_factory=list)

    def apply_action(self, action: str, target: str, chapter: int):
        self.action_history.append({
            "action": action,
            "target": target,
            "chapter": chapter
        })