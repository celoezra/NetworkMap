from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.database.connection import init_db
from app.routers import (
    dashboard, racks, switches, locations, vlans, devices, search, network_map, system, users, admin
)
from app.utils.logger import logger

app = FastAPI(
    title="Mapa de Infraestrutura de Rede",
    description="Sistema para mapeamento físico e lógico de redes de computadores com banco local criptografado (SQLCipher)",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(dashboard.router)
app.include_router(racks.router)
app.include_router(switches.router)
app.include_router(locations.router)
app.include_router(vlans.router)
app.include_router(devices.router)
app.include_router(search.router)
app.include_router(search.connections_router)
app.include_router(network_map.router)
app.include_router(system.router)
app.include_router(users.router)
app.include_router(admin.router)

@app.on_event("startup")
def startup_event():
    logger.info("Iniciando backend da Aplicação NetworkMap...")
    init_db()

@app.get("/api/health")
def health_check():
    return {"status": "ok", "system": "NetworkMap Backend"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
