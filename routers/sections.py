from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import crud, schemas
from database import get_db

router = APIRouter()

# ----- Sections -----
@router.get("/")
def read_sections(db: Session = Depends(get_db)):
    sections = crud.get_sections(db)
    return [{"section_id": s.id, "section_name": s.section_name} for s in sections]

@router.post("/")
def create_section(section: schemas.SectionCreate, db: Session = Depends(get_db)):
    s = crud.create_section(db, section)
    return {"section_id": s.id, "section_name": s.section_name}


# ----- Subjects -----
@router.get("/{section_id}/subjects")
def read_section_subjects(section_id: int, db: Session = Depends(get_db)):
    subjects = crud.get_subjects_by_section(db, section_id)
    return [
        {
            "subject_id": sub.id,
            "subject_name": sub.subject_name,
            "teacher_name": sub.teacher_name,   # ✅ now included
        }
        for sub in subjects
    ]

@router.post("/{section_id}/subjects")
def create_subject(section_id: int, subject: schemas.SubjectBase, db: Session = Depends(get_db)):
    new_subject = crud.create_subject(
        db,
        schemas.SubjectCreate(
            subject_name=subject.subject_name,
            teacher_name=subject.teacher_name,   # ✅ accept teacher
            section_id=section_id
        )
    )
    return {
        "subject_id": new_subject.id,
        "subject_name": new_subject.subject_name,
        "teacher_name": new_subject.teacher_name,
        "section_id": new_subject.section_id
    }
