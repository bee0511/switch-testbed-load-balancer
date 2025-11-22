from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.services.machine_manager import MachineManager
from app.api.deps import get_machine_manager
from app.models.machine import Machine, ReleaseResponse, ReleaseResult

router = APIRouter()

@router.get("/machines", response_model=dict)
def list_machines(
    vendor: Optional[str] = None,
    model: Optional[str] = None,
    version: Optional[str] = None,
    status: Optional[str] = None,
    manager: MachineManager = Depends(get_machine_manager),
):
    machines = manager.get_machines(vendor, model, version, status)
    return {"machines": machines}

@router.post("/reserve/{vendor}/{model}/{version}", response_model=Machine)
async def reserve_machine(
    vendor: str,
    model: str,
    version: str,
    manager: MachineManager = Depends(get_machine_manager),
):
    machine = await manager.reserve_machine(vendor, model, version)
    if not machine:
        raise HTTPException(status_code=404, detail="No available machines found")
    return machine

@router.post("/release/{serial_number}", response_model=ReleaseResponse)
async def release_machine(
    serial_number: str,
    manager: MachineManager = Depends(get_machine_manager),
):
    result = await manager.release_machine(serial_number)
    machine = manager.get_machine(serial_number) # 取得最新狀態的機器物件

    # 根據結果決定 HTTP 回應
    if result == ReleaseResult.NOT_FOUND:
        raise HTTPException(status_code=404, detail=f"Machine {serial_number} not found")
    
    elif result == ReleaseResult.UNREACHABLE:
        # 409 Conflict 通常用於狀態衝突，這裡很適合
        raise HTTPException(
            status_code=409, 
            detail=f"Machine {serial_number} is unreachable and cannot be reset via SSH."
        )
    
    elif result == ReleaseResult.FAILED:
        raise HTTPException(
            status_code=500, 
            detail="Failed to execute reset command on the device."
        )

    elif result == ReleaseResult.ALREADY_AVAILABLE:
        # 200 OK，但告知前端已經是可用狀態
        return ReleaseResponse(
            status=ReleaseResult.ALREADY_AVAILABLE,
            message="Machine was already available.",
            machine=machine
        )

    elif result == ReleaseResult.SUCCESS:
        # 200 OK (或者用 202 Accepted 表示請求已接受處理中)
        return ReleaseResponse(
            status=ReleaseResult.SUCCESS,
            message="Machine reset initiated successfully. It will be reachable soon.",
            machine=machine
        )
    
    # 理論上不會跑到這裡
    raise HTTPException(status_code=500, detail="Unknown error")