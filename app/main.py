import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.devices import router as devices_router
from app.services.logging_config import setup_logging
from app.services.machine_manager import MachineManager

setup_logging()
logger = logging.getLogger("app.main")

machine_manager = MachineManager()

app = FastAPI(title="Switch Testbed Load Balancer", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.machine_manager = machine_manager

app.include_router(devices_router, tags=["machines"])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


logger.info("Switch Testbed Load Balancer application initialized.")
