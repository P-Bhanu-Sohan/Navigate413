import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from db.mongo import connect_to_mongo, disconnect_from_mongo
from db.vector_store import seed_campus_resources
from routers import upload, analyze, translate, simulate, resources, chat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown."""
    # Startup
    logger.info("Starting Navigate413 backend...")
    try:
        await connect_to_mongo()
        await seed_campus_resources()
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    await disconnect_from_mongo()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Navigate413 API",
    description="Multi-agent document reasoning platform for UMass students",
    version="0.2.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(upload.router)
app.include_router(analyze.router)
app.include_router(translate.router)
app.include_router(simulate.router)
app.include_router(resources.router)
app.include_router(chat.router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "Navigate413 API",
        "status": "ready",
        "version": "0.2.0"
    }


@app.get("/health")
async def health():
    """Health check for deployment."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
