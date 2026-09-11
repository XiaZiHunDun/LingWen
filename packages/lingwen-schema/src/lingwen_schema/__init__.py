"""lingwen-schema — canonical schema package.

Phase 50 P3-ARCHDEBT: relocated from infra/schema.py (369 LOC).
TRUE LEAF (1 workspace dep: lingwen-errors).
"""

from __future__ import annotations

from lingwen_schema.service import (
    Array,
    BaseModel,  # re-exported for convenience (used by consumers)
    Boolean,
    Integer,
    NonNegativeInt,
    Number,
    OptionalSchema,
    PositiveInt,
    SchemaDecodeError,
    SchemaEncodeError,
    SchemaValidationError,
    String,
    Struct,
    decode,
    encode,
    optional,
    to_json_schema,
    validate,
)

# Note: BaseModel is re-exported from pydantic (in service.py) for consumer convenience.
# Consumers can do `from lingwen_schema import BaseModel, Field` etc.

__all__ = [
    # Exception classes
    "SchemaValidationError",
    "SchemaDecodeError",
    "SchemaEncodeError",
    # Model classes
    "Struct",
    "Array",
    "String",
    "Number",
    "Integer",
    "Boolean",
    "OptionalSchema",
    "PositiveInt",
    "NonNegativeInt",
    # Helper
    "optional",
    # Functions
    "decode",
    "encode",
    "validate",
    "to_json_schema",
]