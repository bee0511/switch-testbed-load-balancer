from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, Field

from app.services.ticket_manager import TicketManager


class TicketField(str, Enum):
    id = "id"
    status = "status"
    vendor = "vendor"
    model = "model"
    version = "version"
    machine_serial = "machine.serial"
    machine_ip = "machine.ip"
    machine_port = "machine.port"


class DateField(str, Enum):
    enqueued_at = "enqueued_at"
    started_at = "started_at"
    completed_at = "completed_at"


class DateRange(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: Optional[datetime] = Field(default=None, alias="from")
    to: Optional[datetime] = None


class TicketSearchRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    active_fields: List[TicketField] = Field(default_factory=list, alias="activeFields")
    field_values: Dict[TicketField, str] = Field(default_factory=dict, alias="fieldValues")
    date_ranges: Dict[DateField, DateRange] = Field(default_factory=dict, alias="dateRanges")
    result_data: Optional[str] = Field(default=None, alias="resultData")
    raw_data: Optional[str] = Field(default=None, alias="rawData")


def _get_field_value(ticket: dict, field: TicketField) -> Optional[str]:
    if field is TicketField.id:
        return ticket.get("id")
    if field is TicketField.status:
        return ticket.get("status")
    if field is TicketField.vendor:
        return ticket.get("vendor")
    if field is TicketField.model:
        return ticket.get("model")
    if field is TicketField.version:
        return ticket.get("version")
    machine = ticket.get("machine") or {}
    if field is TicketField.machine_serial:
        return machine.get("serial")
    if field is TicketField.machine_ip:
        return machine.get("ip")
    if field is TicketField.machine_port:
        port = machine.get("port")
        return str(port) if port is not None else None
    return None


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


def _parse_datetime(value: Optional[object]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
    return None


def _matches(ticket: dict, payload: TicketSearchRequest) -> bool:
    for field in payload.active_fields:
        expected = payload.field_values.get(field, "").strip()
        if expected and not _contains(_get_field_value(ticket, field), expected):
            return False

    for field, value in payload.field_values.items():
        if field in payload.active_fields:
            continue
        if value.strip() and not _contains(_get_field_value(ticket, field), value.strip()):
            return False

    for field, date_range in payload.date_ranges.items():
        if not date_range.from_ and not date_range.to:
            continue
        target_value = _parse_datetime(ticket.get(field.value))
        if not target_value:
            return False
        if date_range.from_ and target_value < date_range.from_:
            return False
        if date_range.to and target_value > date_range.to:
            return False

    if not _contains(ticket.get("result_data"), _normalize_search_term(payload.result_data)):
        return False

    if not _contains(ticket.get("raw_data"), _normalize_search_term(payload.raw_data)):
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
    matched = [ticket for ticket in tickets if _matches(ticket, payload)]

    return {"tickets": jsonable_encoder(matched)}
