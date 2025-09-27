from __future__ import annotations

from dataclasses import fields as dataclass_fields
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from app.models.machine import Machine
from app.models.ticket import Ticket
from app.services.ticket_manager import TicketManager


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


ALLOWED_FIELDS = _build_allowed_fields()
DATE_FIELD_NAMES = tuple(
    field for field in ("enqueued_at", "started_at", "completed_at") if field in Ticket.model_fields
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
        invalid_active = [field for field in self.active_fields if field not in ALLOWED_FIELDS]
        invalid_values = [field for field in self.field_values if field not in ALLOWED_FIELDS]
        invalid_dates = [field for field in self.date_ranges if field not in DATE_FIELD_NAMES]

        if invalid_active or invalid_values or invalid_dates:
            detail = {
                "active_fields": invalid_active,
                "field_values": invalid_values,
                "date_ranges": invalid_dates,
            }
            raise ValueError(f"Invalid ticket fields supplied: {detail}")

        return self


def _build_ticket_model(ticket_data: dict) -> Optional[Ticket]:
    payload = {key: ticket_data.get(key) for key in Ticket.model_fields}
    machine_data = ticket_data.get("machine")
    if isinstance(machine_data, dict):
        try:
            payload["machine"] = Machine(
                vendor=machine_data.get("vendor") or ticket_data.get("vendor", ""),
                model=machine_data.get("model") or ticket_data.get("model", ""),
                version=str(machine_data.get("version") or ticket_data.get("version", "")),
                ip=machine_data.get("ip") or "",
                port=int(machine_data.get("port") or 0),
                serial=machine_data.get("serial") or "",
                ticket_id=machine_data.get("ticket_id"),
            )
        except (TypeError, ValueError):
            payload["machine"] = None
    try:
        return Ticket.model_validate(payload)
    except ValidationError:
        return None


def _get_field_value(ticket: Ticket, source: dict, field: str) -> Optional[str]:
    if field not in ALLOWED_FIELDS:
        return None

    if "." in field:
        base, nested = field.split(".", 1)
        if base == "machine":
            machine_source = source.get("machine") or {}
            value = machine_source.get(nested)
            return str(value) if value is not None else None
        value = getattr(ticket, base, None)
        if value is None:
            return None
        nested_value = getattr(value, nested, None)
        if nested_value is None:
            return None
        return str(nested_value)

    value = getattr(ticket, field, None)
    if value is None:
        return None
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _contains(value: Optional[str], expected: Optional[str]) -> bool:
    if not expected:
        return True
    if not value:
        return False
    return expected.lower() in value.lower()


def _normalize_search_term(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


def _matches(ticket: Ticket, source: dict, payload: TicketSearchRequest) -> bool:
    for field in payload.active_fields:
        expected = payload.field_values.get(field, "").strip()
        if expected and not _contains(_get_field_value(ticket, source, field), expected):
            return False

    for field, value in payload.field_values.items():
        if field in payload.active_fields:
            continue
        if value.strip() and not _contains(_get_field_value(ticket, source, field), value.strip()):
            return False

    for field_name, date_range in payload.date_ranges.items():
        if field_name not in DATE_FIELD_NAMES:
            return False
        if not date_range.from_ and not date_range.to:
            continue
        target_value = getattr(ticket, field_name, None)
        if not isinstance(target_value, datetime):
            return False
        if date_range.from_ and target_value < date_range.from_:
            return False
        if date_range.to and target_value > date_range.to:
            return False

    if not _contains(ticket.result_data, _normalize_search_term(payload.result_data)):
        return False

    if not _contains(source.get("raw_data"), _normalize_search_term(payload.raw_data)):
        return False

    return True


router = APIRouter()


@router.post("/search")
def search_tickets(payload: TicketSearchRequest, request: Request) -> dict:
    ticket_manager = request.app.state.ticket_manager
    if not ticket_manager:
        raise HTTPException(status_code=500, detail="Ticket manager is not initialized")

    ticket_manager = cast(TicketManager, ticket_manager)
    tickets = ticket_manager.list_tickets()
    matched: List[dict] = []
    for ticket_data in tickets:
        ticket_model = _build_ticket_model(ticket_data)
        if not ticket_model:
            continue
        if _matches(ticket_model, ticket_data, payload):
            matched.append(ticket_data)

    return {"tickets": jsonable_encoder(matched)}
