import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.devices import router as devices_router
from app.api.request import router as request_router
from app.api.reset import router as reset_router
from app.api.result import router as result_router
from app.api.search import router as tickets_router
from app.logging_config import setup_logging
from app.services.ticket_manager import TicketManager

setup_logging()
logger = logging.getLogger("app.main")

ticket_manager = TicketManager()

app = FastAPI(title="Batch Load Balancer API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.state.ticket_manager = ticket_manager

app.include_router(request_router, prefix="/request", tags=["request"])
app.include_router(result_router, prefix="/result", tags=["result"])
app.include_router(reset_router, prefix="/reset", tags=["reset"])
app.include_router(devices_router, prefix="/devices", tags=["devices"])
app.include_router(tickets_router, prefix="/tickets", tags=["tickets"])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


logger.info("Batch Load Balancer API application initialized.")

