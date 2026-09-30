import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .core.config import config
from .core.module_manager import module_manager
from .modules.sync.module import SyncModule
from .modules.organizer.module import OrganizerModule
from .modules.debrid.module import DebridModule
from .web.api import router as core_router

logging.basicConfig(
    level=getattr(logging, config.get("system", "log_level", default="INFO").upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("aetherbox")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing AetherBox Core Engine...")
    
    # Register pluggable modules
    module_manager.app = app
    module_manager.register(SyncModule())
    module_manager.register(OrganizerModule())
    module_manager.register(DebridModule())
    
    # Start all enabled modules
    await module_manager.start_all()
    logger.info("AetherBox startup completed successfully")
    
    yield
    
    logger.info("Shutting down AetherBox...")
    await module_manager.stop_all()
    logger.info("AetherBox shutdown complete")


app = FastAPI(
    title="AetherBox",
    description="The Modular Ingestion, Debrid & Cloud Sync Engine for Homelab Media Stacks",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Core APIs
app.include_router(core_router)

# Mount Static Web UI
STATIC_DIR = Path(__file__).parent / "web" / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    host = config.get("system", "host", default="0.0.0.0")
    port = config.get("system", "port", default=8080)
    uvicorn.run("aetherbox.main:app", host=host, port=port, reload=True)
