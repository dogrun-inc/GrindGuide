from fastapi import FastAPI
from app.routes.analyze import router as analyze_router
from app.routes.compare import router as compare_router

app = FastAPI(title="Powder Measurement PoC")

app.include_router(analyze_router, prefix="/api")
app.include_router(compare_router, prefix="/api")