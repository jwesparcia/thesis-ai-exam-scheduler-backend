from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from routers import sections, schedule
from database import engine, Base
import models

app = FastAPI()

# Middleware for frontend connection
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables automatically
Base.metadata.create_all(bind=engine)

# Routers
app.include_router(sections.router, prefix="/sections", tags=["Sections"])
app.include_router(schedule.router, prefix="/schedule", tags=["Schedule"])

@app.get("/")
def root():
    return {"message": "Exam Scheduler API running"}
