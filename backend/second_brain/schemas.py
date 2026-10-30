from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, StrictInt, model_validator

Importance = Literal["very_low", "low", "medium", "high", "very_high"]
Status = Literal["pending", "in_progress", "completed"]
Score = Annotated[StrictInt, Field(ge=0, le=100)]
Title = Annotated[str, Field(min_length=1, max_length=300)]
Text = Annotated[str, Field(max_length=10000)]
RANGES = {
    "very_low": (0, 19),
    "low": (20, 39),
    "medium": (40, 59),
    "high": (60, 79),
    "very_high": (80, 100),
}


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SessionCreate(Input):
    token: Annotated[SecretStr, Field(min_length=1, max_length=4096)]


class TaskCreate(Input):
    title: Title
    description: Text = ""
    deadline: date | None = None
    parent_task_id: UUID | None = None
    user_importance_level: Importance | None = None


class TaskEdit(Input):
    expected_version: Annotated[StrictInt, Field(ge=1)]
    title: Title | None = None
    description: Text | None = None
    deadline: date | None = None
    user_importance_level: Importance | None = None
    status: Status | None = None

    @model_validator(mode="after")
    def required_fields_not_null(self):
        for key in ("title", "description", "status"):
            if key in self.model_fields_set and getattr(self, key) is None:
                raise ValueError(f"{key} cannot be null")
        return self


class ContextEdit(Input):
    expected_version: Annotated[StrictInt, Field(ge=0)]
    category: Literal[
        "about_user",
        "long_term_direction",
        "current_situation",
        "assistance_preferences",
    ]
    content: Annotated[str, Field(min_length=1, max_length=10000)]
    provenance: Literal["user_stated", "user_confirmed"] = "user_stated"


class PlanRequest(Input):
    request_id: UUID
    message: Annotated[str, Field(min_length=1, max_length=10000)]


class SuggestedTask(Input):
    title: Title
    description: Text
    importance_score: Score


class Proposal(Input):
    reply: Annotated[str, Field(min_length=1, max_length=10000)]
    importance_score: Score
    subtasks: Annotated[list[SuggestedTask], Field(max_length=20)]


class Approval(Input):
    # Optional reviewed replacement permits editing before acceptance.
    proposal: Proposal | None = None


class ConversationTask(Input):
    # A null ID proposes a new object; an ID proposes edits to an owned task.
    task_id: UUID | None
    title: Title
    description: Text
    deadline: date | None
    importance_score: Score
    subtasks: Annotated[list[SuggestedTask], Field(max_length=20)]


class ConversationProposal(Input):
    reply: Annotated[str, Field(min_length=1, max_length=10000)]
    tasks: Annotated[list[ConversationTask], Field(max_length=10)]


class ConversationApproval(Input):
    proposal: ConversationProposal | None = None


class ConversationRequest(PlanRequest):
    conversation_id: UUID | None = None
    review_draft: ConversationProposal | None = None
