from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict, Literal, Tuple

class ReasonSchema(BaseModel):
    code: str
    message: str
    observed: Optional[float | str] = None
    threshold: Optional[float | str] = None
    unit: Optional[str] = None
    context: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

class MetricValueSchema(BaseModel):
    name: str
    value: Optional[float] = None
    unit: str
    direction: Literal["max", "min"]
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class OpportunityDecisionTraceSchema(BaseModel):
    candidate_id: str
    accepted: bool
    reasons: Tuple[ReasonSchema, ...]
    metrics: Tuple[MetricValueSchema, ...]
    pareto: Dict[str, int | bool | None]
    tie_break_key: str
    schema_version: Literal["v2-d.1"]

    model_config = ConfigDict(from_attributes=True)
