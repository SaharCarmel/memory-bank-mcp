from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import router, build_job_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await build_job_service.start_worker()
    yield
    # Shutdown
    await build_job_service.stop_worker()

app = FastAPI(title="Memory Bank Dashboard API", version="0.1.0", lifespan=lifespan)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3333"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)