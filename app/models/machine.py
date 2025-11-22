from enum import Enum
from typing import Optional
from pydantic import BaseModel

class MachineStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNREACHABLE = "unreachable"

class MachineBase(BaseModel):
    """機器的基本屬性定義"""
    vendor: str
    model: str
    version: str
    mgmt_ip: str
    port: int = 22
    serial: str
    hostname: str
    default_gateway: Optional[str] = None
    netmask: Optional[str] = None

class Machine(MachineBase):
    """包含狀態的完整機器物件"""
    status: MachineStatus = MachineStatus.AVAILABLE

    class Config:
        from_attributes = True # 允許從 dict 或物件轉換

class ReserveRequest(BaseModel):
    vendor: str
    model: str
    version: str
    
class ReleaseResult(str, Enum):
    SUCCESS = "success"                 # 成功觸發重置
    ALREADY_AVAILABLE = "already_available" # 機器已經是可用狀態，無需操作
    NOT_FOUND = "not_found"             # 找不到該序號的機器
    UNREACHABLE = "unreachable"         # 機器無法連線，無法執行重置指令
    FAILED = "failed"                   # SSH 連線或重置指令執行失敗

class ReleaseResponse(BaseModel):
    """API 回傳給前端的統一格式"""
    status: ReleaseResult
    message: str
    machine: Optional["Machine"] = None  # 回傳機器最新狀態