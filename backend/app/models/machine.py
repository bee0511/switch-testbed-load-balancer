from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MachineStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNREACHABLE = "unreachable"
    REBOOTING = "rebooting"

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
    model_config = ConfigDict(from_attributes=True)

class ReserveRequest(BaseModel):
    vendor: str
    model: str
    version: str
    
class ReleaseResult(str, Enum):
    SUCCESS = "success"                 # 成功觸發重置
    FAILED = "failed"                   # SSH 連線或重置指令執行失敗
    NOT_FOUND = "not_found"             # 找不到該序號的機器

class ReleaseResponse(BaseModel):
    """API 回傳給前端的統一格式"""
    status: ReleaseResult
    message: str
    machine: Optional["Machine"] = None  # 回傳機器最新狀態
