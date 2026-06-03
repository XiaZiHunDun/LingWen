import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from infra.consistency.state.models import (
    CapabilityState,
    EntityState,
    KnowledgeState,
    LocationState,
    RelationshipState,
)


def test_location_state_creation():
    loc = LocationState(
        location="厨房",
        inDoor=True,
        previous_location="客厅",
        transition_type="walked"
    )
    assert loc.location == "厨房"
    assert loc.inDoor is True
    assert loc.previous_location == "客厅"

def test_entity_state_apply_action():
    entity = EntityState(
        entity_id="林夜",
        entity_type="character",
        alive=True
    )
    entity.apply_action("broke", target="茶杯", chapter=10)
    assert len(entity.action_history) == 1
    assert entity.action_history[0]["action"] == "broke"
    assert entity.action_history[0]["chapter"] == 10

def test_knowledge_state_share_secret():
    knowledge = KnowledgeState(
        known_secrets={"父亲的秘密"},
        shared_with={"林夜": {"父亲的秘密"}}
    )
    assert "父亲的秘密" in knowledge.known_secrets
    assert "林夜" in knowledge.shared_with

def test_relationship_state():
    rs = RelationshipState(
        trust_level=0.8,
        emotional_bond=0.5,
        status="friends",
        last_status_change_chapter=10
    )
    assert rs.trust_level == 0.8
    assert rs.status == "friends"

def test_capability_state():
    cap = CapabilityState(
        abilities={"剑气", "御剑术"},
        mastery_level={"剑气": 0.9, "御剑术": 0.5}
    )
    assert "剑气" in cap.abilities
    assert cap.mastery_level["剑气"] == 0.9
