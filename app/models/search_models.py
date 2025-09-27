from __future__ import annotations

from dataclasses import fields as dataclass_fields
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.machine import Machine
from app.models.ticket import Ticket


class FieldConfig:
    """管理票據搜尋允許的欄位配置"""
    
    @staticmethod
    def _build_allowed_fields() -> Tuple[str, ...]:
        ticket_fields = tuple(Ticket.model_fields.keys())
        machine_allowed: Set[str] = {"serial", "ip", "port"}
        machine_fields = tuple(
            f"machine.{field.name}"
            for field in dataclass_fields(Machine)
            if field.name in machine_allowed
        )
        ordered = (*ticket_fields, *machine_fields)
        # remove duplicates while preserving order
        seen: Set[str] = set()
        result: List[str] = []
        for name in ordered:
            if name not in seen:
                seen.add(name)
                result.append(name)
        return tuple(result)
    
    @property
    def allowed_fields(self) -> Tuple[str, ...]:
        return self._build_allowed_fields()
    
    @property
    def date_field_names(self) -> Tuple[str, ...]:
        return tuple(
            field for field in ("enqueued_at", "started_at", "completed_at") 
            if field in Ticket.model_fields
        )


class DateRange(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: Optional[datetime] = Field(default=None, alias="from")
    to: Optional[datetime] = None


class TicketSearchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    active_fields: List[str] = Field(default_factory=list, alias="activeFields")
    field_values: Dict[str, str] = Field(default_factory=dict, alias="fieldValues")
    date_ranges: Dict[str, DateRange] = Field(default_factory=dict, alias="dateRanges")
    result_data: Optional[str] = Field(default=None, alias="resultData")
    raw_data: Optional[str] = Field(default=None, alias="rawData")

    @model_validator(mode="after")
    def validate_fields(self) -> "TicketSearchRequest":
        field_config = FieldConfig()
        allowed_fields = field_config.allowed_fields
        date_field_names = field_config.date_field_names
        
        invalid_active = [field for field in self.active_fields if field not in allowed_fields]
        invalid_values = [field for field in self.field_values if field not in allowed_fields]
        invalid_dates = [field for field in self.date_ranges if field not in date_field_names]

        if invalid_active or invalid_values or invalid_dates:
            detail = {
                "active_fields": invalid_active,
                "field_values": invalid_values,
                "date_ranges": invalid_dates,
            }
            raise ValueError(f"Invalid ticket fields supplied: {detail}")

        return self