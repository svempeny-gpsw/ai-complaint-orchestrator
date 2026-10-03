from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.complaints import router as complaints_router
from app.core.database import Base, engine
from app.models.complaint_db import ComplaintDB
from app.models.complaint_action_db import ComplaintActionDB

app = FastAPI(
    title="Customer Complaint System",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_database_tables():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(complaints_router)