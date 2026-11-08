
from datetime import date
from enum import Enum
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class VehicleClass(str, Enum):
    PRIVATE_CAR = "private_car"
    TWO_WHEELER = "two_wheeler"
    COMMERCIAL = "commercial"


class Channel(str, Enum):
    APP = "app"
    WEB = "web"
    CALL_CENTRE = "call_centre"


class FNOLRequest(BaseModel):
    """Validated First Notice of Loss submission."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    policy_number: str = Field(min_length=8, max_length=30)
    policy_start: date
    policy_end: date
    date_of_loss: date
    date_reported: date

    vehicle_registration: str
    vehicle_class: VehicleClass

    channel: Channel

    estimated_loss_inr: float = Field(ge=0, le=5_000_000)

    injuries_reported: bool
    third_party_involved: bool
    third_party_details: str | None = None

    theft_reported: bool
    fir_number: str | None = None

    cashless_garage: bool

    location: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20, max_length=5000)

    @field_validator("policy_number")
    @classmethod
    def validate_policy_number(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Z0-9/-]{8,30}", value):
            raise ValueError("Invalid policy number format")
        return value

    @field_validator("vehicle_registration")
    @classmethod
    def validate_vehicle_registration(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Z]{2}\d{1,2}[A-Z]{0,3}\d{4}", value):
            raise ValueError("Invalid Indian vehicle registration number")
        return value

    @model_validator(mode="after")
    def validate_dates_and_details(self):
        if self.policy_start >= self.policy_end:
            raise ValueError("Policy start must be before policy end")

        if not self.policy_start <= self.date_of_loss <= self.policy_end:
            raise ValueError("Date of loss must fall within the policy period")

        if self.date_of_loss > date.today():
            raise ValueError("Date of loss cannot be in the future")

        if self.date_reported < self.date_of_loss:
            raise ValueError("Date reported cannot be before date of loss")

        if self.third_party_involved and not self.third_party_details:
            raise ValueError(
                "Third-party details are required when third party is involved"
            )

        if self.theft_reported and not self.fir_number:
            raise ValueError("FIR number is required when theft is reported")

        return self
