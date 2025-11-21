"""
Main FastAPI application for Mock Interview Agent.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import interviews, audio
from app.config import settings

# Create FastAPI app
app = FastAPI(
    title="Mock Interview Agent API",
    description="AI-powered interview training agent using LangGraph, NLP, and Fuzzy Logic",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(interviews.router)
app.include_router(audio.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Mock Interview Agent API",
        "version": "1.0.0",
        "description": "AI-powered interview training with LangGraph orchestration",
        "environment": settings.environment,
        "llm_provider": settings.llm_provider,
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "interviews": "/api/interviews"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "llm_provider": settings.llm_provider
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
