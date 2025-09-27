from fastapi import APIRouter, HTTPException, Request
from app.models.machine import Machine
from app.services.ticket_manager import TicketManager
from typing import cast

router = APIRouter()

@router.post("/{serial}")
async def reset_machine_by_API(serial: str, request: Request) -> dict:
    """
    重置指定機器
    """
    ticket_manager = request.app.state.ticket_manager
    if not ticket_manager:
        raise HTTPException(status_code=500, detail="Ticket manager is not initialized")
    
    ticket_manager = cast(TicketManager, ticket_manager)
    machine_manager = ticket_manager.machine_manager
    machine = machine_manager.get_machine_by_serial(serial)
    if not machine:
        raise HTTPException(status_code=404, detail=f"Machine {serial} not found")
    
    task_processor = ticket_manager.task_processor
    success = await task_processor.reset_machine(machine)
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue reset task for machine {serial}")
    message = f"Reset task for machine {serial} has completed successfully."
    return {"message": message}