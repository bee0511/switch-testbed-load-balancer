from dataclasses import dataclass, asdict


@dataclass
class Machine:
    vendor: str
    model: str
    version: str
    mgmt_ip: str
    port: int
    serial: str
    hostname: str
    default_gateway: str
    netmask: str
    status: str = "available"

    def to_dict(self) -> dict:
        """Return a serializable representation of the machine."""
        return asdict(self)
