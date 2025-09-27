from fastapi import APIRouter, HTTPException, Request
from app.services.ticket_manager import TicketManager
from typing import cast

router = APIRouter()

@router.get("/{id}")
def get_result(id: str, request: Request) -> dict:
    """
    取得 ticket 狀態和結果
    如果任務還在執行中，立即回復 false (running 狀態)
    如果任務已完成，回復 true 和結果
    """
    ticket_manager = request.app.state.ticket_manager
    if not ticket_manager:
        raise HTTPException(status_code=500, detail="Ticket manager is not initialized")
    
    ticket_manager = cast(TicketManager, ticket_manager)
    
    response = ticket_manager.get_ticket_response(id)
    if not response:
        raise HTTPException(status_code=404, detail=f"Ticket {id} not found")

    return response


@router.get("/")
def get_queue_info(request: Request) -> dict:
    """取得整體佇列狀態"""
    ticket_manager = request.app.state.ticket_manager
    if not ticket_manager:
        raise HTTPException(status_code=500, detail="Ticket manager is not initialized")
    
    ticket_manager = cast(TicketManager, ticket_manager)
    return ticket_manager.get_queue_status()
