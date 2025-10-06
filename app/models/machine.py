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

    def to_dict(self) -> dict:
        """Return a serializable representation of the machine."""
        data = asdict(self)
        data["status"] = "available" if self.available else "unavailable"
        # Keep backward compatible field name for serial number consumers.
        data["serial_number"] = data.pop("serial")
        return data
