# smartcapi-backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import auth, interview, system, dashboard, sync

app = FastAPI(title="SmartCAPI Backend")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Atau spesifikasikan domain frontend Anda
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include new routers
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(interview.router, prefix="/api", tags=["Interview"])
app.include_router(system.router, prefix="/api", tags=["System"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])
app.include_router(sync.router, prefix="/api", tags=["Sync"])


@app.get("/")
def read_root():
    return {"message": "Welcome to SmartCAPI Backend API"}