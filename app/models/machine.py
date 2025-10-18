from dataclasses import dataclass, asdict


@dataclass
class Machine:
    vendor: str
    model: str
    version: str
    ip: str
    port: int
    serial: str
    available: bool = True
    reachable: bool = True

    def to_dict(self) -> dict:
        """Return a serializable representation of the machine."""
        data = asdict(self)
        reachable = data.pop("reachable", True)
        is_available = bool(data.get("available", False)) and reachable
        data["available"] = is_available
        if not reachable:
            status = "unreachable"
        else:
            status = "available" if is_available else "unavailable"
        data["status"] = status
        # Keep backward compatible field name for serial number consumers.
        data["serial_number"] = data.pop("serial")
        return data
