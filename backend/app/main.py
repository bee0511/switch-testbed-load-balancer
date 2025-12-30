import logging
from contextlib import asynccontextmanager
import os
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from app.api.routers import machines
from app.core.logging import setup_logging
from app.api.deps import get_machine_manager, verify_bearer_token
from app.services.machine_monitor import monitor_machines

setup_logging()
logger = logging.getLogger("app.main")

def _require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Required environment variable {var_name} is not set.")
    return value

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    _require_env("API_BEARER_TOKEN")
    manager = await get_machine_manager()
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
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    machines.router,
    tags=["machines"],
    dependencies=[Depends(verify_bearer_token)],
)

@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
