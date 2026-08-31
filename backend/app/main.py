from fastapi import FastAPI
from app.database import engine, Base
import app.models.pcb
import app.models.diagnosis
import app.models.repair
import app.models.test

from app.routers.pcb import router as pcb_router
from app.routers.diagnosis import router as diagnosis_router
from app.routers.repair import router as repair_router
from app.routers.test import router as test_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="GreenUpPCB LIS")

app.include_router(pcb_router)
app.include_router(diagnosis_router)
app.include_router(repair_router)
app.include_router(test_router)


@app.get("/health")
def health():
    return {"status": "ok"}
