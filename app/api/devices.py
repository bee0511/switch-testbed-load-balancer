from typing import cast

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.machine_manager import MachineManager

router = APIRouter()


def _get_machine_manager(request: Request) -> MachineManager:
    manager = getattr(request.app.state, "machine_manager", None)
    if not manager:
        raise HTTPException(status_code=500, detail="Machine manager is not initialized")
    return cast(MachineManager, manager)


@router.get("/machines")
def list_machines(
    request: Request,
    vendor: str | None = Query(default=None),
    model: str | None = Query(default=None),
    version: str | None = Query(default=None),
    status: str | None = Query(
        default=None,
        description=(
            "Filter by machine availability status (available/unavailable/unreachable)."
        ),
    ),
) -> dict:
    """List machines filtered by the given criteria and return filter options."""

    manager = _get_machine_manager(request)
    try:
        machines = [
            machine.to_dict()
            for machine in manager.list_machines(
                vendor=vendor,
                model=model,
                version=version,
                status=status,
            )
        ]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "machines": machines,
    }

@router.get("/get/{vendor}/{model}/{version}")
def reserve_available_machines(
    vendor: str,
    model: str,
    version: str,
    request: Request,
) -> dict:
    """Reserve available machines for the requested specification."""

    manager = _get_machine_manager(request)
    reserved = manager.reserve_machines(vendor, model, version)
    if not reserved:
        raise HTTPException(status_code=404, detail="No available machines for given specification")

    return reserved.to_dict()


@router.post("/release/{serial_number}")
def release_machine(serial_number: str, request: Request) -> dict:
    """Release a previously reserved machine."""

    manager = _get_machine_manager(request)
    machine = manager.get_machine_by_serial(serial_number)
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    manager.release_machine(serial_number)
    refreshed = manager.get_machine_by_serial(serial_number)
    return {"machine": refreshed.to_dict() if refreshed else None}
