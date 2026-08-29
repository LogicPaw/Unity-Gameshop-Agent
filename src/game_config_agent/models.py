"""Domain data structures shared by extraction, validation, and export."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, StrictBool, StrictInt


class CandidateOffer(BaseModel):
    """A possibly incomplete offer extracted from a user's requirement."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    item_name: str | None = None
    reward_amount: StrictInt | None = None
    currency_name: str | None = None
    cost_amount: StrictInt | None = None
    display_name: str | None = None
    category: str | None = None
    badge_text: str | None = None
    enabled: StrictBool | None = None


class CandidateOfferBatch(BaseModel):
    """Structured extraction result returned by the language model."""

    model_config = ConfigDict(extra="forbid")

    offers: list[CandidateOffer] = Field(min_length=1)


class ShopOffer(BaseModel):
    """A fully resolved offer that is safe to pass to the CSV exporter."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    offer_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    display_name: str = Field(min_length=1)
    category: Literal["Items", "Currencies"]
    reward_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    reward_amount: PositiveInt
    cost_id: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    cost_amount: PositiveInt
    badge_text: str = ""
    enabled: bool = True


class ResourceDefinition(BaseModel):
    """A resource loaded from the pinned Unity official snapshot."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    id: str = Field(pattern=r"^[A-Z][A-Z0-9_]*$")
    resource_type: Literal["Currency", "Inventory Item"]
    name: str = Field(min_length=1)
    max: int | None = None
    sprite_address: str | None = None
    source_path: str | None = None


class ValidationIssue(BaseModel):
    """A machine-readable problem that blocks formal CSV export."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    offer_index: int = Field(ge=0)
    code: str
    field: str
    message: str


class DefaultApplied(BaseModel):
    """Records a default so the agent can disclose it to the user."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    offer_index: int = Field(ge=0)
    field: str
    value: str | int | bool
    reason: str


class BuildResult(BaseModel):
    """Result of resolving and validating a batch of candidate offers."""

    model_config = ConfigDict(extra="forbid")

    offers: list[ShopOffer] = Field(default_factory=list)
    issues: list[ValidationIssue] = Field(default_factory=list)
    defaults_applied: list[DefaultApplied] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.issues
