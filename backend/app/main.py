"""
TrueTrace Backend Application
FastAPI Server for Network-Grounded Attack Trace Verification & Forensic Graph Arbitration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .api.investigations import router as inv_router
from .api.evidence import router as ev_router
from .api.sensors import router as sensor_router
from .api.arbitration import router as arb_router
from .api.graphs import router as graph_router
from .api.scenarios import router as scen_router
from .api.reports import router as rep_router

# Initialize SQLite database
init_db()

app = FastAPI(
    title="TrueTrace API",
    description="Falsification-Driven Attack Reconstruction via Observability-Aware Network Invariant Arbitration",
    version="1.0.0"
)

# CORS middleware allowing frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(inv_router)
app.include_router(ev_router)
app.include_router(sensor_router)
app.include_router(arb_router)
app.include_router(graph_router)
app.include_router(scen_router)
app.include_router(rep_router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "TrueTrace Verification Engine",
        "engine_version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
