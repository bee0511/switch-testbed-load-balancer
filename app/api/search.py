from __future__ import annotations

from typing import cast

from fastapi import APIRouter, HTTPException, Request
from fastapi.encoders import jsonable_encoder

from app.models.search_models import TicketSearchRequest
from app.services.ticket_manager import TicketManager
from app.services.ticket_search import TicketSearchService
from app.logging_config import logging


router = APIRouter()
logger = logging.getLogger("app.api.search")

# Initialize the ticket search service
ticket_search_service = TicketSearchService()


@router.post("/search")
def search_tickets(payload: TicketSearchRequest, request: Request) -> dict:
    """搜尋票據API端點"""
    ticket_manager = request.app.state.ticket_manager
    if not ticket_manager:
        raise HTTPException(status_code=500, detail="Ticket manager is not initialized")

    ticket_manager = cast(TicketManager, ticket_manager)
    matched_tickets = ticket_search_service.search_tickets(ticket_manager, payload)
    
    logger.info("Ticket search found %d matching tickets", len(matched_tickets))
    return {"tickets": jsonable_encoder(matched_tickets)}
