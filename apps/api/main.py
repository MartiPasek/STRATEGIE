from fastapi import FastAPI

from core.logging import setup_logging
from modules.ai_processing.api.router import router as ai_processing_router

# Inicializace logování při startu
setup_logging()

app = FastAPI(
    title="STRATEGIE API",
    description="Modular enterprise AI platform",
    version="0.1.0",
)

# Registrace routerů
app.include_router(ai_processing_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
