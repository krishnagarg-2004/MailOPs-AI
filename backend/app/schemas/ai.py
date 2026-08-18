from datetime import datetime
from enum import Enum
import uuid
from pydantic import BaseModel, ConfigDict, Field


class IntentEnum(str, Enum):
    WORK_REQUEST = "WORK_REQUEST"
    STATUS_UPDATE = "STATUS_UPDATE"
    FINANCIAL_INVOICE = "FINANCIAL_INVOICE"
    CONTRACT_LEGAL = "CONTRACT_LEGAL"
    URGENT_ACTION = "URGENT_ACTION"
    INFORMATIONAL = "INFORMATIONAL"
    OTHER = "OTHER"


class PriorityEnum(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class SentimentEnum(str, Enum):
    POSITIVE = "POSITIVE"
    NEUTRAL = "NEUTRAL"
    NEGATIVE = "NEGATIVE"


class ItemTypeEnum(str, Enum):
    ACTION = "ACTION"
    DECISION = "DECISION"
    RISK = "RISK"


class ActionStatusEnum(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"
    COMPLETED = "COMPLETED"


class ExtractedActionSchema(BaseModel):
    description: str = Field(description="Clear, actionable summary of the task")
    assignee: str | None = Field(default=None, description="Owner or recipient assigned to the task")
    due_date: str | None = Field(default=None, description="ISO timestamp or date string of explicit deadline if present")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM, description="Task urgency level")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Model confidence score for this extraction")
    evidence_snippet: str = Field(default="", description="Verbatim text excerpt from the email supporting this action")


class ExtractedDecisionSchema(BaseModel):
    description: str = Field(description="Summary of decision made")
    made_by: str | None = Field(default=None, description="Person or entity who made the decision")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Model confidence score")
    evidence_snippet: str = Field(default="", description="Verbatim text excerpt from the email supporting this decision")


class ExtractedRiskSchema(BaseModel):
    description: str = Field(description="Description of potential risk or obligation flag")
    severity: PriorityEnum = Field(default=PriorityEnum.MEDIUM, description="Severity level of the risk")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Model confidence score")
    evidence_snippet: str = Field(default="", description="Verbatim text excerpt from the email supporting this risk flag")


class EmailExtractionResult(BaseModel):
    """Pydantic structured output model enforced during LLM generation."""
    summary: str = Field(description="Concise 1-2 sentence executive summary of the message")
    intent: IntentEnum = Field(default=IntentEnum.INFORMATIONAL, description="Primary intent of the communication")
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM, description="Overall message priority score")
    sentiment: SentimentEnum = Field(default=SentimentEnum.NEUTRAL, description="Overall message sentiment rating")
    confidence_score: float = Field(default=1.0, ge=0.0, le=1.0, description="Overall confidence score for the analysis")
    rationale: str = Field(description="Short user-facing explanation grounded in email evidence (no chain-of-thought)")
    actions: list[ExtractedActionSchema] = Field(default_factory=list, description="Extracted action items / tasks")
    decisions: list[ExtractedDecisionSchema] = Field(default_factory=list, description="Extracted decisions")
    risks: list[ExtractedRiskSchema] = Field(default_factory=list, description="Extracted operational or financial risks")


# API Request/Response Schemas

class ExtractedActionRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    ai_analysis_id: uuid.UUID
    email_message_id: uuid.UUID | None = None
    email_thread_id: uuid.UUID | None = None
    item_type: ItemTypeEnum
    description: str
    assignee: str | None = None
    due_date: datetime | None = None
    severity_or_priority: PriorityEnum
    confidence_score: float
    evidence_snippet: str
    is_evidence_valid: bool
    status: ActionStatusEnum
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIAnalysisRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    email_message_id: uuid.UUID | None = None
    email_thread_id: uuid.UUID | None = None
    summary: str
    intent: IntentEnum
    priority: PriorityEnum
    sentiment: SentimentEnum
    confidence_score: float
    rationale: str
    model_name: str
    prompt_version: str
    status: str
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime
    extracted_items: list[ExtractedActionRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ActionStatusUpdate(BaseModel):
    status: ActionStatusEnum
    assignee: str | None = None
    due_date: datetime | None = None
