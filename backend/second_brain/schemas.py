from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    StrictBool,
    StrictInt,
    model_validator,
)

Importance = Literal["very_low", "low", "medium", "high", "very_high"]
Status = Literal["pending", "in_progress", "completed"]
TimeHorizon = Literal["short_term", "long_term"]
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


class Handoff(Input):
    handler: Literal["muse", "user"]
    reason: Annotated[str, Field(min_length=1, max_length=1000)]
    requirements: Annotated[
        list[Annotated[str, Field(min_length=1, max_length=500)]], Field(max_length=10)
    ]
    done_when: Annotated[str, Field(min_length=1, max_length=2000)]


class HandoffAssessmentRequest(Input):
    request_id: UUID
    task_ids: Annotated[list[UUID], Field(min_length=1, max_length=20)]


class AssessedSubtask(Input):
    task_id: UUID
    handoff: Handoff


class HandoffAssessment(Input):
    tasks: Annotated[list[AssessedSubtask], Field(min_length=1, max_length=20)]


class ManualSubtask(Input):
    title: Title


class TaskCreate(Input):
    title: Title
    description: Text = ""
    deadline: date | None = None
    parent_task_id: UUID | None = None
    user_importance_level: Importance | None = None
    handoff: Handoff | None = None
    time_horizon: TimeHorizon | None = None
    subtasks: Annotated[list[ManualSubtask], Field(max_length=20)] = Field(
        default_factory=list
    )

    @model_validator(mode="after")
    def manual_subtasks_belong_to_roots(self):
        if self.subtasks and self.parent_task_id is not None:
            raise ValueError("A batch of subtasks can be added with a root task only")
        return self


class TaskEdit(Input):
    expected_version: Annotated[StrictInt, Field(ge=1)]
    title: Title | None = None
    description: Text | None = None
    deadline: date | None = None
    user_importance_level: Importance | None = None
    status: Status | None = None
    handoff: Handoff | None = None
    time_horizon: TimeHorizon | None = None

    @model_validator(mode="after")
    def required_fields_not_null(self):
        for key in ("title", "description", "status"):
            if key in self.model_fields_set and getattr(self, key) is None:
                raise ValueError(f"{key} cannot be null")
        return self


class TaskTrash(Input):
    request_id: UUID
    expected_version: Annotated[StrictInt, Field(ge=1)]


class TaskRestore(Input):
    deletion_id: UUID


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
    # Null supports old saved proposals. New model output must classify every step.
    handoff: Handoff | None = None


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
    handoff: Handoff | None = None
    # Null preserves an existing focus choice; older stored proposals omit it.
    time_horizon: TimeHorizon | None = None


class ConversationProposal(Input):
    reply: Annotated[str, Field(min_length=1, max_length=10000)]
    tasks: Annotated[list[ConversationTask], Field(max_length=10)]
    # An unambiguous existing task being discussed, including answers with no edits.
    chat_task_id: UUID | None = None
    web_search_used: StrictBool = False
    sources: Annotated[list[WebSource], Field(max_length=10)] = Field(
        default_factory=list
    )


class WebSource(Input):
    url: Annotated[str, Field(min_length=1, max_length=2000)]
    title: Annotated[str, Field(max_length=300)]


class ConversationApproval(Input):
    proposal: ConversationProposal | None = None


class ConversationRequest(PlanRequest):
    message: Annotated[str, Field(max_length=10000)]
    attachment_ids: Annotated[list[UUID], Field(max_length=5)] = Field(
        default_factory=list
    )
    conversation_id: UUID | None = None
    chat_task_id: UUID | None = None
    review_draft: ConversationProposal | None = None
    # The dashboard saves directly. False preserves existing review-mode API clients.
    apply_immediately: StrictBool = False
    keep_chat_scope: StrictBool = False
    web_enabled: StrictBool = False
    delegated_task_id: UUID | None = None

    @model_validator(mode="after")
    def message_or_attachment(self):
        if not self.message and not self.attachment_ids:
            raise ValueError("Add a message or an attachment")
        if len(set(self.attachment_ids)) != len(self.attachment_ids):
            raise ValueError("Attach each file once")
        return self
