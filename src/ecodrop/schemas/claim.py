"""Request and response models for claims."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ecodrop.schemas.donation import MAX_NAME_LENGTH


class ClaimCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    donation_id: int = Field(gt=0, examples=[1])
    food_bank_name: str = Field(
        min_length=1, max_length=MAX_NAME_LENGTH, examples=["Bank Żywności Wawer"]
    )


class ClaimRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donation_id: int
    food_bank_name: str
    claimed_at: datetime
