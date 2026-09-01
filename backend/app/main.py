from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import pcb, diagnosis, repair, test

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="GreenUpPCB LIS",
    description="Laboratory Information System for PCB Intake, Diagnosis, Repair & Testing",
    version="1.0.0"
)

# Frontend (React) erisimine izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'lar
app.include_router(pcb.router, prefix="/pcbs")
app.include_router(diagnosis.router, prefix="/pcbs")
app.include_router(repair.router, prefix="/pcbs")
app.include_router(test.router, prefix="/pcbs")

@app.get("/", tags=["General"])
def root():
    return {"message": "GreenUpPCB LIS API is running"}
