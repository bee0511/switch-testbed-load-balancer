from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from typing import cast

from app.utils import build_supported_versions_map
from app.models.ticket import TicketStatus
from app.services.ticket_manager import TicketManager

router = APIRouter()

def check_machine_supported(vendor: str, model: str, version: str) -> bool:
    valid_machines = build_supported_versions_map()
    return (
        vendor in valid_machines
        and model in valid_machines[vendor]
        and version in valid_machines[vendor][model]
    )

@router.post("/{vendor}/{model}/{version}", summary="Create request (file upload)")
async def create_request(vendor: str, model: str, version: str, request: Request, file: UploadFile = File(...)) -> dict:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="file is empty")

    if not check_machine_supported(vendor, model, version):
        raise HTTPException(status_code=400, detail="The specified vendor/model/version is not supported")
    
    ticket_manager = request.app.state.ticket_manager
    if not ticket_manager:
        raise HTTPException(status_code=500, detail="Ticket manager is not initialized")
    
    ticket_manager = cast(TicketManager, ticket_manager)

    ticket = ticket_manager.process_ticket(version, vendor, model, data)
    if not ticket:
        raise HTTPException(status_code=500, detail="Failed when processing the ticket")
    
    response = {
        "id": ticket.id,
        "status": ticket.status,
        "message": (
            "Request accepted and "
            f"{'started processing' if ticket.status == TicketStatus.running else 'queued'}."
        ),
    }

    return response
