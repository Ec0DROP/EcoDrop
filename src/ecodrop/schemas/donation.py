"""Request and response models for donations."""

from datetime import datetime

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from ecodrop.domain.donation import DonationStatus, Unit

MAX_NAME_LENGTH = 200
MAX_ADDRESS_LENGTH = 300


class DonationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    donor_name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH, examples=["Green Market"])
    food_name: str = Field(min_length=1, max_length=MAX_NAME_LENGTH, examples=["Wholegrain bread"])
    quantity: float = Field(gt=0, examples=[12.5])
    unit: Unit = Field(examples=[Unit.KILOGRAM])
    expires_at: AwareDatetime = Field(
        description="ISO 8601 with timezone; must be in the future.",
        examples=["2026-12-01T18:00:00Z"],
    )
    pickup_address: str = Field(
        min_length=1, max_length=MAX_ADDRESS_LENGTH, examples=["ul. Lucerny 15, Warszawa"]
    )


class DonationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    donor_name: str
    food_name: str
    quantity: float
    unit: Unit
    expires_at: datetime
    pickup_address: str
    status: DonationStatus
    created_at: datetime
