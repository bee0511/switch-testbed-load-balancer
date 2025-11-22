import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.api.routers import machines
from app.core.logging import setup_logging
from app.api.deps import get_machine_manager
from app.services.machine_monitor import monitor_machines

setup_logging()
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    manager = get_machine_manager()
    await manager.initialize_status() # 啟動時檢查一次
    
    # 啟動背景監控
    monitor_task = asyncio.create_task(monitor_machines(manager))
    
    yield
    
    # Shutdown
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass
    logger.info("Shutdown complete.")

app = FastAPI(
    title="Switch Testbed Load Balancer", 
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(machines.router, tags=["machines"])

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}