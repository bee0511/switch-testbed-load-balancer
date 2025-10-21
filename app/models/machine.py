from dataclasses import dataclass, asdict


@dataclass
class Machine:
    vendor: str
    model: str
    version: str
    ip: str
    port: int
    serial: str
    status: str = "available"
    available: bool = True

    def to_dict(self) -> dict:
        """Return a serializable representation of the machine."""
        return asdict(self)
