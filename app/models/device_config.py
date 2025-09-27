from typing import List, TypedDict

class DeviceEntry(TypedDict):
    ip: str
    port: int
    serial_number: str

class VersionEntry(TypedDict):
    version: str
    devices: List[DeviceEntry]

class ModelEntry(TypedDict):
    model: str
    versions: List[VersionEntry]

class VendorEntry(TypedDict):
    vendor: str
    models: List[ModelEntry]

class DeviceConfig(TypedDict):
    vendors: List[VendorEntry]
