# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine
from routers import catalog, scheduler, exams

# ✅ Create tables if they don’t exist (safe, no data loss)
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Routers
app.include_router(catalog.router, prefix="", tags=["Catalog"])
app.include_router(scheduler.router, prefix="/scheduler", tags=["Scheduler"])
app.include_router(exams.router, prefix="/exams", tags=["Exams"])

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
