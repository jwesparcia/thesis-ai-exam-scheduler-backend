# routers/sections.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import crud

router = APIRouter(prefix="/sections", tags=["Sections"])

@router.get("/{year_name}")
def get_sections(year_name: str, db: Session = Depends(get_db)):
    """
    Get all sections in a year level (e.g., BSIT-3),
    with their subjects and professor names.
    """
    return crud.get_sections_with_subjects(db, year_name)
