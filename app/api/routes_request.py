from fastapi import APIRouter, HTTPException, UploadFile, File, Request
from typing import cast

from app.utils import load_device
from app.models.ticket import TicketStatus
from app.services.ticket_manager import TicketManager

router = APIRouter()

def get_valid_machines() -> dict:
    config = load_device()
    valid_machines = {}
    for vendor_entry in config.get("vendors", []):
        vendor = vendor_entry.get("vendor")
        if not vendor:
            continue
        if vendor not in valid_machines:
            valid_machines[vendor] = {}

        for model_entry in vendor_entry.get("models", []):
            model = model_entry.get("model")
            if not model:
                continue
            if model not in valid_machines[vendor]:
                valid_machines[vendor][model] = []

            for version_entry in model_entry.get("versions", []):
                version = version_entry.get("version")
                if version and version not in valid_machines[vendor][model]:
                    valid_machines[vendor][model].append(version)

    return valid_machines

def check_machine_supported(vendor: str, model: str, version: str) -> bool:
    valid_machines = get_valid_machines()
    return (vendor in valid_machines and
            model in valid_machines[vendor] and
            version in valid_machines[vendor][model])

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
        "message": f"Request accepted and {'started processing' if ticket.status == TicketStatus.running else 'queued'}."
    }

    return response