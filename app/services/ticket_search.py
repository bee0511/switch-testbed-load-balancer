
from __future__ import annotations

import logging
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import ValidationError

from app.models.machine import Machine
from app.models.ticket import Ticket
from app.models.search_models import FieldConfig, TicketSearchRequest
from app.services.ticket_manager import TicketManager


class TicketModelBuilder:
    """負責建構和驗證票據模型"""
    
    def build_ticket_model(self, ticket_data: dict) -> Optional[Ticket]:
        payload = {key: ticket_data.get(key) for key in Ticket.model_fields}
        payload["testing_config_path"] = "" # No need to show this field
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


class TicketFieldExtractor:
    """負責提取票據欄位值"""
    
    def __init__(self, field_config: FieldConfig):
        self.field_config = field_config
    
    def get_field_value(self, ticket: Ticket, source: dict, field: str) -> Optional[str]:
        if field not in self.field_config.allowed_fields:
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


class TicketSearchMatcher:
    """負責票據搜尋比對邏輯"""
    
    def __init__(self, field_extractor: TicketFieldExtractor, field_config: FieldConfig):
        self.field_extractor = field_extractor
        self.field_config = field_config
    
    def _contains(self, value: Optional[str], expected: Optional[str]) -> bool:
        """處理欄位值匹配邏輯，支援多選"""
        if not expected:
            return True
        if not value:
            return False
        
        if ',' in expected:
            expected_values = [val.strip().lower() for val in expected.split(',') if val.strip()]
            value_lower = value.lower()
            return any(expected_val in value_lower for expected_val in expected_values)
        else:
            return expected.lower() in value.lower()

    def _normalize_search_term(self, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        trimmed = value.strip()
        return trimmed or None
    
    def matches(self, ticket: Ticket, source: dict, payload: TicketSearchRequest) -> bool:
        # Check active fields
        for field in payload.active_fields:
            expected = payload.field_values.get(field, "").strip()
            ticket_field_value = self.field_extractor.get_field_value(ticket, source, field)
            
            if expected and not self._contains(ticket_field_value, expected):
                return False

        # Check other field values
        for field, value in payload.field_values.items():
            if field in payload.active_fields:
                continue
            ticket_field_value = self.field_extractor.get_field_value(ticket, source, field)
            
            if value.strip() and not self._contains(ticket_field_value, value.strip()):
                return False

        # Check date ranges
        for field_name, date_range in payload.date_ranges.items():
            if field_name not in self.field_config.date_field_names:
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

        # Check result data
        if not self._contains(ticket.result_data, self._normalize_search_term(payload.result_data)):
            return False

        # Check raw data
        if not self._contains(source.get("raw_data"), self._normalize_search_term(payload.raw_data)):
            return False

        return True


class TicketSearchService:
    """票據搜尋服務，整合所有搜尋相關功能"""
    
    def __init__(self):
        self.field_config = FieldConfig()
        self.field_extractor = TicketFieldExtractor(self.field_config)
        self.model_builder = TicketModelBuilder()
        self.search_matcher = TicketSearchMatcher(self.field_extractor, self.field_config)
    
    def search_tickets(self, ticket_manager: TicketManager, payload: TicketSearchRequest) -> List[dict]:
        tickets = ticket_manager.list_tickets()
        matched: List[dict] = []
        
        for ticket_data in tickets:
            ticket_model = self.model_builder.build_ticket_model(ticket_data)
            if not ticket_model:
                logging.warning("Invalid ticket data found for ticket: %s", ticket_data["id"])
                continue
            if self.search_matcher.matches(ticket_model, ticket_data, payload):
                matched.append(ticket_data)
        
        return matched