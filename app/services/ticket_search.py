
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from pydantic import ValidationError

from app.models.machine import Machine
from app.models.ticket import Ticket
from app.models.search_models import DateRange, FieldConfig, TicketSearchRequest
from app.services.ticket_manager import TicketManager


logger = logging.getLogger(__name__)


@dataclass
class _PreparedSearch:
    active_fields: List[str]
    active_field_set: Set[str]
    field_values: Dict[str, str]
    date_ranges: Dict[str, DateRange]
    result_data: Optional[str]
    raw_data: Optional[str]


class TicketSearchService:
    """票據搜尋服務，整合所有搜尋相關功能"""

    def __init__(self) -> None:
        self.field_config = FieldConfig()
        self._allowed_fields = set(self.field_config.allowed_fields)
        self._date_fields = set(self.field_config.date_field_names)

    def search_tickets(
        self, ticket_manager: TicketManager, payload: TicketSearchRequest
    ) -> List[dict]:
        tickets = ticket_manager.list_tickets()
        prepared = self._prepare_payload(payload)

        matched: List[dict] = []
        for ticket_data in tickets:
            ticket_model = self._build_ticket(ticket_data)
            if not ticket_model:
                logger.warning("Invalid ticket data found for ticket: %s", ticket_data.get("id"))
                continue
            if self._matches(ticket_model, ticket_data, prepared):
                matched.append(ticket_data)

        return matched

    def _prepare_payload(self, payload: TicketSearchRequest) -> _PreparedSearch:
        field_values = {
            field: value.strip()
            for field, value in payload.field_values.items()
            if value and value.strip()
        }
        active_fields = list(payload.active_fields)
        active_field_set = set(active_fields)

        date_ranges = {
            field: date_range
            for field, date_range in payload.date_ranges.items()
            if field in self._date_fields and (date_range.from_ or date_range.to)
        }

        return _PreparedSearch(
            active_fields=active_fields,
            active_field_set=active_field_set,
            field_values=field_values,
            date_ranges=date_ranges,
            result_data=self._normalize_search_term(payload.result_data),
            raw_data=self._normalize_search_term(payload.raw_data),
        )

    def _build_ticket(self, ticket_data: dict) -> Optional[Ticket]:
        payload = {key: ticket_data.get(key) for key in Ticket.model_fields}
        payload["testing_config_path"] = ""

        machine_data = ticket_data.get("machine")
        if isinstance(machine_data, dict):
            payload["machine"] = self._build_machine(ticket_data, machine_data)
        else:
            payload["machine"] = None

        try:
            return Ticket.model_validate(payload)
        except ValidationError:
            return None

    def _build_machine(self, ticket_data: dict, machine_data: dict) -> Optional[Machine]:
        try:
            return Machine(
                vendor=machine_data.get("vendor") or ticket_data.get("vendor", ""),
                model=machine_data.get("model") or ticket_data.get("model", ""),
                version=str(machine_data.get("version") or ticket_data.get("version", "")),
                ip=machine_data.get("ip") or "",
                port=int(machine_data.get("port") or 0),
                serial=machine_data.get("serial") or "",
                ticket_id=machine_data.get("ticket_id"),
            )
        except (TypeError, ValueError):
            return None

    def _matches(self, ticket: Ticket, source: dict, prepared: _PreparedSearch) -> bool:
        for field in prepared.active_fields:
            expected = prepared.field_values.get(field)
            if expected and not self._contains(self._extract_field(ticket, source, field), expected):
                return False

        for field, expected in prepared.field_values.items():
            if field in prepared.active_field_set:
                continue
            if not self._contains(self._extract_field(ticket, source, field), expected):
                return False

        for field, date_range in prepared.date_ranges.items():
            target_value = getattr(ticket, field, None)
            if not isinstance(target_value, datetime):
                return False
            if date_range.from_ and target_value < date_range.from_:
                return False
            if date_range.to and target_value > date_range.to:
                return False

        if not self._contains(ticket.result_data, prepared.result_data):
            return False
        if not self._contains(source.get("raw_data"), prepared.raw_data):
            return False

        return True

    def _extract_field(self, ticket: Ticket, source: dict, field: str) -> Optional[str]:
        if field not in self._allowed_fields:
            return None

        if "." in field:
            base, nested = field.split(".", 1)
            if base == "machine":
                machine_source = source.get("machine") or {}
                value = machine_source.get(nested)
            else:
                parent = getattr(ticket, base, None)
                value = getattr(parent, nested, None) if parent is not None else None
        else:
            value = getattr(ticket, field, None)

        return self._serialize_value(value)

    def _serialize_value(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, datetime):
            return value.isoformat()
        return str(value)

    def _contains(self, value: Any, expected: Optional[str]) -> bool:
        if expected is None:
            return True
        if value is None:
            return False

        candidate = str(value).lower()
        terms = [term.strip().lower() for term in expected.split(",") if term.strip()]
        if not terms:
            return True
        return any(term in candidate for term in terms)

    def _normalize_search_term(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None
